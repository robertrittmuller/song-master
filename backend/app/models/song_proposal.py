from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, Text, String

from backend.app.db.base import Base


class SongProposal(Base):
    __tablename__ = "song_proposals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    source_prompt = Column(Text, nullable=False)
    use_local = Column(Boolean, default=False)
    status = Column(String(50), default="open", nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
