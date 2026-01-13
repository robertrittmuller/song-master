from typing import List

from fastapi import APIRouter, HTTPException

from backend.app.schemas import Persona, PersonaCreate, PersonaUpdate
from backend.app.services.persona_service import (
    list_personas,
    get_persona,
    create_persona,
    update_persona,
    delete_persona
)

router = APIRouter(prefix="/api/personas", tags=["personas"])


@router.get("", response_model=List[Persona])
def get_personas() -> List[Persona]:
    return list_personas()


@router.get("/{name}", response_model=Persona)
def get_persona_route(name: str) -> Persona:
    persona = get_persona(name)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona


@router.post("", response_model=Persona)
def create_persona_route(persona: PersonaCreate) -> Persona:
    return create_persona(persona)


@router.put("/{name}", response_model=Persona)
def update_persona_route(name: str, persona: PersonaUpdate) -> Persona:
    updated = update_persona(name, persona)
    if not updated:
        raise HTTPException(status_code=404, detail="Persona not found")
    return updated


@router.delete("/{name}")
def delete_persona_route(name: str):
    success = delete_persona(name)
    if not success:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"status": "success"}
