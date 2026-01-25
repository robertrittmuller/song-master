from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


class SongVersion(Base):
    __tablename__ = "song_versions"

    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    lyrics = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    song = relationship("Song", back_populates="versions")
