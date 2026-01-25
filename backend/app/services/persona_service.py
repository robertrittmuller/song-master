import os
from typing import List, Optional

from backend.app.schemas import Persona, PersonaCreate, PersonaUpdate
from helpers import (
    read_persona,
    read_persona_visual_styles,
    resolve_persona_file,
    parse_persona_styles_list
)


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
        styles = read_persona(name) if resolve_persona_file(name) else ""
        visual_styles = read_persona_visual_styles(name) if resolve_persona_file(name) else ""
        personas.append(Persona(
            name=name.title(),
            description=f"Styles from {filename}",
            styles=styles,
            visual_styles=visual_styles
        ))
    return personas


def get_persona(name: str) -> Optional[Persona]:
    """Get a single persona with all fields."""
    if not resolve_persona_file(name):
        return None
    
    styles = read_persona(name)
    visual_styles = read_persona_visual_styles(name)
    return Persona(
        name=name.title(),
        description=f"Styles from {name.lower().replace(' ', '_')}.md",
        styles=styles,
        visual_styles=visual_styles
    )


def create_persona(persona: PersonaCreate) -> Persona:
    """Create a new persona markdown file."""
    filename = f"personas/{persona.name.lower().replace(' ', '_')}.md"
    os.makedirs("personas", exist_ok=True)
    
    content = f"# Suno Persona Name\n{persona.name}\n\n## Persona styles\n{persona.styles}\n\n## Visual styles\n{persona.visual_styles or ''}\n"
    
    with open(filename, "w") as f:
        f.write(content)
        
    return Persona(
        name=persona.name.title(),
        description=f"Styles from {os.path.basename(filename)}",
        styles=persona.styles,
        visual_styles=persona.visual_styles
    )


def update_persona(name: str, persona_update: PersonaUpdate) -> Optional[Persona]:
    """Update an existing persona file."""
    file_path = resolve_persona_file(name)
    if not file_path:
        return None
        
    # Read existing content to preserve name
    with open(file_path, "r") as f:
        lines = f.readlines()
        
    # Extract name from first few lines
    persona_name = name
    for i, line in enumerate(lines):
        if line.startswith("# Suno Persona Name") and i + 1 < len(lines):
            persona_name = lines[i+1].strip()
            break

    # Get current values
    current_styles = read_persona(name)
    current_visual_styles = read_persona_visual_styles(name)
    
    # Apply updates
    new_styles = persona_update.styles if persona_update.styles is not None else current_styles
    new_visual_styles = persona_update.visual_styles if persona_update.visual_styles is not None else current_visual_styles
    
    # Write back
    content = f"# Suno Persona Name\n{persona_name}\n\n## Persona styles\n{new_styles}\n\n## Visual styles\n{new_visual_styles}\n"
    with open(file_path, "w") as f:
        f.write(content)
        
    return Persona(
        name=persona_name.title(),
        description=f"Styles from {os.path.basename(file_path)}",
        styles=new_styles,
        visual_styles=new_visual_styles
    )


def delete_persona(name: str) -> bool:
    """Delete a persona file."""
    file_path = resolve_persona_file(name)
    if not file_path:
        return False
    
    try:
        os.remove(file_path)
        return True
    except OSError:
        return False


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
