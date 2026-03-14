import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
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
        
    return "\n".join(new_lines).strip()


def get_repo_root() -> str:
    """Return the absolute path to the repository root."""
    return str(Path(__file__).resolve().parent)


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
    vocal_gender: Optional[str] = None
) -> str:
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
    storage = get_song_storage_info(title)
    os.makedirs(storage["abs_folder"], exist_ok=True)
    
    # Initial output file, format may vary based on API
    output_file = f"{storage['abs_image_base']}.jpg"
    print(f"[DEBUG] output_file (initial): {output_file}")
    
    try:
        generate_album_art_image(artwork_prompt, output_file)
        # The actual file might have different extension (PNG/WebP) based on API response
        # Check for the actual file
        base_path = storage["abs_image_base"]
        actual_file = None
        for ext in [".png", ".jpg", ".webp"]:
            check_path = f"{base_path}{ext}"
            if os.path.exists(check_path):
                actual_file = check_path
                print(f"[DEBUG] Found actual file: {actual_file}")
                break
        
        if actual_file:
            # Overwrite check - if we have multiple extensions, we might want to clean up others
            # but for now we just return the actual one found.
            return relativize_storage_path(actual_file)
        else:
            print(f"[DEBUG] Image generation completed, checking file exists: {os.path.exists(output_file)}")
            return relativize_storage_path(output_file) if os.path.exists(output_file) else None
    except Exception as e:
        print(f"Warning: Failed to generate album art: {e}")
        return None


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
    
    # Split into lines and process each line
    lines = lyrics.split('\n')
    clean_lines = []
    
    # Define structural headers to preserve (extract just the header part)
    structural_patterns = [
        r'\[Verse\s*\d*\]',
        r'\[Pre-Chorus\]',
        r'\[Chorus\]',
        r'\[Bridge\]',
        r'\[Outro\]',
        r'\[Intro\]',
        r'\[Final Chorus\]',
        r'\[Guitar Solo\]',
        r'\[Instrumental\]'
    ]
    
    for line in lines:
        stripped_line = line.strip()
        
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
    path = os.path.join("tags", "default-tags.txt")
    if not os.path.exists(path):
        return []

    instruments = set()
    with open(path, "r") as f:
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
    generate_album_art: bool
    genre: Optional[str]
    tempo: Optional[str]
    key: Optional[str]
    instruments: Optional[str]
    mood: Optional[str]
    vocal_gender: Optional[str]


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
