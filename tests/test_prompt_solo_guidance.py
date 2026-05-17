import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class PromptSoloGuidanceTests(unittest.TestCase):
    def test_song_drafter_prompt_forbids_numbered_solo_headers(self):
        prompt = (REPO_ROOT / "prompts" / "song_drafter.txt").read_text(encoding="utf-8")

        self.assertIn("Never output numbered solo headers", prompt)
        self.assertIn("render the visible lyric header as", prompt)
        self.assertIn("specific instrumental tag such as", prompt)

    def test_song_revision_prompt_normalizes_numbered_solo_headers(self):
        prompt = (REPO_ROOT / "prompts" / "song_revision.txt").read_text(encoding="utf-8")

        self.assertIn("Never leave numbered solo headers", prompt)
        self.assertIn("normalize the visible lyric header", prompt)
        self.assertIn("specific instrumental tag such as", prompt)

    def test_song_structure_planner_prompt_uses_visible_non_numbered_solo_tags(self):
        prompt = (REPO_ROOT / "prompts" / "song_structure_planner.txt").read_text(encoding="utf-8")

        self.assertIn("Never emit numbered solo tags", prompt)
        self.assertIn("the corresponding `tags` must still use the visible lyric header `[Solo]`", prompt)


if __name__ == "__main__":
    unittest.main()