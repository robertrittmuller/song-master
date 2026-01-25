from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


class GenerationSession(Base):
    __tablename__ = "generation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False)
    current_stage = Column(String(100))
    progress_percentage = Column(Integer, default=0)
    stage_details = Column(Text)  # JSON string
    logs = Column(Text)  # JSON string
    error_log = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    song = relationship("Song", back_populates="generation_session")
