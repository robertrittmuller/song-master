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


async def process_live_listen_feedback(song_id: int, file: UploadFile, song_data: dict, use_local: bool):
    """
    Process the uploaded audio file to get feedback and revise the song lyrics.
    """
    del song_id

    # Live Listen relies on remote multimodal and text models even for songs that
    # were originally created in local mode.
    live_listen_uses_local = False

    # Save the uploaded file temporarily
    suffix = Path(file.filename).suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Get current lyrics
        current_lyrics = song_data.get("lyrics", "")
        if not current_lyrics:
            raise ValueError("Song has no lyrics to review.")

        # Get feedback from multimodal LLM
        feedback = review_song_with_audio(current_lyrics, tmp_path, live_listen_uses_local)
        if _is_live_listen_error(feedback):
            raise ValueError(feedback)

        # Get revision prompt template
        prompts = build_prompts()
        revision_prompt = prompts["revision"]

        # Revise lyrics based on feedback
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

        # Update the song in the database (or wherever it persists)
        # We need to simulate the state update that song_pipeline does, but for a single update.
        # Ideally, we would re-run parts of the pipeline, but here we just want to update the lyrics.
        
        # We return the new lyrics and the feedback used.
        return {
            "revised_lyrics": revised_lyrics,
            "feedback": feedback
        }

    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
