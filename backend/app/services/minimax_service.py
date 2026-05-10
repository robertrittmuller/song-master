from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from backend.app.core.config import Settings, get_settings
from backend.shared.helpers import get_song_storage_info, relativize_storage_path, strip_style_tags


@dataclass
class MiniMaxDemoTrackResult:
    file_path: str
    file_name: str
    file_size: Optional[int]
    mime_type: str
    trace_id: Optional[str]
    model: str
    provider_status: Optional[int]
    provider_response: Dict[str, Any]
    duration_ms: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bitrate: Optional[int] = None


class MiniMaxMusicService:
    """Thin client for MiniMax music generation used by demo-track creation."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def generate_demo_track(
        self,
        title: str,
        user_prompt: str,
        lyrics: str,
        clean_lyrics: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        persona: Optional[str] = None,
        style: Optional[str] = None,
        vocal_gender: Optional[str] = None,
        date: Optional[str] = None,
    ) -> MiniMaxDemoTrackResult:
        api_key = (self.settings.minimax_api_key or "").strip()
        if not api_key:
            raise RuntimeError("MINIMAX_API_KEY is not configured in .env.")

        model_name = (self.settings.minimax_music_model or "").strip()
        if not model_name:
            raise RuntimeError("MINIMAX_MUSIC_MODEL is not configured in .env.")

        prepared_lyrics = self._prepare_lyrics(clean_lyrics, lyrics)
        prompt = self._build_prompt(
            title=title,
            user_prompt=user_prompt,
            metadata=metadata or {},
            persona=persona,
            style=style,
            vocal_gender=vocal_gender,
        )

        payload = {
            "model": model_name,
            "prompt": prompt,
            "lyrics": prepared_lyrics,
            "output_format": "url",
            "lyrics_optimizer": False,
            "audio_setting": {
                "sample_rate": 44100,
                "bitrate": 256000,
                "format": "mp3",
            },
        }
        response = requests.post(
            self._music_generation_url(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.minimax_request_timeout,
        )
        response.raise_for_status()

        body = response.json()
        base_resp = body.get("base_resp") or {}
        if base_resp.get("status_code", 0) not in (0, None):
            raise RuntimeError(base_resp.get("status_msg") or "MiniMax request failed.")

        data = body.get("data") or {}
        audio_url = data.get("audio_url") or data.get("audio")
        if not isinstance(audio_url, str) or not audio_url.startswith("http"):
            raise RuntimeError("MiniMax did not return a downloadable audio URL.")

        absolute_file_path = self._demo_track_file_path(title=title, date=date)
        self._download_audio(audio_url, absolute_file_path)

        audio_path = Path(absolute_file_path)
        extra_info = body.get("extra_info") or {}
        return MiniMaxDemoTrackResult(
            file_path=relativize_storage_path(str(audio_path)),
            file_name=audio_path.name,
            file_size=audio_path.stat().st_size if audio_path.exists() else None,
            mime_type="audio/mpeg",
            trace_id=body.get("trace_id"),
            model=model_name,
            provider_status=data.get("status"),
            provider_response=body,
            duration_ms=extra_info.get("music_duration"),
            sample_rate=extra_info.get("music_sample_rate"),
            channels=extra_info.get("music_channel"),
            bitrate=extra_info.get("bitrate"),
        )

    def _music_generation_url(self) -> str:
        return f"{self.settings.minimax_api_base.rstrip('/')}/music_generation"

    def _demo_track_file_path(self, title: str, date: Optional[str]) -> str:
        storage = get_song_storage_info(title, date)
        folder = Path(storage["abs_folder"])
        folder.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"{storage['abs_image_base']}_demo_{timestamp}.mp3"

    def _prepare_lyrics(self, clean_lyrics: Optional[str], lyrics: str) -> str:
        prepared = strip_style_tags(clean_lyrics or "").strip()
        if not prepared:
            prepared = strip_style_tags(lyrics or "").strip()
        if not prepared:
            raise ValueError("Song lyrics are required before creating a demo track.")
        if len(prepared) > 3500:
            raise ValueError("Song lyrics exceed the MiniMax 3500 character limit.")
        return prepared

    def _build_prompt(
        self,
        title: str,
        user_prompt: str,
        metadata: Dict[str, Any],
        persona: Optional[str],
        style: Optional[str],
        vocal_gender: Optional[str],
    ) -> str:
        prompt_parts = [f"Create a polished demo track for the song '{title}'."]

        description = self._normalize_text(metadata.get("description"))
        if description:
            prompt_parts.append(description)

        if user_prompt.strip():
            prompt_parts.append(f"Original brief: {user_prompt.strip()}")

        style_tokens = self._normalize_text(metadata.get("suno_styles"))
        if style_tokens:
            prompt_parts.append(f"Style references: {style_tokens}")
        elif style:
            prompt_parts.append(f"Core style: {style}")

        for key, label in (
            ("genre", "Genre"),
            ("mood", "Mood"),
            ("tempo", "Tempo"),
            ("key", "Key"),
            ("instruments", "Instruments"),
        ):
            value = self._normalize_text(metadata.get(key))
            if value:
                prompt_parts.append(f"{label}: {value}")

        if persona:
            prompt_parts.append(f"Persona: {persona.replace('_', ' ')}")
        if vocal_gender:
            prompt_parts.append(f"Vocal presentation: {vocal_gender}")

        prompt = " ".join(part for part in prompt_parts if part).strip()
        return prompt[:2000] if len(prompt) > 2000 else prompt

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return ", ".join(str(item).strip() for item in value if str(item).strip())
        return str(value).strip()

    def _download_audio(self, audio_url: str, destination: str) -> None:
        response = requests.get(audio_url, stream=True, timeout=self.settings.minimax_request_timeout)
        response.raise_for_status()

        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with destination_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)