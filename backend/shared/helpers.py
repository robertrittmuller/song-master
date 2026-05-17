import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from tools.create_album_art import generate_album_art_image


def read_styles() -> Dict[str, str]:
    """Load and process style configurations from JSON file."""
    consolidated_path = Path(get_repo_root()) / "styles" / "styles.json"
    if not consolidated_path.exists():
        raise FileNotFoundError(f"Missing consolidated styles file at {consolidated_path}")

    with consolidated_path.open("r") as file:
        raw_styles = json.load(file)

    styles: Dict[str, str] = {}
    for key in ("artist_styles", "core_styles", "example_styles"):
        entries = raw_styles.get(key, [])
        styles[key] = "\n".join(entries) if isinstance(entries, list) else str(entries)

    styles["suno_genres"] = json.dumps(raw_styles.get("suno_genres", {}), separators=(",", ":"))
    return styles


def read_tags() -> Dict[str, str]:
    tags: Dict[str, str] = {}
    tags_dir = Path(get_repo_root()) / "tags"
    for filename in os.listdir(tags_dir):
        if filename.endswith(".txt"):
            with open(tags_dir / filename, "r") as file:
                tags[filename] = file.read()
    return tags


_CONTEXT_STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "give",
    "in",
    "into",
    "it",
    "make",
    "of",
    "on",
    "or",
    "song",
    "that",
    "the",
    "this",
    "to",
    "up",
    "use",
    "with",
    "write",
}

_SECTION_FAMILIES = (
    "pre-chorus",
    "post-chorus",
    "verse",
    "chorus",
    "bridge",
    "outro",
    "intro",
    "hook",
    "refrain",
    "interlude",
    "breakdown",
    "break",
    "solo",
    "finale",
    "end",
)
_LIVE_PERFORMANCE_TERMS = (
    "live",
    "crowd",
    "concert",
    "arena",
    "festival",
    "encore",
    "applause",
    "cheering",
    "audience",
    "stadium",
    "on stage",
    "stage banter",
    "mosh",
    "singalong crowd",
)
_LIVE_PERFORMANCE_EXCLUDE_STYLES = (
    "live performance",
    "concert crowd",
    "crowd noise",
    "audience singalong",
    "applause",
    "arena ambience",
    "festival crowd",
    "stadium chant",
    "encore energy",
    "stage banter",
)
_SOLO_NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
}
_SOLO_ORDINAL_WORDS = {
    "first": 1,
    "1st": 1,
    "one": 1,
    "second": 2,
    "2nd": 2,
    "two": 2,
    "third": 3,
    "3rd": 3,
    "three": 3,
}
_STRUCTURE_BASE_ORDER = (
    "Intro",
    "Verse 1",
    "Pre-Chorus",
    "Chorus",
    "Post-Chorus",
    "Verse 2",
    "Chorus 2",
    "Breakdown",
    "Bridge",
    "Instrumental",
    "Solo 1",
    "Solo 2",
    "Chorus 3",
    "Outro",
)


def _tokenize_context_text(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9+#-]+", (text or "").lower())
    return [token for token in tokens if len(token) >= 3 and token not in _CONTEXT_STOPWORDS]


def _build_context_phrases(
    user_input: str,
    default_params: Dict[str, Optional[str]],
    persona_styles: str,
    style: Optional[str] = None,
) -> List[str]:
    phrases = [user_input, persona_styles, style or ""]
    phrases.extend(str(value) for value in default_params.values() if value)
    return [phrase.strip().lower() for phrase in phrases if phrase and phrase.strip()]


def _score_context_line(line: str, keywords: List[str], phrases: List[str]) -> int:
    lowered = line.lower()
    score = 0
    for phrase in phrases:
        if phrase and phrase in lowered:
            score += 8
    for keyword in keywords:
        if keyword in lowered:
            score += 2
    return score


def _select_top_context_lines(
    lines: List[str],
    keywords: List[str],
    phrases: List[str],
    limit: int,
) -> List[str]:
    scored_lines: List[tuple[int, int, str]] = []
    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        score = _score_context_line(line, keywords, phrases)
        if score > 0:
            scored_lines.append((score, index, line))

    scored_lines.sort(key=lambda item: (-item[0], item[1]))
    return [line for _, _, line in scored_lines[:limit]]


def _choose_tempo_tag(tempo: Optional[str]) -> Optional[str]:
    if not tempo:
        return None

    match = re.search(r"\d{2,3}", str(tempo))
    if not match:
        return f"[Tempo: {tempo}]"

    requested = int(match.group(0))
    available_tempos = [70, 75, 80, 85, 90, 95, 100, 110, 120, 128, 130, 140, 150, 160, 180]
    closest = min(available_tempos, key=lambda value: abs(value - requested))
    return f"[Tempo: {closest} BPM]"


def _choose_key_tag(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    normalized = str(key).strip()
    if not normalized:
        return None
    if normalized.startswith("[") and normalized.endswith("]"):
        return normalized
    return f"[Key: {normalized}]"


def _choose_vocal_tag(vocal_gender: Optional[str]) -> Optional[str]:
    if not vocal_gender:
        return None

    lowered = vocal_gender.strip().lower()
    mapping = {
        "male": "[Male Vocal]",
        "female": "[Female Vocal]",
        "duet": "[Male-Female Duet]",
    }
    for key, tag in mapping.items():
        if key == lowered:
            return tag
    if "duet" in lowered:
        return "[Male-Female Duet]"
    if "female" in lowered:
        return "[Female Vocal]"
    if "male" in lowered:
        return "[Male Vocal]"
    return f"[{vocal_gender}]"


def infer_vocal_gender_from_persona(persona_styles: str) -> Optional[str]:
    """Infer the intended vocal gender from persona style text when no explicit setting exists."""
    lowered = (persona_styles or "").lower()
    if not lowered.strip():
        return None

    def has_phrase(phrase: str) -> bool:
        pattern = r"(?<![a-z])" + re.escape(phrase.lower()) + r"(?![a-z])"
        return bool(re.search(pattern, lowered))

    if any(has_phrase(token) for token in ("duet", "male-female duet", "female-male duet")):
        return "Duet"

    female_markers = (
        "female vocal",
        "female vocals",
        "female voice",
        "female lead",
        "female singer",
        "mezzo-soprano",
        "soprano",
        "alto",
    )
    male_markers = (
        "male vocal",
        "male vocals",
        "male voice",
        "male lead",
        "male singer",
        "baritone",
        "tenor",
    )

    has_female = any(has_phrase(marker) for marker in female_markers)
    has_male = any(has_phrase(marker) for marker in male_markers)

    if has_female and not has_male:
        return "Female"
    if has_male and not has_female:
        return "Male"
    return None


def build_compact_style_context(
    styles: Dict[str, str],
    user_input: str,
    default_params: Dict[str, Optional[str]],
    persona_styles: str,
    style: Optional[str] = None,
) -> str:
    """Select a compact style context for the current song request."""
    phrases = _build_context_phrases(user_input, default_params, persona_styles, style)
    keywords = _tokenize_context_text(" ".join(phrases))

    selected_artist_styles = _select_top_context_lines(
        styles.get("artist_styles", "").splitlines(),
        keywords,
        phrases,
        limit=6,
    )
    selected_core_styles = _select_top_context_lines(
        styles.get("core_styles", "").splitlines(),
        keywords,
        phrases,
        limit=10,
    )
    selected_example_styles = _select_top_context_lines(
        styles.get("example_styles", "").splitlines(),
        keywords,
        phrases,
        limit=4,
    )

    if not selected_core_styles:
        selected_core_styles = [
            line.strip()
            for line in styles.get("core_styles", "").splitlines()
            if line.strip()
        ][:8]

    selected_suno_genres: List[str] = []
    try:
        suno_genres = json.loads(styles.get("suno_genres", "{}"))
    except json.JSONDecodeError:
        suno_genres = {}

    for genre_name, description in suno_genres.items():
        line = f"{genre_name}: {description}"
        if _score_context_line(line, keywords, phrases) > 0:
            selected_suno_genres.append(line)
        if len(selected_suno_genres) >= 6:
            break

    context_sections = [
        ("Relevant Artist/Reference Styles", selected_artist_styles),
        ("Relevant Core Style Cues", selected_core_styles),
        ("Relevant Example Styles", selected_example_styles),
        ("Relevant Suno Genres", selected_suno_genres),
    ]

    rendered_sections = []
    for title, lines in context_sections:
        if not lines:
            continue
        rendered_sections.append(f"{title}:\n" + "\n".join(f"- {line}" for line in lines))

    return "\n\n".join(rendered_sections)


def build_compact_tag_context(
    tags: Dict[str, str],
    user_input: str,
    default_params: Dict[str, Optional[str]],
    persona_styles: str,
    style: Optional[str] = None,
    allowed_structure_names: Optional[List[str]] = None,
) -> str:
    """Build a concise, song-specific tag context instead of dumping the full tag catalog."""
    phrases = _build_context_phrases(user_input, default_params, persona_styles, style)
    keywords = _tokenize_context_text(" ".join(phrases))

    available_tag_lines: List[str] = []
    for content in tags.values():
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if line.startswith("[") and line.endswith("]"):
                available_tag_lines.append(line)

    structure_tags = []
    for name in allowed_structure_names or ["Intro", "Verse 1", "Chorus", "Verse 2", "Bridge", "Outro"]:
        tag_name = str(name).strip()
        if not tag_name:
            continue
        structure_tags.append(f"[{tag_name}]")

    relevant_tags = _select_top_context_lines(available_tag_lines, keywords, phrases, limit=8)

    explicit_tags = [
        f"[Genre: {default_params['genre']}]" if default_params.get("genre") else None,
        _choose_tempo_tag(default_params.get("tempo")),
        _choose_key_tag(default_params.get("key")),
        f"[Mood: {default_params['mood']}]" if default_params.get("mood") else None,
        f"[Instruments: {default_params['instruments']}]" if default_params.get("instruments") else None,
        _choose_vocal_tag(default_params.get("vocal_gender")),
    ]

    deduped_relevant_tags = list(
        dict.fromkeys(
            structure_tags + [tag for tag in explicit_tags if tag] + relevant_tags
        )
    )

    return (
        "Recommended structure tags:\n"
        + "\n".join(f"- {tag}" for tag in structure_tags)
        + "\n\nRelevant tag cues:\n"
        + "\n".join(f"- {tag}" for tag in deduped_relevant_tags[len(structure_tags):])
    )

def _normalize_compare_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (text or "").lower())).strip()


def parse_artist_style_catalog(artist_styles_text: str) -> Dict[str, List[str]]:
    """Parse artist style lines into an artist -> style-token map."""
    catalog: Dict[str, List[str]] = {}
    for raw_line in (artist_styles_text or "").splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue

        artist_name, style_blob = line.split(":", 1)
        artist_name = artist_name.strip()
        if not artist_name:
            continue

        style_tokens = [token.strip() for token in style_blob.split(",") if token.strip()]
        if not style_tokens:
            continue

        existing = catalog.get(artist_name, [])
        seen = {_normalize_compare_text(token) for token in existing}
        for token in style_tokens:
            normalized = _normalize_compare_text(token)
            if not normalized or normalized in seen:
                continue
            existing.append(token)
            seen.add(normalized)
        catalog[artist_name] = existing
    return catalog


def extract_artist_style_tokens_from_prompt(user_input: str, styles: Dict[str, str]) -> List[str]:
    """Return style tokens for artists explicitly referenced in the user's prompt."""
    catalog = parse_artist_style_catalog(styles.get("artist_styles", ""))
    normalized_prompt = f" {_normalize_compare_text(user_input or '')} "
    if not normalized_prompt.strip():
        return []

    collected: List[str] = []
    seen = set()
    for artist_name, style_tokens in catalog.items():
        normalized_artist = _normalize_compare_text(artist_name)
        if not normalized_artist:
            continue
        if f" {normalized_artist} " not in normalized_prompt:
            continue
        for token in style_tokens:
            normalized_token = _normalize_compare_text(token)
            if not normalized_token or normalized_token in seen:
                continue
            seen.add(normalized_token)
            collected.append(token)
    return collected


def map_artist_references_to_suno_styles(
    style_tokens: List[str],
    user_input: str,
    styles: Dict[str, str],
) -> List[str]:
    """
    Remove artist-name style tokens and replace them with mapped style tokens from styles.json.
    """
    catalog = parse_artist_style_catalog(styles.get("artist_styles", ""))
    normalized_artists = [
        _normalize_compare_text(artist_name)
        for artist_name in catalog.keys()
        if _normalize_compare_text(artist_name)
    ]
    mapped_tokens = extract_artist_style_tokens_from_prompt(user_input, styles)

    filtered_tokens: List[str] = []
    for token in style_tokens:
        cleaned = str(token).strip()
        if not cleaned:
            continue
        normalized_token = _normalize_compare_text(cleaned)
        if not normalized_token:
            continue

        if any(f" {artist} " in f" {normalized_token} " for artist in normalized_artists):
            continue
        filtered_tokens.append(cleaned)

    merged = mapped_tokens + filtered_tokens
    deduped: List[str] = []
    seen = set()
    for token in merged:
        normalized_token = _normalize_compare_text(token)
        if not normalized_token or normalized_token in seen:
            continue
        seen.add(normalized_token)
        deduped.append(token)
    return deduped


def _normalize_section_name(value: str) -> str:
    lowered = _normalize_compare_text(_strip_tag_wrapper(value))
    return lowered.replace("pre chorus", "pre-chorus").replace("post chorus", "post-chorus")


def _strip_tag_wrapper(tag: str) -> str:
    stripped = (tag or "").strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        return stripped[1:-1].strip()
    return stripped


def _section_family(value: str) -> str:
    normalized = _normalize_section_name(value)
    for family in _SECTION_FAMILIES:
        if normalized.startswith(family):
            return family
    return normalized


def _dedupe_tags(tags: List[str]) -> List[str]:
    deduped: List[str] = []
    seen = set()
    for tag in tags:
        normalized = _normalize_section_name(tag)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(tag if tag.startswith("[") and tag.endswith("]") else f"[{tag}]")
    return deduped


def _is_style_metadata_tag(tag: str) -> bool:
    lowered = _strip_tag_wrapper(tag).strip().lower()
    return any(
        lowered.startswith(token)
        for token in ("style:", "genre:", "tempo:", "key:", "mood:", "instruments:", "dynamic:")
    )


def _style_metadata_category(tag: str) -> str:
    lowered = _strip_tag_wrapper(tag).strip().lower()
    for prefix in ("style:", "genre:", "tempo:", "key:", "mood:", "instruments:", "dynamic:"):
        if lowered.startswith(prefix):
            return prefix[:-1]
    return lowered


def contains_live_performance_terms(text: Optional[str]) -> bool:
    lowered = (text or "").strip().lower()
    return bool(lowered) and any(term in lowered for term in _LIVE_PERFORMANCE_TERMS)


def sanitize_live_performance_text_block(text: str, no_live_performance: bool) -> str:
    """Remove lines that imply a live-performance setting when the option is enabled."""
    if not no_live_performance:
        return text

    kept_lines = []
    for raw_line in (text or "").splitlines():
        if contains_live_performance_terms(raw_line):
            continue
        kept_lines.append(raw_line)
    return "\n".join(kept_lines).strip()


def sanitize_style_token_list(tokens: List[str], no_live_performance: bool) -> List[str]:
    """Filter out live-performance style tokens when the option is enabled."""
    if not no_live_performance:
        return [token for token in tokens if token]
    return [token for token in tokens if token and not contains_live_performance_terms(token)]


def build_live_performance_exclude_styles(existing: List[str], no_live_performance: bool) -> List[str]:
    """Append standard live-performance exclusions for Suno when requested."""
    if not no_live_performance:
        return list(dict.fromkeys(item for item in existing if item))
    merged = list(existing) + list(_LIVE_PERFORMANCE_EXCLUDE_STYLES)
    return list(dict.fromkeys(item for item in merged if item))


def sanitize_brief_for_no_live_performance(
    brief: Dict[str, Any],
    no_live_performance: bool,
) -> Dict[str, Any]:
    """Strip live-performance style cues from the planned brief when requested."""
    if not no_live_performance:
        return brief

    sanitized = dict(brief)
    raw_global_tokens = sanitized.get("suno_style_tokens", [])
    if isinstance(raw_global_tokens, list):
        sanitized["suno_style_tokens"] = sanitize_style_token_list(
            [str(token).strip() for token in raw_global_tokens if str(token).strip()],
            True,
        )

    section_plan = []
    for item in sanitized.get("section_plan", []):
        if not isinstance(item, dict):
            continue
        section_item = dict(item)
        raw_style_tags = section_item.get("style_tags", [])
        if isinstance(raw_style_tags, str):
            raw_style_tags = [raw_style_tags]
        if isinstance(raw_style_tags, list):
            section_item["style_tags"] = [
                str(tag).strip()
                for tag in raw_style_tags
                if str(tag).strip() and not contains_live_performance_terms(str(tag))
            ]
        section_plan.append(section_item)
    sanitized["section_plan"] = section_plan
    return sanitized


def extract_solo_requirements(user_input: str) -> Dict[str, Any]:
    """Extract explicit solo requirements such as count and instrument from the prompt."""
    lowered = (user_input or "").lower()
    requirements = {"count": 0, "instrument": None}
    if "solo" not in lowered:
        return requirements

    window_match = re.search(r"([^\n.]{0,80})\bsolos?\b", lowered)
    prefix = window_match.group(1) if window_match else lowered

    count_candidates = re.findall(r"\b(\d+|one|two|three|four|a|an)\b", prefix)
    raw_count = count_candidates[-1].strip() if count_candidates else ""
    if raw_count.isdigit():
        count = int(raw_count)
    else:
        count = _SOLO_NUMBER_WORDS.get(raw_count, 1)

    instrument_candidates = re.findall(r"\b(guitar|piano|violin|cello|sax(?:ophone)?|drum)\b", prefix)
    raw_instrument = instrument_candidates[-1].strip() if instrument_candidates else ""
    if raw_instrument == "saxophone":
        raw_instrument = "sax"

    requirements["count"] = max(1, count)
    requirements["instrument"] = raw_instrument or None
    return requirements


def _resolve_structure_anchor_name(raw_anchor: str, allowed_names: Optional[List[str]] = None) -> Optional[str]:
    normalized = _normalize_section_name(raw_anchor)
    alias_map = {
        "intro": "Intro",
        "opening": "Intro",
        "verse 1": "Verse 1",
        "first verse": "Verse 1",
        "verse one": "Verse 1",
        "verse 2": "Verse 2",
        "second verse": "Verse 2",
        "verse two": "Verse 2",
        "pre-chorus": "Pre-Chorus",
        "pre chorus": "Pre-Chorus",
        "chorus": "Chorus",
        "post-chorus": "Post-Chorus",
        "post chorus": "Post-Chorus",
        "breakdown": "Breakdown",
        "bridge": "Bridge",
        "instrumental": "Instrumental",
        "interlude": "Instrumental",
        "outro": "Outro",
    }
    resolved = alias_map.get(normalized)
    if not resolved:
        return None
    if allowed_names and resolved not in allowed_names:
        return None
    return resolved


def extract_section_placement_requirements(
    user_input: str,
    allowed_names: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """Extract explicit section placement requirements such as where solos must land."""
    lowered = (user_input or "").lower()
    if "solo" not in lowered:
        return []

    solo_window = lowered[lowered.find("solo"):]
    placements: List[Dict[str, str]] = []
    seen = set()

    ordinal_pattern = re.compile(
        r"\b(first|1st|one|second|2nd|two|third|3rd|three)\b"
        r"(?:[^.\n]{0,40}?)\bafter\s+(?:the\s+)?"
        r"(first verse|verse 1|verse one|second verse|verse 2|verse two|pre-chorus|pre chorus|chorus|bridge|breakdown|instrumental|interlude|intro|outro)\b"
    )
    for match in ordinal_pattern.finditer(solo_window):
        solo_index = _SOLO_ORDINAL_WORDS.get(match.group(1), 0)
        if solo_index <= 0:
            continue
        section_name = f"Solo {solo_index}"
        if allowed_names and section_name not in allowed_names:
            continue
        after_name = _resolve_structure_anchor_name(match.group(2), allowed_names)
        if not after_name:
            continue
        key = (section_name, after_name)
        if key in seen:
            continue
        seen.add(key)
        placements.append({"name": section_name, "after": after_name})

    next_solo_index = 1
    generic_pattern = re.compile(
        r"\b(?:guitar|piano|violin|cello|sax(?:ophone)?|drum)?\s*solo\b"
        r"(?:[^.\n]{0,30}?)\bafter\s+(?:the\s+)?"
        r"(first verse|verse 1|verse one|second verse|verse 2|verse two|pre-chorus|pre chorus|chorus|bridge|breakdown|instrumental|interlude|intro|outro)\b"
    )
    for match in generic_pattern.finditer(lowered):
        while (allowed_names and f"Solo {next_solo_index}" not in allowed_names) and next_solo_index <= 3:
            next_solo_index += 1
        if next_solo_index > 3:
            break
        section_name = f"Solo {next_solo_index}"
        after_name = _resolve_structure_anchor_name(match.group(1), allowed_names)
        if not after_name:
            continue
        key = (section_name, after_name)
        if key in seen:
            continue
        seen.add(key)
        placements.append({"name": section_name, "after": after_name})
        next_solo_index += 1

    return placements


def _default_goal_for_section_name(name: str) -> str:
    normalized = _normalize_section_name(name)
    defaults = {
        "intro": "Set the sonic scene before the first lyric lands.",
        "verse 1": "Set the scene with specific imagery.",
        "pre-chorus": "Build tension into the hook.",
        "chorus": "Deliver the core hook in a memorable, singable way.",
        "chorus 2": "Bring the hook back with more lift and payoff.",
        "post-chorus": "Extend the hook or emotional release without overexplaining it.",
        "verse 2": "Deepen the idea without repeating verse 1 language.",
        "breakdown": "Strip the arrangement back and create contrast before the final lift.",
        "bridge": "Introduce a fresh turn or emotional lift before the ending run.",
        "instrumental": "Let the arrangement carry the emotion without sung lyrics.",
        "solo 1": "Deliver the first instrumental release with clear melodic payoff.",
        "solo 2": "Escalate the instrumental payoff before the ending resolution.",
        "chorus 3": "Deliver the final hook payoff before the resolution.",
        "outro": "Resolve the emotional arc cleanly.",
    }
    return defaults.get(normalized, "Advance the song coherently.")


def get_allowed_structure_names(user_input: str, brief: Optional[Dict[str, Any]] = None) -> List[str]:
    """Return the closed section-name vocabulary offered to the structure planner."""
    lowered = (user_input or "").lower()
    brief_names = {
        _normalize_section_name(str(item.get("name") or ""))
        for item in (brief or {}).get("section_plan", [])
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }

    allowed = ["Verse 1", "Chorus", "Verse 2", "Chorus 2", "Bridge", "Chorus 3", "Outro"]

    if "intro" in lowered or "intro" in brief_names:
        allowed.insert(0, "Intro")
    if "pre-chorus" in lowered or "pre chorus" in lowered or "pre-chorus" in brief_names:
        allowed.insert(2 if "Intro" in allowed else 1, "Pre-Chorus")
    if "post-chorus" in lowered or "post chorus" in lowered or "post-chorus" in brief_names:
        insert_at = allowed.index("Chorus") + 1 if "Chorus" in allowed else len(allowed)
        allowed.insert(insert_at, "Post-Chorus")
    if "breakdown" in lowered or "drop out" in lowered or "dropout" in lowered or "breakdown" in brief_names:
        allowed.insert(-2 if len(allowed) >= 2 else len(allowed), "Breakdown")
    if "instrumental" in lowered or "interlude" in lowered or "instrumental" in brief_names:
        allowed.insert(-1 if allowed else 0, "Instrumental")

    solo_requirements = extract_solo_requirements(user_input)
    requested_solos = min(max(int(solo_requirements.get("count", 0)), 0), 2)
    brief_solos = sum(1 for name in brief_names if name.startswith("solo"))
    for index in range(max(requested_solos, brief_solos)):
        allowed.insert(-1 if allowed else len(allowed), f"Solo {index + 1}")

    return list(dict.fromkeys(name for name in allowed if name in _STRUCTURE_BASE_ORDER))


_STRUCTURE_GUIDANCE_PATTERNS = (
    {
        "name": "Core verse-chorus arc",
        "shape": ["Verse 1", "Chorus", "Verse 2", "Chorus 2", "Bridge", "Chorus 3", "Outro"],
        "when": "Use when the hook and lyric narrative matter more than formal experimentation.",
        "signals": ("pop", "rock", "folk", "country", "indie", "hook", "anthem", "catchy"),
    },
    {
        "name": "Lifted pre-chorus build",
        "shape": ["Intro", "Verse 1", "Pre-Chorus", "Chorus", "Verse 2", "Chorus 2", "Bridge", "Chorus 3", "Outro"],
        "when": "Use when the song wants a clear tension-to-release rise into a big chorus.",
        "signals": ("anthemic", "cinematic", "uplifting", "dramatic", "build", "lift", "soaring"),
    },
    {
        "name": "Brooding breakdown arc",
        "shape": ["Verse 1", "Chorus", "Verse 2", "Chorus 2", "Breakdown", "Bridge", "Chorus 3", "Outro"],
        "when": "Use when the theme is heavy, tense, dark, or emotionally collapsing before a final turn.",
        "signals": ("dark", "tense", "brooding", "grief", "breakup", "haunted", "melancholy"),
    },
    {
        "name": "Instrument feature arc",
        "shape": ["Verse 1", "Solo 1", "Chorus", "Verse 2", "Chorus 2", "Bridge", "Solo 2", "Chorus 3", "Outro"],
        "when": "Use when the prompt explicitly asks for solos, instrumental spotlights, or guitar-driven release moments.",
        "signals": ("solo", "guitar", "violin", "cello", "instrumental", "shred", "lead break"),
    },
)

_SHORT_FORM_STRUCTURE_TERMS = (
    "short form",
    "short-form",
    "minimal",
    "ambient",
    "instrumental",
    "spoken word",
    "through-composed",
    "through composed",
    "drone",
    "chant",
)

_SPARSE_STRUCTURE_TERMS = (
    "folk",
    "singer-songwriter",
    "singer songwriter",
    "ballad",
    "acoustic",
    "intimate",
    "story song",
    "narrative",
    "hymn",
)

_HOOK_FORWARD_STRUCTURE_TERMS = (
    "pop",
    "rock",
    "country",
    "anthem",
    "anthemic",
    "catchy",
    "hook",
    "radio",
    "uplifting",
    "driving",
    "big chorus",
)


def infer_chorus_return_count(user_input: str, brief: Optional[Dict[str, Any]] = None) -> int:
    """Infer how many chorus appearances fit the song style and request."""
    brief = brief or {}
    source_parts = [
        user_input or "",
        str(brief.get("theme") or ""),
        str(brief.get("hook_strategy") or ""),
        " ".join(str(token) for token in brief.get("suno_style_tokens", []) if token),
    ]
    lowered = " ".join(source_parts).lower()

    if any(term in lowered for term in _SHORT_FORM_STRUCTURE_TERMS):
        return 1
    if any(term in lowered for term in _SPARSE_STRUCTURE_TERMS):
        return 2
    if any(term in lowered for term in _HOOK_FORWARD_STRUCTURE_TERMS):
        return 3
    return 2


def build_structure_guidance(
    user_input: str,
    brief: Optional[Dict[str, Any]],
    default_params: Dict[str, Optional[str]],
    allowed_names: List[str],
) -> str:
    """Build compact planning guidance for the structure-selection LLM step."""
    brief = brief or {}
    source_parts = [
        user_input or "",
        str(brief.get("theme") or ""),
        str(brief.get("emotional_arc") or ""),
        str(brief.get("hook_strategy") or ""),
        " ".join(str(token) for token in brief.get("suno_style_tokens", []) if token),
        " ".join(str(value) for value in default_params.values() if value),
    ]
    lowered = " ".join(source_parts).lower()

    scored_patterns: List[tuple[int, Dict[str, Any]]] = []
    for pattern in _STRUCTURE_GUIDANCE_PATTERNS:
        score = sum(1 for signal in pattern["signals"] if signal in lowered)
        if any(name.startswith("Solo ") for name in allowed_names) and "Solo 1" in pattern["shape"]:
            score += 2
        if "Pre-Chorus" in allowed_names and "Pre-Chorus" in pattern["shape"]:
            score += 1
        if "Breakdown" in allowed_names and "Breakdown" in pattern["shape"]:
            score += 1
        scored_patterns.append((score, pattern))

    scored_patterns.sort(key=lambda item: (-item[0], item[1]["name"]))
    selected_patterns = [pattern for _, pattern in scored_patterns[:3]]

    requested_moments = []
    chorus_return_count = infer_chorus_return_count(user_input, brief)
    if any(name.startswith("Solo ") for name in allowed_names):
        solo_requirements = extract_solo_requirements(user_input)
        instrument = str(solo_requirements.get("instrument") or "lead").strip()
        requested_moments.append(f"- The prompt requests {solo_requirements['count']} {instrument} solo section(s).")
    requested_moments.append(
        f"- Based on the style and prompt, plan for about {chorus_return_count} chorus appearance(s) unless the user explicitly asks for a different form."
    )
    placement_requirements = extract_section_placement_requirements(user_input, allowed_names)
    for placement in placement_requirements:
        requested_moments.append(f"- Keep {placement['name']} immediately after {placement['after']}.")

    if not requested_moments:
        requested_moments.append("- No special section-placement requirement was explicitly detected.")

    rendered_patterns = []
    for pattern in selected_patterns:
        filtered_shape = [name for name in pattern["shape"] if name in allowed_names]
        rendered_patterns.append(
            f"- {pattern['name']}: {' > '.join(filtered_shape)}. {pattern['when']}"
        )

    return "\n".join(
        [
            "Recommended structure archetypes:",
            *rendered_patterns,
            "",
            "Common section placement guidance:",
            "- Intro usually opens the song.",
            "- Verse 1 should lead into the first Chorus.",
            "- Pre-Chorus usually sits between a Verse and Chorus.",
            "- Post-Chorus usually follows a Chorus directly.",
            "- Verse 2 usually follows the first Chorus or Post-Chorus.",
            "- Bridge or Breakdown usually appears after Verse 2 and before the final lift.",
            "- Solo or Instrumental feature sections usually land after a Verse, after the Bridge, or just before the ending resolution.",
            "- Outro should be the final section.",
            "",
            "Prompt-specific structure constraints:",
            *requested_moments,
            "",
            "Allowed section names for this song:",
            f"- {', '.join(allowed_names)}",
        ]
    ).strip()


def read_persona(persona_name: str) -> str:
    persona_file = resolve_persona_file(persona_name)
    if not persona_file:
        return ""

    with open(persona_file, "r") as file:
        content = file.read()
    if "Persona styles" not in content:
        return ""

    start = content.find("Persona styles") + len("Persona styles")
    end = content.find("\n\n", start)
    return content[start:end].strip()


def read_persona_visual_styles(persona_name: str) -> str:
    """Extract visual styles from the persona markdown file."""
    persona_file = resolve_persona_file(persona_name)
    if not persona_file:
        return ""

    with open(persona_file, "r") as file:
        content = file.read()
    if "Visual styles" not in content:
        return ""

    start = content.find("Visual styles") + len("Visual styles")
    # Check for another section or end of file
    end = content.find("\n##", start)
    if end == -1:
        end = len(content)
    return content[start:end].strip()


def resolve_persona_file(persona_input: str) -> Optional[str]:
    """
    Resolve a persona input to an existing markdown file.
    Supports:
    - direct paths (absolute or relative, with optional ~ expansion)
    - persona slugs/names that map to personas/<name>.md
    """
    if not persona_input:
        return None

    expanded = os.path.expanduser(persona_input)
    # Direct file path support (absolute or relative)
    if os.path.isfile(expanded):
        return expanded
    # If it looks like a path but doesn't exist, don't try to slugify
    if os.path.isabs(expanded) or os.sep in persona_input:
        return None
    # Fallback to personas directory by slugifying name
    persona_file = Path(get_repo_root()) / "personas" / f"{persona_input.lower().replace(' ', '_')}.md"
    if persona_file.is_file():
        return str(persona_file)
    return None


def load_prompt_from_file(prompt_path: str) -> str:
    expanded = os.path.expanduser(prompt_path)
    if not os.path.isfile(expanded):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(expanded, "r") as file:
        return file.read().strip()


def read_prompt(prompt_name: str) -> str:
    prompt_file = Path(get_repo_root()) / "prompts" / f"{prompt_name}.txt"
    if not prompt_file.exists():
        return ""
    with prompt_file.open("r") as file:
        return file.read()


def get_default_song_params() -> Dict[str, Optional[str]]:
    return {
        "genre": os.getenv("DEFAULT_SONG_GENRE", "rock"),
        "persona": os.getenv("DEFAULT_PERSONA"),
        "tempo": os.getenv("DEFAULT_TEMPO", "120"),
        "key": os.getenv("DEFAULT_KEY", "C"),
        "instruments": os.getenv("DEFAULT_INSTRUMENTS", "guitar,bass,drums"),
        "mood": os.getenv("DEFAULT_MOOD", "happy"),
        "vocal_gender": os.getenv("DEFAULT_VOCAL_GENDER"),
        "rhyme_scheme": os.getenv("DEFAULT_RHYME_SCHEME"),
    }


def coalesce_song_setting(*values: Optional[str], fallback: str = "Auto") -> str:
    """Return the first non-empty song setting, otherwise a display fallback."""
    for value in values:
        if value:
            return value
    return fallback


def parse_persona(user_input: str, cli_persona: Optional[str]) -> Optional[str]:
    """Extract persona name from user input or CLI argument."""
    if cli_persona:
        return cli_persona
    lowered = user_input.lower()
    if "persona:" not in lowered:
        return None
    start = lowered.find("persona:") + len("persona:")
    end = user_input.find(" ", start)
    return user_input[start:].strip() if end == -1 else user_input[start:end].strip()


def enhance_user_input(
    user_input: str,
    song_name: Optional[str],
    style: Optional[str] = None,
    vocal_gender: Optional[str] = None,
    rhyme_scheme: Optional[str] = None,
) -> str:
    """Enhance the user's initial request by adding explicit song title, style, or vocal guidance."""
    parts = []
    
    if song_name:
        parts.append(f"Song Title: {song_name}")

    if vocal_gender:
        parts.append(f"Requested Vocal Gender: {vocal_gender}")
    
    if rhyme_scheme and rhyme_scheme != "Auto":
        parts.append(f"Rhyme Scheme: {rhyme_scheme}")
    
    parts.append(user_input)
    
    if style:
        parts.append(f"The song's main style will be {style}")
    
    return "\n".join(parts)



def remove_thinking_tags(text: str) -> str:
    """Remove thinking tokens enclosed in <think></think> or <thought></thought> tags (including tags themselves)."""
    import re
    # Match <think>...</think> or <thought>...</thought>
    # Case insensitive, handle optional spaces like <think >, handle unclosed tags at the end.
    patterns = [
        r'<(think|thought)[^>]*>.*?</\1>', # Closed tags
        r'<(think|thought)[^>]*>.*$',       # Unclosed tags at end of string
    ]
    result = text
    for pattern in patterns:
        result = re.sub(pattern, '', result, flags=re.DOTALL | re.IGNORECASE)
    return result.strip()


def extract_title(lyrics: str, provided_title: Optional[str]) -> str:
    if provided_title:
        return provided_title
    
    # Clean thinking tags before extracting title
    lyrics = remove_thinking_tags(lyrics)
    
    # Check for various title formats
    title_markers = ["Title:", "Song Title:", "## Song Title"]
    lines = lyrics.splitlines()
    for i, line in enumerate(lines):
        trimmed = line.strip()
        for marker in title_markers:
            if trimmed.startswith(marker):
                # Check if title is on the same line
                title = trimmed[len(marker):].strip()
                if title:
                    return title
                # Check if title is on the next line
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line:
                        return next_line
                
    # Fallback to first non-empty line if it doesn't look like a tag or a marker
    for line in lines:
        trimmed = line.strip()
        if trimmed and not (trimmed.startswith("[") and trimmed.endswith("]")):
            # Also ignore the markers themselves if they appear as standalone lines
            if any(trimmed.startswith(marker) for marker in title_markers) and not any(trimmed == marker for marker in title_markers):
                # This case is handled above, but just in case
                pass
            elif not any(trimmed == marker for marker in title_markers):
                return trimmed[:50]
            
    return "Unknown Song"


def remove_title_from_lyrics(lyrics: str) -> str:
    """Strip the title block from the beginning of the LLM output and remove thinking tokens."""
    lyrics = remove_thinking_tags(lyrics)
    lines = lyrics.splitlines()
    if not lines:
        return lyrics
        
    title_markers = ["Title:", "Song Title:", "## Song Title"]
    new_lines = []
    skip_next = False
    found_title = False
    
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
            
        trimmed = line.strip()
        if not found_title and trimmed:
            marker_found = None
            for marker in title_markers:
                if trimmed.startswith(marker):
                    marker_found = marker
                    break
            
            if marker_found:
                found_title = True
                # If marker is the whole line, skip the next line too (if it exists)
                if trimmed == marker_found and i + 1 < len(lines):
                    skip_next = True
                continue
        
        new_lines.append(line)
        
    # Remove leading empty lines
    while new_lines and not new_lines[0].strip():
        new_lines.pop(0)
        
    return normalize_lyrics_section_tags("\n".join(new_lines).strip())


def normalize_lyrics_section_tags(lyrics: str) -> str:
    """Normalize generated structural tags to the tag vocabulary expected by downstream consumers."""
    normalized = lyrics or ""
    normalized = re.sub(r"\[(solo)\s+\d+\]", r"[\1]", normalized, flags=re.IGNORECASE)
    return normalized


def get_repo_root() -> str:
    """Return the absolute path to the repository root."""
    return str(Path(__file__).resolve().parents[2])


def resolve_storage_path(relative_path: str) -> str:
    """Resolve a repo-relative storage path to an absolute filesystem path."""
    return str((Path(get_repo_root()) / relative_path).resolve())


def relativize_storage_path(path: str) -> str:
    """Convert an absolute path to a repo-relative storage path when possible."""
    root = Path(get_repo_root()).resolve()
    try:
        return str(Path(path).resolve().relative_to(root))
    except ValueError:
        return path


def get_song_storage_info(title: str, date: Optional[str] = None) -> Dict[str, str]:
    """
    Generate consistent folder and filenames for a song.
    
    Returns a dict with:
    - folder: 'songs/YYYY-MM-DD - Song Title'
    - md: 'songs/YYYY-MM-DD - Song Title/YYYY-MM-DD - Song Title.md'
    - image_base: 'songs/YYYY-MM-DD - Song Title/YYYY-MM-DD - Song Title' (without extension)
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Sanitize title slightly for filesystem safety while keeping it human readable
    # Remove characters that are definitely problematic across OSs
    forbidden_chars = '<>:"/\\|?*'
    safe_title = "".join(c for c in title if c not in forbidden_chars).strip()
    
    folder_name = f"{date} - {safe_title}"
    folder_path = os.path.join("songs", folder_name)
    
    # For file names, we also use the same safe title
    base_name = f"{date} - {safe_title}"
    md_path = os.path.join(folder_path, f"{base_name}.md")
    image_base_path = os.path.join(folder_path, base_name)
    
    repo_root = get_repo_root()
    abs_folder = os.path.abspath(os.path.join(repo_root, folder_path))
    abs_md = os.path.abspath(os.path.join(repo_root, md_path))
    abs_image_base = os.path.abspath(os.path.join(repo_root, image_base_path))

    return {
        "folder": folder_path,
        "md": md_path,
        "image_base": image_base_path,
        "abs_folder": abs_folder,
        "abs_md": abs_md,
        "abs_image_base": abs_image_base,
    }


def get_album_storage_info(album_name: str, album_id: Optional[int], date: Optional[str] = None) -> Dict[str, str]:
    """Generate consistent folder and filenames for album artwork assets."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    forbidden_chars = '<>:"/\\|?*'
    safe_name = "".join(char for char in album_name if char not in forbidden_chars).strip() or "Album"
    album_segment = f"album-{album_id}" if album_id is not None else "album"
    folder_name = f"{album_segment} - {safe_name}"
    folder_path = os.path.join("songs", "albums", folder_name)
    image_base_path = os.path.join(folder_path, f"{date} - {safe_name}")

    repo_root = get_repo_root()
    abs_folder = os.path.abspath(os.path.join(repo_root, folder_path))
    abs_image_base = os.path.abspath(os.path.join(repo_root, image_base_path))

    return {
        "folder": folder_path,
        "image_base": image_base_path,
        "abs_folder": abs_folder,
        "abs_image_base": abs_image_base,
    }


def _resolve_generated_art_path(abs_output_base: str, filename_suffix: str = "") -> Optional[str]:
    base_path = f"{abs_output_base}{filename_suffix}"
    for ext in [".png", ".jpg", ".webp"]:
        check_path = f"{base_path}{ext}"
        if os.path.exists(check_path):
            print(f"[DEBUG] Found actual file: {check_path}")
            return relativize_storage_path(check_path)
    return None


def generate_artwork_from_prompt(prompt: str, abs_output_base: str, filename_suffix: str = "") -> Optional[str]:
    """Generate artwork from a prepared prompt and return the repo-relative path."""
    output_file = f"{abs_output_base}{filename_suffix}.jpg"
    print(f"[DEBUG] output_file (initial): {output_file}")

    try:
        generate_album_art_image(prompt, output_file)
        actual_file = _resolve_generated_art_path(abs_output_base, filename_suffix)
        if actual_file:
            return actual_file
        print(f"[DEBUG] Image generation completed, checking file exists: {os.path.exists(output_file)}")
        return relativize_storage_path(output_file) if os.path.exists(output_file) else None
    except Exception as e:
        print(f"Warning: Failed to generate album art: {e}")
        return None


def rename_song_files(old_title: str, new_title: str, date: str) -> Dict[str, str]:
    """
    Rename the song folder and files when the title changes.
    Returns the new storage info.
    """
    old_info = get_song_storage_info(old_title, date)
    new_info = get_song_storage_info(new_title, date)

    old_folder = old_info["abs_folder"]
    new_folder = new_info["abs_folder"]

    if os.path.exists(old_folder) and old_folder != new_folder:
        # 1. Rename files inside first
        old_base = os.path.basename(old_info["image_base"])
        new_base = os.path.basename(new_info["image_base"])

        for filename in os.listdir(old_folder):
            if filename.startswith(old_base):
                # Ensure we only rename files that belong to this song (exact base or base+suffix)
                suffix = filename[len(old_base):]
                if suffix and not (suffix.startswith(".") or suffix.startswith("_") or suffix.startswith("-")):
                    continue

                old_file_path = os.path.join(old_folder, filename)
                new_file_name = filename.replace(old_base, new_base, 1)
                new_file_path = os.path.join(old_folder, new_file_name)

                # Update title in markdown if it's the .md file
                if filename.endswith(".md"):
                    try:
                        with open(old_file_path, "r") as f:
                            content = f.read()

                        # Update title in markdown - usually ## Title
                        old_md_title = f"## {old_title}"
                        new_md_title = f"## {new_title}"
                        if old_md_title in content:
                            content = content.replace(old_md_title, new_md_title)

                        with open(old_file_path, "w") as f:
                            f.write(content)
                    except Exception as e:
                        print(f"Error updating markdown title: {e}")

                try:
                    os.rename(old_file_path, new_file_path)
                except Exception as e:
                    print(f"Error renaming file {old_file_path} to {new_file_name}: {e}")

        # 2. Rename the folder
        try:
            os.rename(old_folder, new_folder)
        except Exception as e:
            print(f"Error renaming folder {old_folder} to {new_folder}: {e}")

    return new_info


def generate_album_art(
    title: str,
    user_input: str,
    persona_name: Optional[str] = None,
    style: Optional[str] = None,
    mood: Optional[str] = None,
    vocal_gender: Optional[str] = None,
    date: Optional[str] = None,
    filename_suffix: str = "",
) -> Optional[str]:
    """Generate album artwork using integrated function with enriched prompt."""
    import os
    
    # DEBUG: Log working directory
    print(f"[DEBUG] generate_album_art cwd: {os.getcwd()}")
    print(f"[DEBUG] generate_album_art title: {title}")
    
    # Base prompt elements
    prompt_parts = [f"Album cover for song '{title}'"]
    
    # Add user theme/prompt
    prompt_parts.append(f"with theme '{user_input}'")
    
    # Add persona visual styles if available
    if persona_name:
        visual_styles = read_persona_visual_styles(persona_name)
        if visual_styles:
            prompt_parts.append(f"in styles: {visual_styles}")
            
    # Add song metadata for more context
    metadata_context = []
    if style:
        metadata_context.append(f"style: {style}")
    if mood:
        metadata_context.append(f"mood: {mood}")
    if vocal_gender:
        metadata_context.append(f"vocal gender: {vocal_gender}")
        
    if metadata_context:
        prompt_parts.append(f"({', '.join(metadata_context)})")
        
    # Final assembly
    artwork_prompt = " ".join(prompt_parts)
    
    # Debug print to verify prompt consistency
    print(f"--- Art Prompt: {artwork_prompt}")
    
    # Use storage info helper for consistent paths
    storage = get_song_storage_info(title, date)
    os.makedirs(storage["abs_folder"], exist_ok=True)

    return generate_artwork_from_prompt(
        artwork_prompt,
        storage["abs_image_base"],
        filename_suffix=filename_suffix,
    )


def extract_song_details_for_art(song_path: str) -> tuple[str, str]:
    expanded = os.path.expanduser(song_path)
    if not os.path.isfile(expanded):
        raise FileNotFoundError(f"Song file not found: {song_path}")

    with open(expanded, "r") as file:
        content = file.read()

    title = None
    for line in content.splitlines():
        if line.startswith("## "):
            title = line[3:].strip()
            break
    if not title:
        raise ValueError(f"Could not extract song title from {song_path}")

    user_prompt = ""
    marker = "- **User Prompt**:"
    if marker in content:
        start = content.index(marker) + len(marker)
        # Stop at the lyrics header or next heading; collapse whitespace for a clean prompt
        end = content.find("### Song Lyrics", start)
        if end == -1:
            end = content.find("\n##", start)
        if end == -1:
            end = len(content)
        user_prompt = " ".join(content[start:end].strip().split())

    return title, user_prompt


def parse_persona_styles_list(persona_styles: str):
    if not persona_styles:
        return []
    # Split on commas or newlines; keep concise tokens
    raw_tokens = []
    for line in persona_styles.splitlines():
        raw_tokens.extend([part.strip() for part in line.split(",")])
    return [token for token in raw_tokens if token]


def strip_style_tags(lyrics: str) -> str:
    """Remove style tags while preserving song structure headers like [Verse 1], [Chorus], etc."""
    import re

    lyrics = normalize_lyrics_section_tags(lyrics)
    
    # Split into lines and process each line
    lines = lyrics.split('\n')
    clean_lines = []
    
    # Define structural headers to preserve (extract just the header part)
    structural_patterns = [
        r'\[Verse\s*\d*\]',
        r'\[Pre-Chorus\]',
        r'\[Chorus(?:\s*\d+)?\]',
        r'\[Bridge\]',
        r'\[Outro\]',
        r'\[Intro\]',
        r'\[Solo\]',
        r'\[Guitar Solo\]',
        r'\[[^\]\n]+\s+Solo\]',
        r'\[Instrumental\]'
    ]
    
    for line in lines:
        stripped_line = line.strip()

        if re.match(r'^\*(?:[^*\n]|\*\*)+\*$', stripped_line):
            continue

        stripped_line = re.sub(r'^\*(?:[^*\n]|\*\*)+\*\s*', '', stripped_line)
        
        # Check if this line contains a structural header
        structural_header = None
        for pattern in structural_patterns:
            match = re.search(pattern, stripped_line, re.IGNORECASE)
            if match:
                structural_header = match.group(0)
                break
        
        if structural_header:
            # Add just the clean structural header
            clean_lines.append(structural_header)
            continue
        
        # Remove lines that are purely style tags (in brackets)
        if re.match(r'^\[.*\]$', stripped_line):
            continue
        
        # Remove inline style tags but keep the content
        # This handles cases like "[Female Vocal] Feel the rush..." -> "Feel the rush..."
        line = re.sub(r'^\[.*?\]\s*', '', stripped_line)
        
        # Only add non-empty lines
        if line.strip():
            clean_lines.append(line)
    
    # Add spacing between sections for better readability
    result_lines = []
    for i, line in enumerate(clean_lines):
        result_lines.append(line)
        # Add empty line after structural headers
        if i < len(clean_lines) - 1:
            for pattern in structural_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    # Check if next line is not already empty
                    if clean_lines[i + 1].strip():
                        result_lines.append('')
                    break
    
    return '\n'.join(result_lines)


def save_song(title: str, user_input: str, lyrics: str, default_params: Dict[str, Optional[str]], metadata: Dict[str, object], album_art_path: Optional[str] = None) -> str:
    """Save the generated song to a markdown file with metadata."""
    description = metadata.get("description", "Short description of the song's theme and style.")
    suno_styles = metadata.get("suno_styles")
    suno_exclude_styles = metadata.get("suno_exclude_styles", [])
    if isinstance(suno_styles, list):
        styles_line = ", ".join(str(style) for style in suno_styles if style) or "Auto"
    elif suno_styles:
        styles_line = str(suno_styles)
    else:
        styles_line = coalesce_song_setting(default_params.get("genre"))
    exclude_line = ", ".join(suno_exclude_styles) if isinstance(suno_exclude_styles, list) else str(suno_exclude_styles)
    target_audience = metadata.get("target_audience", "Suggested demographic")
    commercial_potential = metadata.get("commercial_potential", "Assessment")
    mood_value = coalesce_song_setting(metadata.get("mood"), default_params.get("mood"))
    tempo_value = coalesce_song_setting(metadata.get("tempo"), default_params.get("tempo"))
    key_value = coalesce_song_setting(metadata.get("key"), default_params.get("key"))
    instruments_value = coalesce_song_setting(metadata.get("instruments"), default_params.get("instruments"))

    # Generate clean lyrics without style tags
    clean_lyrics = strip_style_tags(lyrics)
    
    # Prepare album art markdown if path is provided
    album_art_md = ""
    if album_art_path:
        # Use relative path for the markdown link if it's in the same folder
        art_filename = os.path.basename(album_art_path)
        album_art_md = f"![Album Art]({art_filename})\n\n"

    final_md = f"""
## {title}
### {description}

{album_art_md}## Suno Styles
{styles_line}

## Suno Exclude-styles
{exclude_line if exclude_line else "None"}

## Additional Metadata
- **Emotional Arc**: {mood_value}
- **Target Audience**: {target_audience}
- **Commercial Potential**: {commercial_potential}
- **Technical Notes**: BPM: {tempo_value}, Key: {key_value}, Instruments: {instruments_value}
- **User Prompt**: {user_input}

### Song Lyrics:
{lyrics}

### Clean Lyrics (No Style Tags):
{clean_lyrics}
"""
    storage = get_song_storage_info(title)
    os.makedirs(storage["abs_folder"], exist_ok=True)
    filename = storage["abs_md"]
    with open(filename, "w") as file:
        file.write(final_md)
    return storage["md"]


@dataclass
class SongResources:
    styles: Dict[str, str]
    tags: Dict[str, str]
    persona_styles: str
    default_params: Dict[str, Optional[str]]


def get_instrument_tags() -> List[str]:
    """Parse tags/default-tags.txt to extract unique instrument tags."""
    path = Path(get_repo_root()) / "tags" / "default-tags.txt"
    if not path.exists():
        return []

    instruments = set()
    with path.open("r") as f:
        for line in f:
            line = line.strip()
            # Handle [Instruments: ...]
            if line.startswith("[Instruments:"):
                content = line[len("[Instruments:"):].strip("[]")
                # Split by comma and clean up each instrument
                parts = [p.strip() for p in content.split(",")]
                for part in parts:
                    if part:
                        # Some parts might have additional context like "filtered synth pads"
                        # We might want to keep them as is or split more. 
                        # The user wants "selection of tags", so keeping the common ones.
                        instruments.add(part)
            # Handle solo tags like [Guitar Solo]
            elif line.startswith("[") and line.endswith("]") and "Solo" in line:
                solo_instrument = line[1:-1].replace("Solo", "").strip()
                if solo_instrument:
                    instruments.add(solo_instrument)

    # Filter out empty or too long strings
    valid_instruments = [i for i in instruments if 0 < len(i) < 40]
    return sorted(list(set(valid_instruments)))


class SongState(TypedDict, total=False):
    user_input: str
    prompt_user_input: str
    song_name: Optional[str]
    persona: Optional[str]
    persona_name: Optional[str]
    style: Optional[str]
    use_local: bool
    resources: SongResources
    brief: Dict[str, Any]
    structure_plan: List[Dict[str, Any]]
    structure_guidance: str
    lyrics: str
    feedback: str
    score: float
    round: int
    max_rounds: int
    suno_review_issues: List[Dict[str, Any]]
    quality_review_issues: List[Dict[str, Any]]
    review_issues: List[Dict[str, Any]]
    needs_revision: bool
    metadata: Dict[str, Any]
    filename: Optional[str]
    album_art: Optional[str]
    style_context: str
    tag_context: str
    generate_album_art: bool
    genre: Optional[str]
    tempo: Optional[str]
    key: Optional[str]
    instruments: Optional[str]
    mood: Optional[str]
    vocal_gender: Optional[str]
    no_live_performance: bool


def load_resources(persona_name: Optional[str]) -> SongResources:
    styles = read_styles()
    tags = read_tags()
    persona_styles = read_persona(persona_name) if persona_name else ""
    default_params = get_default_song_params()
    persona_vocal_gender = infer_vocal_gender_from_persona(persona_styles)
    if persona_vocal_gender and not default_params.get("vocal_gender"):
        default_params["vocal_gender"] = persona_vocal_gender
    return SongResources(styles=styles, tags=tags, persona_styles=persona_styles, default_params=default_params)


def progress_steps(use_local: bool):
    """Return progress steps for song generation based on mode."""
    if use_local:
        return [
            "Parsing user input and persona",
            "Loading resources (styles, tags, personas, defaults)",
            "Planning song structure",
            "Generating initial song draft (local LLM)",
            "Running prompt-only review pass",
            "Applying targeted lyric fixes (if needed)",
            "Generating metadata summary",
            "Skipping album artwork (local mode)",
            "Formatting and saving final song",
        ]
    return [
        "Parsing user input and persona",
        "Loading resources (styles, tags, personas, defaults)",
        "Planning song structure",
        "Generating initial song draft",
        "Running prompt-only review pass",
        "Applying targeted lyric fixes (if needed)",
        "Generating metadata summary",
        "Generating album artwork",
        "Formatting and saving final song",
    ]
