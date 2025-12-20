from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class SongCreate(BaseModel):
    user_prompt: str = Field(..., description="The song description or request")
    title: Optional[str] = Field(default=None, description="Optional custom title")
    persona: Optional[str] = Field(default=None, description="Persona slug or name")
    style: Optional[str] = Field(default=None, description="Core style for the song")
    use_local: bool = Field(default=False, description="Whether to use local LLM mode")
    project_id: Optional[int] = Field(default=None, description="Associated project ID")
    generation_config: Optional[dict[str, Any]] = Field(
        default=None, description="Advanced generation parameters"
    )


class SongRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    title: str
    status: str
    score: Optional[int]
    persona: Optional[str]
    use_local: bool
    created_at: datetime
    album_art: Optional[str] = None


class SongDetail(SongRead):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    user_prompt: str
    lyrics: Optional[str]
    metadata: Optional[str] = Field(default=None, alias="metadata_json")
    album_art: Optional[str] = None
    project_id: Optional[int] = None
    generation_config: Optional[str] = None
    clean_lyrics: Optional[str] = None
    error_message: Optional[str] = None


class GenerationLog(BaseModel):
    timestamp: datetime
    message: str


class SongStatus(BaseModel):
    song_id: int
    progress: int
    current_stage: Optional[str]
    status: str
    estimated_seconds_remaining: Optional[int] = None
    logs: List[GenerationLog] = Field(default_factory=list)
    error_message: Optional[str] = None
