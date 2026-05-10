import asyncio
import json
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401 - registers model metadata
from backend.app.api.routes.songs import create_song
from backend.app.db.base import Base
from backend.app.models import SongProposal, User
from backend.app.schemas import SongCreate
from backend.app.services.song_proposal_service import generate_song_proposal_ideas


class _StubLLM:
    def __init__(self, response: str):
        self.response = response

    def invoke(self, prompt: str) -> str:
        if "Prompt Creator guidelines" not in prompt:
            raise AssertionError("Prompt creator guidance was not included.")
        return self.response


class SongProposalTests(unittest.TestCase):
    def test_generate_song_proposal_ideas_normalizes_json_response(self):
        payload = {
            "proposals": [
                {
                    "title": f"Idea {index}",
                    "prompt": f"Write song prompt {index} with style, mood, structure, and constraints.",
                }
                for index in range(1, 6)
            ]
        }

        with patch(
            "backend.app.services.song_proposal_service.get_llm",
            return_value=_StubLLM(json.dumps(payload)),
        ):
            proposals = generate_song_proposal_ideas(
                "Make cinematic rock ideas about ocean crossings.",
                count=5,
                use_local=False,
            )

        self.assertEqual(len(proposals), 5)
        self.assertEqual(proposals[0]["title"], "Idea 1")
        self.assertIn("style", proposals[0]["prompt"])

    def test_generate_song_proposal_ideas_rejects_short_response(self):
        payload = {
            "proposals": [
                {
                    "title": "Only One",
                    "prompt": "Write one song prompt.",
                }
            ]
        }

        with patch(
            "backend.app.services.song_proposal_service.get_llm",
            return_value=_StubLLM(json.dumps(payload)),
        ):
            with self.assertRaises(ValueError):
                generate_song_proposal_ideas("Make several ideas.", count=5, use_local=False)


class SongProposalAcceptanceTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.session_factory = sessionmaker(bind=engine)

    def test_create_song_marks_proposal_accepted(self):
        session = self.session_factory()
        user = User(username="writer", email="writer@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        session.refresh(user)

        proposal = SongProposal(
            user_id=user.id,
            title="Idea to accept",
            prompt="Write the accepted song.",
            source_prompt="Make something cinematic.",
            use_local=False,
        )
        session.add(proposal)
        session.commit()
        session.refresh(proposal)

        payload = SongCreate(
            user_prompt="Write the accepted song.",
            title="Accepted Song",
            proposal_id=proposal.id,
            use_local=False,
        )

        with patch("backend.app.api.routes.songs.generation_manager.start_generation") as start_generation:
            song = asyncio.run(create_song(payload, db=session, current_user=user))

        session.refresh(proposal)

        self.assertEqual(song.title, "Accepted Song")
        self.assertEqual(song.user_id, user.id)
        self.assertEqual(proposal.status, "accepted")
        self.assertIsNotNone(proposal.accepted_at)
        start_generation.assert_called_once()


if __name__ == "__main__":
    unittest.main()
