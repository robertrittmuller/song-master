import os
from typing import List, Optional

from backend.app.schemas import Persona
from helpers import read_persona, resolve_persona_file, parse_persona_styles_list


def list_personas() -> List[Persona]:
    """Return personas discovered in the personas directory."""
    personas_dir = "personas"
    personas: List[Persona] = []
    if not os.path.isdir(personas_dir):
        return personas

    for filename in sorted(os.listdir(personas_dir)):
        if not filename.endswith(".md"):
            continue
        name = filename.replace(".md", "").replace("_", " ")
        path = os.path.join(personas_dir, filename)
        styles = read_persona(name) if resolve_persona_file(name) else ""
        personas.append(Persona(name=name.title(), description=f"Styles from {filename}", styles=styles))
    return personas


def get_persona_styles(persona_name: Optional[str]) -> List[str]:
    """Get the list of style tags for a persona."""
    if not persona_name:
        return []
    persona_styles = read_persona(persona_name)
    return parse_persona_styles_list(persona_styles)


def sync_persona_style_tags(
    current_persona: Optional[str],
    new_persona: Optional[str]
) -> tuple[List[str], List[str]]:
    """
    Compare persona style tags and return added and removed tags.
    
    Returns:
        tuple: (added_tags, removed_tags)
    """
    current_tags = set(get_persona_styles(current_persona))
    new_tags = set(get_persona_styles(new_persona))
    
    added = list(new_tags - current_tags)
    removed = list(current_tags - new_tags)
    
    return added, removed
