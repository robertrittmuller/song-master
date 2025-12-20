import os
from typing import List

from backend.app.schemas import Persona
from helpers import read_persona, resolve_persona_file


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
