from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ModelOption(BaseModel):
    id: str
    name: Optional[str] = None
    source: str
    recommended: bool = False


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
    local_model: str = "local-model"
    regenerate_model: Optional[str] = None
    temperature: float = 0.6
    max_tokens: int = 4096
    request_timeout_seconds: float = 1200.0
    use_local: bool = False
    local_url: Optional[str] = None
    recommended_models: List[str] = Field(default_factory=list)
    recommended_local_models: List[str] = Field(default_factory=list)
    models: List[ModelOption] = Field(default_factory=list)
    generation: GenerationDefaults
    ui: Dict[str, object] = {"theme": "dark"}
