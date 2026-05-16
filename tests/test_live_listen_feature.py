import asyncio
import io
import unittest
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from langchain_core.prompts import PromptTemplate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401 - registers model metadata
from backend.app.api.routes.songs import live_listen_feedback
from backend.app.db.base import Base
from backend.app.models import Song, User
from backend.app.services.live_listen_service import process_live_listen_feedback


class LiveListenServiceTests(unittest.TestCase):
    def test_local_song_uses_remote_models_for_live_listen(self):
        upload = UploadFile(filename="take.mp3", file=io.BytesIO(b"mp3-data"))

        with patch(
            "backend.app.services.live_listen_service.review_song_with_audio",
            return_value="Tighten the second verse cadence.",
        ) as review_mock, patch(
            "backend.app.services.live_listen_service.build_prompts",
            return_value={
                "revision": PromptTemplate(
                    input_variables=["lyrics", "feedback", "user_input", "brief"],
                    template="{lyrics}\n{feedback}\n{user_input}\n{brief}",
                )
            },
        ), patch(
            "backend.app.services.live_listen_service.revise_lyrics",
            return_value="Revised lyrics",
        ) as revise_mock:
            result = asyncio.run(
                process_live_listen_feedback(
                    song_id=1,
                    file=upload,
                    song_data={
                        "lyrics": "Original lyrics",
                        "user_prompt": "Keep it urgent.",
                    },
                    use_local=True,
                )
            )

        self.assertEqual(result["revised_lyrics"], "Revised lyrics")
        review_mock.assert_called_once()
        self.assertFalse(review_mock.call_args.args[2])
        revise_mock.assert_called_once()
        self.assertFalse(revise_mock.call_args.args[3])


class LiveListenRouteTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.session_factory = sessionmaker(bind=engine)

    def test_live_feedback_rejects_provider_failure_with_400(self):
        session = self.session_factory()
        user = User(username="writer", email="writer@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        session.refresh(user)

        song = Song(
            user_id=user.id,
            title="Local Song",
            user_prompt="Make it hit hard.",
            status="completed",
            use_local=True,
            lyrics="[Verse]\nOffline and loud",
        )
        session.add(song)
        session.commit()
        session.refresh(song)

        upload = UploadFile(filename="take.mp3", file=io.BytesIO(b"mp3-data"))

        with patch(
            "backend.app.services.live_listen_service.review_song_with_audio",
            return_value="Multimodal LLM error: provider unavailable.",
        ):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(live_listen_feedback(song.id, file=upload, db=session, current_user=user))

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "Multimodal LLM error: provider unavailable.")


if __name__ == "__main__":
    unittest.main()