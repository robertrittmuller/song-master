import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

from fastapi import UploadFile

from backend.shared.ai_functions import build_prompts, review_song_with_audio, revise_lyrics
from backend.shared.helpers import remove_thinking_tags


def _is_live_listen_error(feedback: str) -> bool:
    normalized = (feedback or "").strip()
    if not normalized:
        return True

    return normalized.startswith((
        "Audio review is not supported",
        "Multimodal LLM error:",
        "Error reading audio file:",
    ))


def _process_live_listen_audio_path(audio_path: str, song_data: dict) -> Dict[str, str]:
    """Analyze a local audio file and return revised lyrics plus feedback."""
    # Live Listen relies on remote multimodal and text models even for songs that
    # were originally created in local mode.
    live_listen_uses_local = False

    current_lyrics = song_data.get("lyrics", "")
    if not current_lyrics:
        raise ValueError("Song has no lyrics to review.")

    feedback = review_song_with_audio(current_lyrics, audio_path, live_listen_uses_local)
    if _is_live_listen_error(feedback):
        raise ValueError(feedback)

    prompts = build_prompts()
    revision_prompt = prompts["revision"]

    revised_lyrics = remove_thinking_tags(
        revise_lyrics(
            revision_prompt,
            current_lyrics,
            feedback,
            live_listen_uses_local,
            user_input=song_data.get("user_prompt", ""),
            brief=None,
        )
    )

    return {
        "revised_lyrics": revised_lyrics,
        "feedback": feedback,
    }


async def process_live_listen_feedback(song_id: int, file: UploadFile, song_data: dict, use_local: bool) -> Dict[str, str]:
    """Process an uploaded audio file and return Live Listen lyric feedback."""
    del song_id, use_local

    suffix = Path(file.filename or "").suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        return _process_live_listen_audio_path(tmp_path, song_data)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


async def process_live_listen_feedback_from_path(
    song_id: int,
    audio_path: str,
    song_data: dict,
    use_local: bool,
) -> Dict[str, str]:
    """Process an existing local song audio file and return Live Listen lyric feedback."""
    del song_id, use_local

    return _process_live_listen_audio_path(audio_path, song_data)
