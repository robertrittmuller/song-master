import unittest

from backend.shared.helpers import (
    apply_section_plan_tags_to_lyrics,
    get_default_lyric_tags,
    normalize_lyrics_section_tags,
    remove_title_from_lyrics,
    strip_style_tags,
)


class LyricsTagNormalizationTests(unittest.TestCase):
    def test_normalize_lyrics_section_tags_rewrites_numbered_solos(self):
        lyrics = "[Verse 1]\n[Solo 1]\nlead line\n[Solo 2]\nmore lead"

        normalized = normalize_lyrics_section_tags(lyrics)

        self.assertEqual(normalized, "[Verse 1]\n[Solo]\nlead line\n[Solo]\nmore lead")

    def test_strip_style_tags_preserves_generic_and_instrument_solo_headers(self):
        lyrics = "[Verse 1] [style: tense]\nline\n[Solo 1]\n[Violin Solo]\n[Instruments: soaring violin]"

        stripped = strip_style_tags(lyrics)

        self.assertEqual(stripped, "[Verse 1]\n\nline\n[Solo]\n\n[Violin Solo]")

    def test_apply_section_plan_tags_to_lyrics_restores_missing_header_metadata(self):
        lyrics = "[Verse 1]\nline\n\n[Chorus]\nhook"
        section_plan = [
            {
                "name": "Verse 1",
                "tags": ["[Verse 1]", "[Female Vocal]"],
                "style_tags": ["[style: intimate synthpop]", "[Dynamic: restrained]"],
            },
            {
                "name": "Chorus",
                "tags": ["[Chorus]", "[Female Vocal]"],
                "style_tags": ["[style: wide synthpop]", "[Dynamic: lifted]"],
            },
        ]

        normalized = apply_section_plan_tags_to_lyrics(lyrics, section_plan)

        self.assertIn("[Verse 1] [Female Vocal] [style: intimate synthpop] [Dynamic: restrained]", normalized)
        self.assertIn("[Chorus] [Female Vocal] [style: wide synthpop] [Dynamic: lifted]", normalized)

    def test_apply_section_plan_tags_to_lyrics_normalizes_plain_section_headings(self):
        lyrics = "## Verse 1\nline\n\nChorus:\nhook"
        section_plan = [
            {
                "name": "Verse 1",
                "tags": ["[Verse 1]", "[Male Vocal]"],
                "style_tags": ["[style: acoustic rock]"],
            },
            {
                "name": "Chorus",
                "tags": ["[Chorus]", "[Male Vocal]"],
                "style_tags": ["[style: acoustic rock, lifted]"],
            },
        ]

        normalized = apply_section_plan_tags_to_lyrics(lyrics, section_plan)

        self.assertIn("[Verse 1] [Male Vocal] [style: acoustic rock]\nline", normalized)
        self.assertIn("[Chorus] [Male Vocal] [style: acoustic rock, lifted]\nhook", normalized)

    def test_remove_title_from_lyrics_strips_bare_title_line(self):
        lyrics = "Neon Harbor\n\n[Intro]\nSynths rise\n\n[Verse 1]\nLine"

        stripped = remove_title_from_lyrics(lyrics, "Neon Harbor")

        self.assertEqual(stripped, "[Intro]\nSynths rise\n\n[Verse 1]\nLine")

    def test_remove_title_from_lyrics_strips_title_repeated_inside_intro(self):
        lyrics = "Title: Neon Harbor\n\n[Intro] [style: synthpop]\nNeon Harbor\nSynths rise"

        stripped = remove_title_from_lyrics(lyrics, "Neon Harbor")

        self.assertEqual(stripped, "[Intro] [style: synthpop]\nSynths rise")

    def test_get_default_lyric_tags_returns_bracketless_default_tags(self):
        tags = get_default_lyric_tags()

        self.assertIn("Intro", tags)
        self.assertIn("Female Vocal", tags)
        self.assertIn("Dynamic: Explosive energy", tags)
        self.assertNotIn("[Intro]", tags)


if __name__ == "__main__":
    unittest.main()
