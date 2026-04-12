from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict


class SongProposalGenerate(BaseModel):
    source_prompt: str = Field(..., min_length=1, description="High-level proposal guidance")
    count: int = Field(default=5, description="Number of proposals to generate")
    use_local: bool = Field(default=False, description="Whether to use local LLM mode")

    @field_validator("source_prompt")
    @classmethod
    def validate_source_prompt(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("source_prompt is required")
        return stripped

    @field_validator("count")
    @classmethod
    def validate_count(cls, value: int) -> int:
        if value not in {5, 10}:
            raise ValueError("count must be 5 or 10")
        return value


class SongProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    prompt: str
    source_prompt: str
    use_local: bool
    status: str
    accepted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SongProposalGenerateResponse(BaseModel):
    proposals: List[SongProposalRead]
