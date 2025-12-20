import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal
from backend.app.models import GenerationSession, Song, SongFile
from backend.app.schemas import GenerationLog, SongCreate, SongStatus
from backend.app.services.song_pipeline import generate_song_pipeline
from helpers import strip_style_tags


class SongGenerationManager:
    """Task manager that runs the real CLI pipeline in the background."""

    def __init__(self) -> None:
        self.tasks: Dict[int, asyncio.Task] = {}
        self.progress_cache: Dict[int, SongStatus] = {}

    def start_generation(self, song_id: int, payload: SongCreate) -> None:
        if song_id in self.tasks:
            return
        self.tasks[song_id] = asyncio.create_task(self._run_generation(song_id, payload))

    def get_status(self, song_id: int) -> Optional[SongStatus]:
        return self.progress_cache.get(song_id)

    def _cache_status(self, song_id: int, status: SongStatus) -> None:
        self.progress_cache[song_id] = status

    async def shutdown(self) -> None:
        """Cancel any in-flight generation tasks on application shutdown."""
        if not self.tasks:
            return
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()
        self.progress_cache.clear()

    async def _run_generation(self, song_id: int, payload: SongCreate) -> None:
        session: Session = SessionLocal()
        logs: List[GenerationLog] = []
        log_lock = Lock()
        current_progress = 0
        try:
            generation = GenerationSession(
                song_id=song_id,
                session_id=str(uuid.uuid4()),
                current_stage="queued",
                progress_percentage=0,
                logs=json.dumps([]),
                started_at=datetime.utcnow(),
            )
            session.add(generation)
            song = session.get(Song, song_id)
            if song:
                song.status = "generating"
                song.generation_started_at = datetime.utcnow()
            session.commit()

            def add_log(message: str, progress: Optional[int] = None, status: str = "generating") -> None:
                nonlocal current_progress
                with log_lock:
                    if progress is not None:
                        current_progress = progress
                    log_entry = GenerationLog(timestamp=datetime.utcnow(), message=message)
                    logs.append(log_entry)
                    self._cache_status(
                        song_id,
                        SongStatus(
                            song_id=song_id,
                            progress=current_progress,
                            current_stage=message,
                            status=status,
                            estimated_seconds_remaining=None,
                            logs=list(logs),
                            error_message=None,
                        ),
                    )

            add_log("Starting pipeline", progress=5)

            loop = asyncio.get_running_loop()
            # Run the real CLI workflow in a thread to avoid blocking the event loop.
            final_state = await loop.run_in_executor(
                None,
                lambda: generate_song_pipeline(
                    payload.user_prompt,
                    payload.use_local,
                    payload.title,
                    payload.persona,
                    payload.style,
                    add_log,
                ),
            )

            add_log("Finalizing results", progress=95)

            lyrics = final_state.get("lyrics") if isinstance(final_state, dict) else None
            metadata = final_state.get("metadata") if isinstance(final_state, dict) else {}
            filename = final_state.get("filename") if isinstance(final_state, dict) else None
            album_art = final_state.get("album_art") if isinstance(final_state, dict) else None

            if song:
                song.status = "completed"
                song.lyrics = lyrics
                song.clean_lyrics = strip_style_tags(lyrics) if lyrics else None
                song.metadata_json = json.dumps(metadata) if metadata else None
                song.album_art = album_art
                song.generation_completed_at = datetime.utcnow()
                song.score = int(final_state.get("score", 0)) if isinstance(final_state, dict) else None
            if filename:
                path = Path(filename)
                song_file = SongFile(
                    song_id=song_id,
                    file_type="lyrics",
                    file_path=str(path),
                    file_name=path.name,
                    file_size=path.stat().st_size if path.exists() else None,
                    mime_type="text/markdown",
                    is_primary=True,
                )
                session.add(song_file)

            add_log("Generation completed", progress=100, status="completed")

            if generation:
                generation.current_stage = "completed"
                generation.progress_percentage = 100
                generation.logs = json.dumps([log.model_dump(mode="json") for log in logs])
                generation.completed_at = datetime.utcnow()
                generation.updated_at = datetime.utcnow()
            session.commit()
        except Exception as exc:  # pragma: no cover - defensive logging for runtime errors
            error_log = GenerationLog(timestamp=datetime.utcnow(), message=f"Error: {exc}")
            logs.append(error_log)

            # Clean up generation session and song to avoid blank/failed records
            db_gen = session.query(GenerationSession).filter(GenerationSession.song_id == song_id)
            db_gen.delete()

            if song := session.get(Song, song_id):
                session.delete(song)
            session.commit()

            self._cache_status(
                song_id,
                SongStatus(
                    song_id=song_id,
                    progress=0,
                    current_stage="error",
                    status="failed",
                    estimated_seconds_remaining=None,
                    logs=logs,
                    error_message=str(exc),
                ),
            )
        finally:
            session.close()
            self.tasks.pop(song_id, None)


generation_manager = SongGenerationManager()
