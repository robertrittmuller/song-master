import json
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401 - registers model metadata
from backend.app.api.routes.albums import _build_album_art_request, create_album, generate_album_cover_art
from backend.app.db.base import Base
from backend.app.models import Album, Song
from backend.app.schemas import AlbumArtGenerateRequest, AlbumCreate
from backend.app.services.auth_service import create_user


class AlbumArtFeatureTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.session_factory = sessionmaker(bind=engine)

    def test_album_art_prompt_uses_personas_lyrics_and_direction(self):
        album = Album(
            name="Night Static",
            description="A glossy synth-noir record about distance and velocity.",
            art_prompt_direction="Keep the cover cinematic and rain-soaked.",
        )
        album.songs = [
            Song(
                title="Headlights",
                user_prompt="Neon heartbreak on the freeway",
                persona="antidote",
                lyrics="[Verse]\nMidnight engines glow under violet rain\nThe city bends like chrome in the window",
                clean_lyrics="Midnight engines glow under violet rain\nThe city bends like chrome in the window",
                metadata_json=json.dumps({"description": "Neon heartbreak on the freeway"}),
                status="completed",
                use_local=False,
            ),
            Song(
                title="Static Bloom",
                user_prompt="Electric desire with a dangerous edge",
                persona="anagram",
                lyrics="We wear the sparks like halos in reverse\nEvery red light turns into a dare",
                clean_lyrics="We wear the sparks like halos in reverse\nEvery red light turns into a dare",
                metadata_json=json.dumps({"description": "Electric desire with a dangerous edge"}),
                status="completed",
                use_local=False,
            ),
        ]

        with patch(
            "backend.app.api.routes.albums.read_persona_visual_styles",
            side_effect=lambda persona: f"{persona} visual language",
        ):
            prompt = _build_album_art_request(album)

        self.assertIn("Night Static", prompt)
        self.assertIn("Antidote", prompt)
        self.assertIn("Anagram", prompt)
        self.assertIn("antidote visual language", prompt)
        self.assertIn("Midnight engines glow under violet rain", prompt)
        self.assertIn("Electric desire with a dangerous edge", prompt)
        self.assertIn("Keep the cover cinematic and rain-soaked", prompt)

    def test_create_album_persists_prompt_direction(self):
        session = self.session_factory()
        user = create_user(session, "owner", "owner@example.com", "OwnerPass9")

        created = create_album(
            payload=AlbumCreate(
                name="Signal Fires",
                description="Collected night-drive songs",
                art_prompt_direction="Use stark silhouettes and sodium-vapor light",
            ),
            db=session,
            current_user=user,
        )

        self.assertEqual(created.name, "Signal Fires")
        self.assertEqual(created.art_prompt_direction, "Use stark silhouettes and sodium-vapor light")

    def test_generate_album_art_saves_path_and_direction(self):
        session = self.session_factory()
        user = create_user(session, "owner", "owner@example.com", "OwnerPass9")

        album = Album(user_id=user.id, name="Chrome Saints", description="A unified neon-rock release")
        session.add(album)
        session.flush()
        session.add(
            Song(
                user_id=user.id,
                album_id=album.id,
                title="Chrome Lips",
                user_prompt="Gloss, velocity, and danger",
                persona="antidote",
                lyrics="Chrome lips and dashboard halos",
                clean_lyrics="Chrome lips and dashboard halos",
                status="completed",
                use_local=False,
            )
        )
        session.commit()

        with patch("backend.app.api.routes.albums.os.makedirs"), patch(
            "backend.app.api.routes.albums.generate_artwork_from_prompt",
            return_value="images/albums/album-1-chrome-saints/2026-04-20 - Chrome Saints_art.png",
        ):
            updated = generate_album_cover_art(
                album_id=album.id,
                payload=AlbumArtGenerateRequest(art_prompt_direction="Make it feel dangerous and elegant"),
                db=session,
                current_user=user,
            )

        self.assertEqual(
            updated.album_art,
            "images/albums/album-1-chrome-saints/2026-04-20 - Chrome Saints_art.png",
        )
        self.assertEqual(updated.art_prompt_direction, "Make it feel dangerous and elegant")


if __name__ == "__main__":
    unittest.main()