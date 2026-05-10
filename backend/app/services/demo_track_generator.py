import asyncio
import json
from threading import Lock
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal
from backend.app.models import Song, SongFile
from backend.app.schemas import DemoTrackStatus, GenerationLog
from backend.app.services.minimax_service import MiniMaxDemoTrackResult, MiniMaxMusicService


class DemoTrackGenerationManager:
    """Background task manager for MiniMax-powered demo tracks."""

    def __init__(self) -> None:
        self.tasks: Dict[int, asyncio.Task] = {}
        self.progress_cache: Dict[int, DemoTrackStatus] = {}

    def start_generation(self, song_id: int) -> DemoTrackStatus:
        if song_id in self.tasks:
            return self.progress_cache.get(song_id) or self._status(song_id=song_id, progress=5, current_stage="Queued demo track generation", status="queued", logs=[])

        status = self._status(
            song_id=song_id,
            progress=5,
            current_stage="Queued demo track generation",
            status="queued",
            logs=[],
        )
        self._cache_status(song_id, status)
        self.tasks[song_id] = asyncio.create_task(self._run_generation(song_id))
        return status

    def get_status(self, song_id: int) -> Optional[DemoTrackStatus]:
        return self.progress_cache.get(song_id)

    def _cache_status(self, song_id: int, status: DemoTrackStatus) -> None:
        self.progress_cache[song_id] = status

    async def shutdown(self) -> None:
        if not self.tasks:
            return
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()
        self.progress_cache.clear()

    async def _run_generation(self, song_id: int) -> None:
        session: Session = SessionLocal()
        logs: List[GenerationLog] = []
        log_lock = Lock()
        current_progress = 0

        def add_log(message: str, progress: Optional[int] = None, status: str = "generating", error_message: Optional[str] = None) -> None:
            nonlocal current_progress
            with log_lock:
                if progress is not None:
                    current_progress = progress
                logs.append(GenerationLog(timestamp=self._utcnow(), message=message))
                self._cache_status(
                    song_id,
                    self._status(
                        song_id=song_id,
                        progress=current_progress,
                        current_stage=message,
                        status=status,
                        logs=list(logs),
                        error_message=error_message,
                    ),
                )

        try:
            song = session.get(Song, song_id)
            if not song:
                raise RuntimeError("Song not found.")

            metadata = {}
            if song.metadata_json:
                try:
                    metadata = json.loads(song.metadata_json)
                except json.JSONDecodeError:
                    metadata = {}

            add_log("Preparing MiniMax request", progress=15)
            service = MiniMaxMusicService()
            song_date = song.created_at.strftime("%Y-%m-%d") if song.created_at else None

            loop = asyncio.get_running_loop()
            add_log("Requesting MiniMax music generation", progress=45)
            result = await loop.run_in_executor(
                None,
                lambda: service.generate_demo_track(
                    title=song.title,
                    user_prompt=song.user_prompt or "",
                    lyrics=song.lyrics or "",
                    clean_lyrics=song.clean_lyrics,
                    metadata=metadata,
                    persona=song.persona,
                    style=song.style,
                    vocal_gender=song.vocal_gender,
                    date=song_date,
                ),
            )

            add_log("Saving demo track", progress=85)
            self._save_demo_track(session, song_id, result)
            add_log("Demo track created", progress=100, status="completed")
        except Exception as exc:  # pragma: no cover - runtime safety
            add_log(f"Demo track failed: {exc}", progress=current_progress or 0, status="failed", error_message=str(exc))
        finally:
            session.close()
            self.tasks.pop(song_id, None)

    def _save_demo_track(self, session: Session, song_id: int, result: MiniMaxDemoTrackResult) -> None:
        session.query(SongFile).filter(
            SongFile.song_id == song_id,
            SongFile.file_type == "demo_track",
        ).update({SongFile.is_primary: False})

        existing = (
            session.query(SongFile)
            .filter(SongFile.song_id == song_id, SongFile.file_path == result.file_path)
            .first()
        )
        if not existing:
            existing = SongFile(
                song_id=song_id,
                file_type="demo_track",
                file_path=result.file_path,
                file_name=result.file_name,
            )

        existing.file_type = "demo_track"
        existing.file_path = result.file_path
        existing.file_name = result.file_name
        existing.file_size = result.file_size
        existing.mime_type = result.mime_type
        existing.is_primary = True
        session.add(existing)
        session.commit()

    def _status(
        self,
        song_id: int,
        progress: int,
        current_stage: Optional[str],
        status: str,
        logs: List[GenerationLog],
        error_message: Optional[str] = None,
    ) -> DemoTrackStatus:
        return DemoTrackStatus(
            song_id=song_id,
            progress=progress,
            current_stage=current_stage,
            status=status,
            estimated_seconds_remaining=None,
            logs=logs,
            error_message=error_message,
        )

    def _utcnow(self):
        from datetime import datetime

        return datetime.utcnow()


demo_track_generation_manager = DemoTrackGenerationManager()