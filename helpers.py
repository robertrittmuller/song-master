import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from tools.create_album_art import generate_album_art_image


def read_styles() -> Dict[str, str]:
    """Load and process style configurations from JSON file."""
    consolidated_path = os.path.join("styles", "styles.json")
    if not os.path.exists(consolidated_path):
        raise FileNotFoundError(f"Missing consolidated styles file at {consolidated_path}")

    with open(consolidated_path, "r") as file:
        raw_styles = json.load(file)

    styles: Dict[str, str] = {}
    for key in ("artist_styles", "core_styles", "example_styles"):
        entries = raw_styles.get(key, [])
        styles[key] = "\n".join(entries) if isinstance(entries, list) else str(entries)

    styles["suno_genres"] = json.dumps(raw_styles.get("suno_genres", {}), separators=(",", ":"))
    return styles


def read_tags() -> Dict[str, str]:
    tags: Dict[str, str] = {}
    for filename in os.listdir("tags"):
        if filename.endswith(".txt"):
            with open(f"tags/{filename}", "r") as file:
                tags[filename] = file.read()
    return tags


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
    persona_file = f"personas/{persona_input.lower().replace(' ', '_')}.md"
    if os.path.isfile(persona_file):
        return persona_file
    return None


def load_prompt_from_file(prompt_path: str) -> str:
    expanded = os.path.expanduser(prompt_path)
    if not os.path.isfile(expanded):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(expanded, "r") as file:
        return file.read().strip()


def read_prompt(prompt_name: str) -> str:
    prompt_file = f"prompts/{prompt_name}.txt"
    if not os.path.exists(prompt_file):
        return ""
    with open(prompt_file, "r") as file:
        return file.read()


def get_default_song_params() -> Dict[str, Optional[str]]:
    return {
        "genre": os.getenv("DEFAULT_SONG_GENRE", "rock"),
        "persona": os.getenv("DEFAULT_PERSONA"),
        "tempo": os.getenv("DEFAULT_TEMPO", "120"),
        "key": os.getenv("DEFAULT_KEY", "C"),
        "instruments": os.getenv("DEFAULT_INSTRUMENTS", "guitar,bass,drums"),
        "mood": os.getenv("DEFAULT_MOOD", "happy"),
    }


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


def enhance_user_input(user_input: str, song_name: Optional[str]) -> str:
    if not song_name:
        return user_input
    return f"Song Title: {song_name}\n\n{user_input}"


def extract_title(lyrics: str, provided_title: Optional[str]) -> str:
    if provided_title:
        return provided_title
    if "## Song Title" in lyrics:
        start = lyrics.find("## Song Title") + len("## Song Title")
        end = lyrics.find("\n", start)
        return lyrics[start:end].strip()
    return "Unknown Song"


def generate_album_art(title: str, user_input: str) -> str:
    """Generate album artwork using integrated function."""
    artwork_prompt = (
        f"Album cover for song '{title}' with theme {user_input}. "
        "Do not include any text, lettering, or typography on the image."
    )
    output_file = f"songs/{title.replace(' ', '_')}_cover.jpg"
    os.makedirs("songs", exist_ok=True)
    try:
        generate_album_art_image(artwork_prompt, output_file)
    except Exception as e:
        print(f"Warning: Failed to generate album art: {e}")
        return None
    return output_file


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


def save_song(title: str, user_input: str, lyrics: str, default_params: Dict[str, Optional[str]], metadata: Dict[str, object]) -> str:
    """Save the generated song to a markdown file with metadata."""
    description = metadata.get("description", "Short description of the song's theme and style.")
    suno_styles = metadata.get("suno_styles", [default_params.get("genre", "rock")])
    suno_exclude_styles = metadata.get("suno_exclude_styles", [])
    styles_line = ", ".join(suno_styles) if isinstance(suno_styles, list) else str(suno_styles)
    exclude_line = ", ".join(suno_exclude_styles) if isinstance(suno_exclude_styles, list) else str(suno_exclude_styles)
    target_audience = metadata.get("target_audience", "Suggested demographic")
    commercial_potential = metadata.get("commercial_potential", "Assessment")

    final_md = f"""
## {title}
### {description}

## Suno Styles
{styles_line}

## Suno Exclude-styles
{exclude_line if exclude_line else "None"}

## Additional Metadata
- **Emotional Arc**: {default_params['mood']}
- **Target Audience**: {target_audience}
- **Commercial Potential**: {commercial_potential}
- **Technical Notes**: BPM: {default_params['tempo']}, Key: {default_params['key']}, Instruments: {default_params['instruments']}
- **User Prompt**: {user_input}

### Song Lyrics:
{lyrics}
"""
    os.makedirs("songs", exist_ok=True)
    date = datetime.now().strftime("%Y%m%d")
    filename = f"songs/{date}_{title.replace(' ', '_')}.md"
    with open(filename, "w") as file:
        file.write(final_md)
    return filename


@dataclass
class SongResources:
    styles: Dict[str, str]
    tags: Dict[str, str]
    persona_styles: str
    default_params: Dict[str, Optional[str]]


class SongState(TypedDict, total=False):
    user_input: str
    song_name: Optional[str]
    persona: Optional[str]
    persona_name: Optional[str]
    use_local: bool
    resources: SongResources
    lyrics: str
    feedback: str
    score: float
    round: int
    max_rounds: int
    score_threshold: float
    preflight_passed: bool
    preflight_issues: List[str]
    metadata: Dict[str, Any]
    filename: Optional[str]
    album_art: Optional[str]


def load_resources(persona_name: Optional[str]) -> SongResources:
    styles = read_styles()
    tags = read_tags()
    persona_styles = read_persona(persona_name) if persona_name else ""
    default_params = get_default_song_params()
    return SongResources(styles=styles, tags=tags, persona_styles=persona_styles, default_params=default_params)


def progress_steps(use_local: bool):
    """Return progress steps for song generation based on mode."""
    if use_local:
        return [
            "Parsing user input and persona",
            "Loading resources (styles, tags, personas, defaults)",
            "Generating initial song draft (local LLM)",
            "Reviewing and refining lyrics (3 iterations, local LLM)",
            "Applying critic feedback (local LLM)",
            "Running preflight checks (local LLM)",
            "Generating metadata summary",
            "Skipping album artwork (local mode)",
            "Formatting and saving final song",
        ]
    return [
        "Parsing user input and persona",
        "Loading resources (styles, tags, personas, defaults)",
        "Generating initial song draft",
        "Reviewing and refining lyrics (3 iterations)",
        "Applying critic feedback",
        "Running preflight checks",
        "Generating metadata summary",
        "Generating album artwork",
        "Formatting and saving final song",
    ]