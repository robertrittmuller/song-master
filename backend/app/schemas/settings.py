from typing import Dict, Optional

from pydantic import BaseModel


class GenerationDefaults(BaseModel):
    genre: Optional[str]
    persona: Optional[str]
    tempo: Optional[str]
    key: Optional[str]
    instruments: Optional[str]
    mood: Optional[str]


class SettingsResponse(BaseModel):
    llm_provider: str = "openrouter"
    model: str = "gpt-4o-mini"
    temperature: float = 0.6
    max_tokens: int = 4096
    use_local: bool = False
    local_url: Optional[str] = None
    generation: GenerationDefaults
    ui: Dict[str, object] = {"theme": "dark"}
