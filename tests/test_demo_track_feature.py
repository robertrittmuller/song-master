import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401 - registers model metadata
from backend.app.api.routes.songs import create_demo_track, get_demo_track_status
from backend.app.core.config import Settings
from backend.app.db.base import Base
from backend.app.models import Song, SongFile, User
from backend.app.schemas import DemoTrackStatus
from backend.app.services.minimax_service import MiniMaxMusicService


class _MockResponse:
    def __init__(self, json_body=None, content_chunks=None, status_code=200):
        self._json_body = json_body or {}
        self._content_chunks = content_chunks or []
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_body

    def iter_content(self, chunk_size=1024):
        del chunk_size
        for chunk in self._content_chunks:
            yield chunk


class MiniMaxMusicServiceTests(unittest.TestCase):
    def test_generate_demo_track_downloads_audio_and_returns_metadata(self):
        settings = Settings(
            minimax_api_key="demo-key",
            minimax_music_model="music-2.6",
            minimax_api_base="https://api.minimax.io/v1",
            minimax_request_timeout=5,
        )
        service = MiniMaxMusicService(settings=settings)

        with tempfile.TemporaryDirectory() as temp_dir:
            abs_image_base = str(Path(temp_dir) / "2026-04-12 - Demo Song")
            with patch(
                "backend.app.services.minimax_service.get_song_storage_info",
                return_value={
                    "abs_folder": temp_dir,
                    "abs_image_base": abs_image_base,
                },
            ), patch(
                "backend.app.services.minimax_service.relativize_storage_path",
                side_effect=lambda path: Path(path).name,
            ), patch(
                "backend.app.services.minimax_service.requests.post",
                return_value=_MockResponse(
                    json_body={
                        "data": {
                            "audio": "https://cdn.example.com/demo.mp3",
                            "status": 2,
                        },
                        "trace_id": "trace-123",
                        "extra_info": {
                            "music_duration": 25364,
                            "music_sample_rate": 44100,
                            "music_channel": 2,
                            "bitrate": 256000,
                        },
                        "base_resp": {
                            "status_code": 0,
                            "status_msg": "success",
                        },
                    }
                ),
            ) as mock_post, patch(
                "backend.app.services.minimax_service.requests.get",
                return_value=_MockResponse(content_chunks=[b"demo-audio"]),
            ):
                result = service.generate_demo_track(
                    title="Demo Song",
                    user_prompt="Dreamy synth pop for a late-night drive.",
                    lyrics="[Verse]\nCity lights and satellite hearts",
                    clean_lyrics="[Verse]\nCity lights and satellite hearts",
                    metadata={"genre": "synth pop", "mood": "dreamy"},
                    persona="antidote",
                )

        self.assertEqual(result.model, "music-2.6")
        self.assertTrue(result.file_name.endswith(".mp3"))
        self.assertEqual(result.trace_id, "trace-123")
        self.assertEqual(result.sample_rate, 44100)
        self.assertEqual(mock_post.call_args.kwargs["json"]["output_format"], "url")
        self.assertEqual(mock_post.call_args.kwargs["json"]["model"], "music-2.6")

    def test_generate_demo_track_strips_asterisk_effect_tags_from_payload(self):
        settings = Settings(
            minimax_api_key="demo-key",
            minimax_music_model="music-2.6",
            minimax_api_base="https://api.minimax.io/v1",
            minimax_request_timeout=5,
        )
        service = MiniMaxMusicService(settings=settings)

        with tempfile.TemporaryDirectory() as temp_dir:
            abs_image_base = str(Path(temp_dir) / "2026-04-12 - Demo Song")
            with patch(
                "backend.app.services.minimax_service.get_song_storage_info",
                return_value={
                    "abs_folder": temp_dir,
                    "abs_image_base": abs_image_base,
                },
            ), patch(
                "backend.app.services.minimax_service.relativize_storage_path",
                side_effect=lambda path: Path(path).name,
            ), patch(
                "backend.app.services.minimax_service.requests.post",
                return_value=_MockResponse(
                    json_body={
                        "data": {
                            "audio": "https://cdn.example.com/demo.mp3",
                            "status": 2,
                        },
                        "base_resp": {
                            "status_code": 0,
                            "status_msg": "success",
                        },
                    }
                ),
            ) as mock_post, patch(
                "backend.app.services.minimax_service.requests.get",
                return_value=_MockResponse(content_chunks=[b"demo-audio"]),
            ):
                service.generate_demo_track(
                    title="Demo Song",
                    user_prompt="Huge rock energy.",
                    lyrics="[Verse]\n*crowd cheering*\nCity lights ignite the dark",
                    clean_lyrics="[Verse]\n*crowd cheering*\nCity lights ignite the dark",
                )

        self.assertEqual(
            mock_post.call_args.kwargs["json"]["lyrics"],
            "[Verse]\n\nCity lights ignite the dark",
        )


class DemoTrackRouteTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.session_factory = sessionmaker(bind=engine)

    def test_create_demo_track_rejects_local_song(self):
        session = self.session_factory()
        user = User(username="writer", email="writer@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        session.refresh(user)

        song = Song(
            user_id=user.id,
            title="Local Song",
            user_prompt="Make a local song.",
            status="completed",
            use_local=True,
            lyrics="[Verse]\nOffline and loud",
        )
        session.add(song)
        session.commit()
        session.refresh(song)

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(create_demo_track(song.id, db=session, current_user=user))

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("local-only songs", ctx.exception.detail)

    def test_create_demo_track_starts_background_job_for_completed_song(self):
        session = self.session_factory()
        user = User(username="writer2", email="writer2@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        session.refresh(user)

        song = Song(
            user_id=user.id,
            title="Remote Song",
            user_prompt="Make a remote song.",
            status="completed",
            use_local=False,
            lyrics="[Verse]\nTurn the freeway into starlight",
            clean_lyrics="[Verse]\nTurn the freeway into starlight",
        )
        session.add(song)
        session.commit()
        session.refresh(song)

        queued = DemoTrackStatus(
            song_id=song.id,
            progress=5,
            current_stage="Queued demo track generation",
            status="queued",
            logs=[],
            error_message=None,
        )

        with patch(
            "backend.app.api.routes.songs.demo_track_generation_manager.start_generation",
            return_value=queued,
        ) as start_generation:
            result = asyncio.run(create_demo_track(song.id, db=session, current_user=user))

        self.assertEqual(result.status, "queued")
        start_generation.assert_called_once_with(song.id)

    def test_get_demo_track_status_falls_back_to_completed_when_track_exists(self):
        session = self.session_factory()
        user = User(username="writer3", email="writer3@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        session.refresh(user)

        song = Song(
            user_id=user.id,
            title="Song With Demo",
            user_prompt="Make a song with a demo.",
            status="completed",
            use_local=False,
            lyrics="[Verse]\nA skyline humming in the rain",
        )
        session.add(song)
        session.commit()
        session.refresh(song)

        session.add(
            SongFile(
                song_id=song.id,
                file_type="demo_track",
                file_path="songs/2026-04-12 - Song With Demo/demo.mp3",
                file_name="demo.mp3",
                mime_type="audio/mpeg",
                is_primary=True,
            )
        )
        session.commit()

        with patch(
            "backend.app.api.routes.songs.demo_track_generation_manager.get_status",
            return_value=None,
        ):
            result = get_demo_track_status(song.id, db=session, current_user=user)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.progress, 100)


if __name__ == "__main__":
    unittest.main()