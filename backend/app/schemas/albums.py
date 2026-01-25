from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

from backend.app.schemas.songs import SongRead


class AlbumCreate(BaseModel):
    name: str = Field(..., description="Album name")
    description: Optional[str] = None


class AlbumRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    songs: List[SongRead] = []
