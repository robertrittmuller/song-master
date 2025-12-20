from typing import Optional

from pydantic import BaseModel


class Persona(BaseModel):
    name: str
    description: Optional[str] = None
    styles: Optional[str] = None
