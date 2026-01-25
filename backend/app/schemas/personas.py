from typing import Optional

from pydantic import BaseModel


class Persona(BaseModel):
    name: str
    description: Optional[str] = None
    styles: Optional[str] = None
    visual_styles: Optional[str] = None


class PersonaCreate(BaseModel):
    name: str
    styles: str
    visual_styles: Optional[str] = None


class PersonaUpdate(BaseModel):
    styles: Optional[str] = None
    visual_styles: Optional[str] = None
