import json
import unittest
from unittest.mock import patch

from langchain_core.prompts import PromptTemplate

from backend.shared.ai_functions import generate_metadata_summary
from backend.shared.helpers import map_artist_references_to_suno_styles


class _StubLLM:
    def __init__(self, responses):
        self._responses = list(responses)

    def invoke(self, _prompt: str) -> str:
        if not self._responses:
            raise AssertionError("Stub LLM ran out of responses.")
        return self._responses.pop(0)


class ArtistStyleMappingTests(unittest.TestCase):
    def setUp(self):
        self.style_catalog = {
            "artist_styles": (
                "Nirvana: 90s grunge, dark male vocals, distorted guitars, raw angst\n"
                "Taylor Swift: pop, alternative folk, emotional, female vocals"
            )
        }

    def test_map_artist_references_to_suno_styles_replaces_artist_tokens(self):
        result = map_artist_references_to_suno_styles(
            ["Nirvana", "grunge", "in the style of Taylor Swift"],
            "Write a song in the style of Nirvana",
            self.style_catalog,
        )
        lowered = {token.lower() for token in result}

        self.assertIn("90s grunge", lowered)
        self.assertIn("dark male vocals", lowered)
        self.assertIn("grunge", lowered)
        self.assertFalse(any("nirvana" in token for token in lowered))
        self.assertFalse(any("taylor swift" in token for token in lowered))

    def test_generate_metadata_summary_replaces_artist_name_tokens(self):
        payload = {
            "description": "A dark alt-rock breakup song.",
            "suno_styles": ["Nirvana", "grunge"],
            "suno_exclude_styles": [],
            "target_audience": "Alternative rock listeners",
            "commercial_potential": "Strong niche appeal",
        }
        prompt = PromptTemplate.from_template("{user_input}")

        with patch("backend.shared.ai_functions.get_llm", return_value=_StubLLM([json.dumps(payload)])):
            metadata = generate_metadata_summary(
                prompt,
                "lyrics",
                "Write a dark song in the style of Nirvana",
                {"genre": "rock"},
                "",
                use_local=False,
                style_catalog=self.style_catalog,
            )

        lowered = {token.lower() for token in metadata["suno_styles"]}
        self.assertIn("90s grunge", lowered)
        self.assertIn("grunge", lowered)
        self.assertFalse(any("nirvana" in token for token in lowered))

    def test_generate_metadata_summary_fallback_also_maps_artist_styles(self):
        prompt = PromptTemplate.from_template("{user_input}")

        with patch("backend.shared.ai_functions.get_llm", return_value=_StubLLM(["not-json"])):
            metadata = generate_metadata_summary(
                prompt,
                "lyrics",
                "Write a dark song in the style of Nirvana",
                {"genre": "rock"},
                "",
                use_local=False,
                style_catalog=self.style_catalog,
            )

        lowered = {token.lower() for token in metadata["suno_styles"]}
        self.assertIn("90s grunge", lowered)
        self.assertFalse(any("nirvana" in token for token in lowered))


if __name__ == "__main__":
    unittest.main()
