"""
Song Master CLI client that delegates lyric generation to the FastAPI backend.
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from helpers import (
    extract_song_details_for_art,
    generate_album_art,
    get_default_song_params,
    load_prompt_from_file,
    save_song,
)

load_dotenv()

DEFAULT_API_BASE = (
    os.getenv("SONG_MASTER_API_BASE")
    or os.getenv("API_BASE")  # fallback to a generic name if provided
    or "http://localhost:8000"
)


def build_api_base(cli_value: Optional[str]) -> str:
    base = cli_value or DEFAULT_API_BASE
    return base.rstrip("/")


def start_backend_generation(
    api_base: str, prompt: str, use_local: bool, song_name: Optional[str], persona: Optional[str], project_id: Optional[int] = None
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "user_prompt": prompt,
        "title": song_name,
        "persona": persona,
        "use_local": use_local,
        "project_id": project_id,
    }
    response = requests.post(f"{api_base}/api/songs/generate", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def poll_generation_status(api_base: str, song_id: int, poll_interval: float) -> None:
    last_stage: Optional[str] = None
    last_progress: Optional[int] = None
    while True:
        response = requests.get(f"{api_base}/api/songs/{song_id}/status", timeout=15)
        response.raise_for_status()
        status = response.json()
        status_name = status.get("status")
        stage = status.get("current_stage") or status_name
        progress = status.get("progress")

        if stage != last_stage or progress != last_progress:
            progress_label = f"{progress}%" if progress is not None else "-"
            print(f"[{progress_label}] {stage or 'waiting'}")
            last_stage, last_progress = stage, progress

        if status_name == "completed":
            return
        if status_name == "failed":
            raise RuntimeError(status.get("error_message") or "Generation failed")

        time.sleep(poll_interval)


def fetch_song_detail(api_base: str, song_id: int) -> Dict[str, Any]:
    response = requests.get(f"{api_base}/api/songs/{song_id}", timeout=15)
    response.raise_for_status()
    return response.json()


def parse_metadata(raw_metadata: Any) -> Dict[str, Any]:
    if isinstance(raw_metadata, dict):
        return raw_metadata
    if isinstance(raw_metadata, str) and raw_metadata:
        try:
            return json.loads(raw_metadata)
        except json.JSONDecodeError:
            return {"raw": raw_metadata}
    return {}


def persist_local_copy(song_detail: Dict[str, Any]) -> Optional[str]:
    title = song_detail.get("title") or "Untitled"
    lyrics = song_detail.get("lyrics")
    user_prompt = song_detail.get("user_prompt", "")
    metadata = parse_metadata(song_detail.get("metadata") or song_detail.get("metadata_json"))
    if not lyrics:
        return None
    default_params = get_default_song_params()
    return save_song(title, user_prompt, lyrics, default_params, metadata)


def regenerate_album_art(song_path: str) -> str:
    title, user_prompt = extract_song_details_for_art(song_path)
    return generate_album_art(title, user_prompt or "Use the song metadata to inspire the cover art.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a song using the Song Master backend")
    parser.add_argument("prompt", nargs="?", help="The song description or request")
    parser.add_argument(
        "--prompt-file",
        type=str,
        default=None,
        help="Path to a .txt file containing the song description or request",
    )
    parser.add_argument("--local", action="store_true", help="Use local LM Studio LLM and disable image generation")
    parser.add_argument("--name", type=str, default=None, help="Optional song name/title")
    parser.add_argument(
        "--persona",
        type=str,
        default=None,
        help='Specify the persona by name (e.g., "antidote") or by path to a persona .md file',
    )
    parser.add_argument(
        "--regen-cover",
        type=str,
        default=None,
        help="Path to an existing song markdown file to regenerate album art and exit",
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default=None,
        help=f"Base URL for the Song Master backend (default: {DEFAULT_API_BASE})",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds between polling the backend for generation status",
    )

    args = parser.parse_args()

    if args.regen_cover:
        try:
            artwork_path = regenerate_album_art(args.regen_cover)
        except (FileNotFoundError, ValueError) as regen_err:
            parser.error(str(regen_err))
            sys.exit(2)
        print(f"Album art regenerated: {artwork_path}")
        sys.exit(0)

    try:
        prompt_text = load_prompt_from_file(args.prompt_file) if args.prompt_file else args.prompt
    except FileNotFoundError as prompt_err:
        parser.error(str(prompt_err))
        sys.exit(2)

    if not prompt_text:
        parser.error("You must provide a prompt as an argument or via --prompt-file")
        sys.exit(2)

    api_base = build_api_base(args.api_base)
    try:
        song_record = start_backend_generation(api_base, prompt_text, args.local, args.name, args.persona)
    except requests.RequestException as exc:
        sys.exit(f"Failed to start backend generation: {exc}")

    song_id = song_record.get("id")
    if song_id is None:
        sys.exit("Backend did not return a song id.")
    title = song_record.get("title", "Untitled")
    print(f"Started backend generation for '{title}' (id: {song_id}) via {api_base}")
    try:
        poll_generation_status(api_base, song_id, args.poll_interval)
    except Exception as exc:  # pragma: no cover - runtime only
        sys.exit(f"Generation failed: {exc}")

    try:
        song_detail = fetch_song_detail(api_base, song_id)
    except requests.RequestException as exc:
        sys.exit(f"Failed to fetch generated song details: {exc}")

    local_file = persist_local_copy(song_detail)

    print("\nGeneration completed.")
    print(f"Title: {song_detail.get('title')}")
    mode_local = song_detail.get("use_local") if song_detail.get("use_local") is not None else args.local
    print(f"Persona: {song_detail.get('persona') or 'default'} | Mode: {'local' if mode_local else 'remote'}")
    if local_file:
        print(f"Local copy saved to {local_file}")
    print("\nLyrics:\n")
    print(song_detail.get("lyrics") or "No lyrics returned.")


if __name__ == "__main__":
    main()
