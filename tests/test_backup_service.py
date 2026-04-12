import json
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401 - registers model metadata
from backend.app.db.base import Base
from backend.app.models import Album, Song, SongFile, SongProposal, User
from backend.app.services.backup_service import create_backup_zip, restore_backup_zip


class BackupServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.storage_dir = self.repo_root / "songs" / "2026-04-12 - Backup Test"
        self.storage_dir.mkdir(parents=True)
        self.app_image_path = self.repo_root / "images" / "header.jpg"
        self.markdown_path = self.storage_dir / "2026-04-12 - Backup Test.md"
        self.art_path = self.storage_dir / "2026-04-12 - Backup Test.jpg"
        self.persona_path = self.repo_root / "personas" / "backup-persona.md"
        self.app_image_path.parent.mkdir(parents=True)
        self.app_image_path.write_bytes(b"app image bytes")
        self.markdown_path.write_text("## Backup Test\n\n### Song Lyrics:\nLine one\n", encoding="utf-8")
        self.art_path.write_bytes(b"fake image bytes")
        self.persona_path.parent.mkdir(parents=True)
        self.persona_path.write_text("# Backup Persona\n\nTest persona content.\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _session_factory(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        return sessionmaker(bind=engine)

    def _seed_source_session(self):
        SessionLocal = self._session_factory()
        session = SessionLocal()
        user = User(username="backup", email="backup@example.com", password_hash="hash")
        session.add(user)
        session.flush()
        album = Album(user_id=user.id, name="Backup Album", description="Songs to preserve")
        session.add(album)
        session.flush()
        song = Song(
            album_id=album.id,
            title="Backup Test",
            user_prompt="Write a backup test song",
            lyrics="[Verse 1]\nLine one",
            clean_lyrics="Line one",
            album_art="songs/2026-04-12 - Backup Test/2026-04-12 - Backup Test.jpg",
            status="completed",
            use_local=False,
        )
        session.add(song)
        session.flush()
        session.add(
            SongFile(
                song_id=song.id,
                file_type="lyrics",
                file_path="songs/2026-04-12 - Backup Test/2026-04-12 - Backup Test.md",
                file_name="2026-04-12 - Backup Test.md",
                mime_type="text/markdown",
                is_primary=True,
            )
        )
        session.add(
            SongProposal(
                title="Backup Proposal",
                prompt="Write a backup proposal song.",
                source_prompt="Create backup proposal ideas.",
                use_local=False,
            )
        )
        session.commit()
        return session

    def test_backup_zip_contains_database_rows_and_assets(self):
        with patch("backend.app.services.backup_service.get_repo_root", return_value=str(self.repo_root)):
            session = self._seed_source_session()
            backup = create_backup_zip(session).getvalue()

        with zipfile.ZipFile(BytesIO(backup), "r") as archive:
            names = set(archive.namelist())
            self.assertIn("manifest.json", names)
            self.assertIn("data.json", names)
            self.assertIn(
                "assets/songs/2026-04-12 - Backup Test/2026-04-12 - Backup Test.md",
                names,
            )
            self.assertIn(
                "assets/songs/2026-04-12 - Backup Test/2026-04-12 - Backup Test.jpg",
                names,
            )
            self.assertIn("assets/personas/backup-persona.md", names)
            self.assertNotIn("assets/images/header.jpg", names)
            data = json.loads(archive.read("data.json").decode("utf-8"))

        self.assertEqual(len(data["users"]), 1)
        self.assertEqual(len(data["albums"]), 1)
        self.assertEqual(len(data["songs"]), 1)
        self.assertEqual(len(data["song_proposals"]), 1)
        self.assertEqual(len(data["song_files"]), 1)

    def test_restore_imports_once_then_skips_duplicates(self):
        with patch("backend.app.services.backup_service.get_repo_root", return_value=str(self.repo_root)):
            source_session = self._seed_source_session()
            backup = create_backup_zip(source_session).getvalue()
            self.persona_path.unlink()

            RestoreSession = self._session_factory()
            restore_session = RestoreSession()
            first_result = restore_backup_zip(restore_session, backup)
            second_result = restore_backup_zip(restore_session, backup)

        self.assertEqual(first_result.imported["users"], 1)
        self.assertEqual(first_result.imported["albums"], 1)
        self.assertEqual(first_result.imported["songs"], 1)
        self.assertEqual(first_result.imported["song_proposals"], 1)
        self.assertEqual(first_result.imported["song_files"], 1)
        self.assertEqual(first_result.restored_files, 1)
        self.assertEqual(second_result.skipped["users"], 1)
        self.assertEqual(second_result.skipped["albums"], 1)
        self.assertEqual(second_result.skipped["songs"], 1)
        self.assertEqual(second_result.skipped["song_proposals"], 1)
        self.assertEqual(second_result.skipped["song_files"], 1)
        self.assertTrue(self.persona_path.exists())
        self.assertEqual(restore_session.query(Song).count(), 1)
        self.assertEqual(restore_session.query(SongProposal).count(), 1)
        self.assertEqual(restore_session.query(SongFile).count(), 1)


if __name__ == "__main__":
    unittest.main()
