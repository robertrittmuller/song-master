from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class SongCreate(BaseModel):
    user_prompt: str = Field(..., description="The song description or request")
    title: str = Field(..., description="The custom title for the song")
    persona: Optional[str] = Field(default=None, description="Persona slug or name")
    vocal_gender: Optional[str] = Field(default=None, description="Vocal gender (Male, Female, Duet)")
    style: Optional[str] = Field(default=None, description="Core style for the song")
    genre: Optional[str] = Field(default=None, description="Detailed genre for the song")
    tempo: Optional[str] = Field(default=None, description="Tempo in BPM")
    key: Optional[str] = Field(default=None, description="Musical key")
    instruments: Optional[str] = Field(default=None, description="Instruments to include")
    mood: Optional[str] = Field(default=None, description="Mood of the song")
    use_local: bool = Field(default=False, description="Whether to use local LLM mode")
    album_id: Optional[int] = Field(default=None, description="Associated album ID")
    generation_config: Optional[dict[str, Any]] = Field(
        default=None, description="Advanced generation parameters"
    )
    generate_album_art: bool = Field(default=True, description="Whether to generate album art")


class SongUpdate(BaseModel):
    title: Optional[str] = None
    album_id: Optional[int] = None
    score: Optional[int] = None


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


class SongVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_number: int
    lyrics: str
    created_at: datetime


class SongDetail(SongRead):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    user_prompt: str
    lyrics: Optional[str]
    vocal_gender: Optional[str] = None
    metadata: Optional[str] = Field(default=None, alias="metadata_json")
    album_art: Optional[str] = None
    album_id: Optional[int] = None
    generation_config: Optional[str] = None
    clean_lyrics: Optional[str] = None
    error_message: Optional[str] = None
    live_feedback: Optional[str] = None
    versions: List[SongVersionRead] = []


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
