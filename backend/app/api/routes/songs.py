from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.deps import get_db
from backend.app.models import GenerationSession, Song
from backend.app.schemas import SongCreate, SongDetail, SongRead, SongStatus
from backend.app.services.song_generator import generation_manager

router = APIRouter(prefix="/api/songs", tags=["songs"])


@router.get("", response_model=List[SongRead])
def list_songs(db: Session = Depends(get_db)) -> List[SongRead]:
    return db.query(Song).order_by(Song.created_at.desc()).limit(50).all()


@router.get("/{song_id}", response_model=SongDetail)
def get_song(song_id: int, db: Session = Depends(get_db)) -> SongDetail:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    return song


@router.get("/{song_id}/status", response_model=SongStatus)
def get_song_status(song_id: int, db: Session = Depends(get_db)) -> SongStatus:
    cached = generation_manager.get_status(song_id)
    if cached:
        return cached
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    return SongStatus(
        song_id=song.id,
        progress=0,
        current_stage=None,
        status=song.status,
        estimated_seconds_remaining=None,
        logs=[],
        error_message=song.error_message,
    )


@router.delete("/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song(song_id: int, db: Session = Depends(get_db)) -> None:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    # Clean up progress sessions first to avoid FK issues in SQLite
    db.query(GenerationSession).filter(GenerationSession.song_id == song_id).delete()
    db.delete(song)
    db.commit()


@router.post("/generate", response_model=SongDetail, status_code=status.HTTP_201_CREATED)
async def create_song(payload: SongCreate, db: Session = Depends(get_db)) -> SongDetail:
    """Persist a new song record and start an async generation task."""
    title = payload.title or "Untitled"
    song = Song(
        title=title,
        user_prompt=payload.user_prompt,
        persona=payload.persona,
        style=payload.style,
        use_local=payload.use_local,
        project_id=payload.project_id,
        status="pending",
        generation_config=None if not payload.generation_config else str(payload.generation_config),
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    generation_manager.start_generation(song.id, payload)
    return song
