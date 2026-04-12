from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    album_id = Column(Integer, ForeignKey("albums.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    user_prompt = Column(Text, nullable=False)
    persona = Column(String(100))
    style = Column(String(100))
    vocal_gender = Column(String(50))
    use_local = Column(Boolean, default=False)
    lyrics: Optional[str] = Column(Text)
    clean_lyrics: Optional[str] = Column(Text)
    metadata_json = Column("metadata", Text)  # JSON string
    album_art = Column(Text)  # Path to album art file
    score = Column(Integer)
    status = Column(String(50), default="pending")
    generation_config = Column(Text)  # JSON string
    error_message = Column(Text)
    live_feedback = Column(Text)
    generation_started_at = Column(DateTime)
    generation_completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="songs")
    album = relationship("Album", back_populates="songs")
    files = relationship(
        "SongFile",
        back_populates="song",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    generation_session = relationship(
        "GenerationSession",
        back_populates="song",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    versions = relationship(
        "SongVersion",
        back_populates="song",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
