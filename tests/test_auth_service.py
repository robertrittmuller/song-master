import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401 - registers model metadata
from backend.app.api.routes.albums import list_albums
from backend.app.db.base import Base
from backend.app.models import Album, Song, SongProposal
from backend.app.services.auth_service import authenticate_user, build_auth_response, change_password, create_user


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.session_factory = sessionmaker(bind=engine)

    def test_first_user_claims_legacy_content(self):
        session = self.session_factory()
        album = Album(name="Legacy Album", description="Imported before auth")
        session.add(album)
        session.flush()
        session.add(
            Song(
                album_id=album.id,
                title="Legacy Song",
                user_prompt="Preserve this song",
                lyrics="Legacy lyrics",
                clean_lyrics="Legacy lyrics",
                status="completed",
                use_local=False,
            )
        )
        session.add(
            SongProposal(
                title="Legacy Proposal",
                prompt="Legacy prompt",
                source_prompt="Legacy source",
                use_local=False,
            )
        )
        session.commit()

        user = create_user(session, "owner", "owner@example.com", "OwnerPass9")
        claimed_album = session.query(Album).filter(Album.name == "Legacy Album").one()
        claimed_song = session.query(Song).filter(Song.title == "Legacy Song").one()
        claimed_proposal = session.query(SongProposal).filter(SongProposal.title == "Legacy Proposal").one()

        self.assertEqual(claimed_album.user_id, user.id)
        self.assertEqual(claimed_song.user_id, user.id)
        self.assertEqual(claimed_proposal.user_id, user.id)

    def test_change_password_rotates_credentials(self):
        session = self.session_factory()
        user = create_user(session, "writer", "writer@example.com", "WriterPass9")

        authenticated_user = authenticate_user(session, "writer", "WriterPass9")
        response = build_auth_response(authenticated_user)
        self.assertTrue(response.access_token)
        self.assertEqual(response.user.username, "writer")

        change_password(session, user, "WriterPass9", "WriterPass10")

        with self.assertRaises(HTTPException):
            authenticate_user(session, "writer", "WriterPass9")

        refreshed_user = authenticate_user(session, "writer@example.com", "WriterPass10")
        self.assertEqual(refreshed_user.id, user.id)

    def test_album_listing_is_scoped_to_current_user(self):
        session = self.session_factory()
        owner = create_user(session, "owner", "owner@example.com", "OwnerPass9")
        other = create_user(session, "other", "other@example.com", "OtherPass9")

        session.add(Album(user_id=owner.id, name="Owner Album", description="Mine"))
        session.add(Album(user_id=other.id, name="Other Album", description="Not mine"))
        session.commit()

        albums = list_albums(db=session, current_user=owner)

        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].name, "Owner Album")


if __name__ == "__main__":
    unittest.main()