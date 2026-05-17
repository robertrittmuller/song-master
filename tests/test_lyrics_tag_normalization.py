import unittest

from backend.shared.helpers import normalize_lyrics_section_tags, strip_style_tags


class LyricsTagNormalizationTests(unittest.TestCase):
    def test_normalize_lyrics_section_tags_rewrites_numbered_solos(self):
        lyrics = "[Verse 1]\n[Solo 1]\nlead line\n[Solo 2]\nmore lead"

        normalized = normalize_lyrics_section_tags(lyrics)

        self.assertEqual(normalized, "[Verse 1]\n[Solo]\nlead line\n[Solo]\nmore lead")

    def test_strip_style_tags_preserves_generic_and_instrument_solo_headers(self):
        lyrics = "[Verse 1] [style: tense]\nline\n[Solo 1]\n[Violin Solo]\n[Instruments: soaring violin]"

        stripped = strip_style_tags(lyrics)

        self.assertEqual(stripped, "[Verse 1]\n\nline\n[Solo]\n\n[Violin Solo]")


if __name__ == "__main__":
    unittest.main()