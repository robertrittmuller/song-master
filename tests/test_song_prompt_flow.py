import json
import unittest
from unittest.mock import patch

from langchain_core.prompts import PromptTemplate

from ai_functions import build_song_brief, plan_song_structure, run_specialized_reviews


class _StubLLM:
    def __init__(self, responses):
        self._responses = list(responses)

    def invoke(self, _prompt: str) -> str:
        if not self._responses:
            raise AssertionError("Stub LLM ran out of responses.")
        return self._responses.pop(0)


class SongPromptFlowTests(unittest.TestCase):
    def test_build_song_brief_returns_llm_brief_without_deterministic_section_injection(self):
        payload = {
            "theme": "restless highway escape",
            "point_of_view": "first person",
            "emotional_arc": "regret to release",
            "hook_strategy": "repeat the exit sign image",
            "imagery_anchors": ["dashboard glow", "wet asphalt"],
            "non_negotiables": ["keep it grounded"],
            "required_lines": ["we stay gold"],
            "avoid_phrases": ["heart on the line"],
            "suno_style_tokens": ["heartland rock"],
            "section_plan": [
                {
                    "name": "Verse 1",
                    "goal": "Open on the night drive.",
                    "tags": ["[Verse 1]", "[Male Vocal]"],
                    "style_tags": ["[style: heartland rock, grounded]"],
                },
                {
                    "name": "Chorus",
                    "goal": "Land the hook.",
                    "tags": ["[Chorus]", "[Male Vocal]"],
                    "style_tags": ["[style: heartland rock, wider]"],
                },
            ],
        }

        with patch("ai_functions.get_llm", return_value=_StubLLM([json.dumps(payload)])):
            brief = build_song_brief(
                PromptTemplate.from_template("{user_input}"),
                'Write a highway rock song with two guitar solos and the line "we stay gold"',
                "styles",
                "tags",
                "persona",
                {"genre": "rock", "vocal_gender": "Male"},
                use_local=False,
            )

        self.assertEqual([section["name"] for section in brief["section_plan"]], ["Verse 1", "Chorus"])
        self.assertEqual(brief["required_lines"], ["we stay gold"])

    def test_build_song_brief_raises_when_model_does_not_return_json(self):
        with patch("ai_functions.get_llm", return_value=_StubLLM(["not json"])):
            with self.assertRaises(ValueError):
                build_song_brief(
                    PromptTemplate.from_template("{user_input}"),
                    "Write a song",
                    "styles",
                    "tags",
                    "persona",
                    {"genre": "rock"},
                    use_local=False,
                )

    def test_plan_song_structure_uses_model_output_without_repairing_order(self):
        payload = {
            "sections": [
                {
                    "name": "Chorus",
                    "goal": "Open with the hook.",
                    "tags": ["[Chorus]", "[Female Vocal]"],
                    "style_tags": ["[style: wide, hook-forward]"],
                },
                {
                    "name": "Verse 1",
                    "goal": "Explain why the hook matters.",
                    "tags": ["[Verse 1]", "[Female Vocal]"],
                    "style_tags": ["[style: tense, close-up]"],
                },
            ]
        }

        with patch("ai_functions.get_llm", return_value=_StubLLM([json.dumps(payload)])):
            section_plan = plan_song_structure(
                PromptTemplate.from_template("{brief}"),
                "Write a dramatic rock song",
                {"section_plan": []},
                "guidance",
                "tag context",
                {"genre": "rock", "vocal_gender": "Female"},
                use_local=False,
            )

        self.assertEqual([section["name"] for section in section_plan], ["Chorus", "Verse 1"])

    def test_run_specialized_reviews_merges_prompt_feedback_only(self):
        review_prompts = {
            "theme": PromptTemplate.from_template("theme {lyrics}"),
            "quality": PromptTemplate.from_template("quality {lyrics}"),
            "suno": PromptTemplate.from_template("suno {lyrics}"),
        }
        responses = [
            json.dumps(
                {
                    "summary": "Theme holds.",
                    "issues": [
                        {
                            "location": "Verse 1",
                            "problem": "Opening image is vague.",
                            "instruction": "Replace the first line with a sharper physical image.",
                            "priority": 2,
                        }
                    ],
                }
            ),
            json.dumps(
                {
                    "summary": "Quality issue found.",
                    "issues": [
                        {
                            "location": "Verse 1",
                            "problem": "Opening image is vague.",
                            "instruction": "Replace the first line with a sharper physical image.",
                            "priority": 2,
                        },
                        {
                            "location": "Chorus",
                            "problem": "Hook is too wordy.",
                            "instruction": "Trim the chorus to one clean central phrase.",
                            "priority": 3,
                        },
                    ],
                }
            ),
            json.dumps({"summary": "Suno tags are clear.", "issues": []}),
        ]

        with patch("ai_functions.get_llm", return_value=_StubLLM(responses)):
            review_results = run_specialized_reviews(
                review_prompts,
                "[Verse 1]\nLine\n\n[Chorus]\nLine",
                use_local=False,
                user_input="Write a rock song",
                brief={"theme": "escape"},
            )

        self.assertEqual(len(review_results["issues"]), 2)
        self.assertIn("Trim the chorus to one clean central phrase.", review_results["feedback"])


if __name__ == "__main__":
    unittest.main()
