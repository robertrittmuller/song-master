from typing import List

from fastapi import APIRouter

from backend.app.schemas import Persona
from backend.app.services.persona_service import list_personas

router = APIRouter(prefix="/api/personas", tags=["personas"])


@router.get("", response_model=List[Persona])
def get_personas() -> List[Persona]:
    return list_personas()
