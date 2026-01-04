from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from backend.app.db.deps import get_db
from backend.app.models import GenerationSession, Song
from backend.app.schemas import SongCreate, SongDetail, SongRead, SongStatus, SongUpdate
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
        vocal_gender=payload.vocal_gender,
        use_local=payload.use_local,
        album_id=payload.album_id,
        status="pending",
        generation_config=None if not payload.generation_config else str(payload.generation_config),
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    generation_manager.start_generation(song.id, payload)
    return song


@router.patch("/{song_id}", response_model=SongDetail)
def update_song(
    song_id: int, payload: SongUpdate, db: Session = Depends(get_db)
) -> SongDetail:
    """Update song metadata (e.g., move to an album)."""
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(song, key, value)

    db.add(song)
    db.commit()
    db.refresh(song)
    return song


@router.post("/{song_id}/regenerate-art", response_model=SongDetail)
async def regenerate_song_art(song_id: int, db: Session = Depends(get_db)) -> SongDetail:
    """Trigger album art regeneration for an existing song."""
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    from helpers import extract_title, generate_album_art
    import json

    title = extract_title(song.lyrics or "", song.title)
    
    # Extract mood from metadata_json if available
    metadata = {}
    if song.metadata_json:
        try:
            metadata = json.loads(song.metadata_json)
        except:
            pass
            
    mood = metadata.get("mood")
    
    artwork_path = generate_album_art(
        title, 
        song.user_prompt,
        persona_name=song.persona,
        style=song.style,
        mood=mood,
        vocal_gender=song.vocal_gender
    )

    if artwork_path:
        song.album_art = artwork_path
        db.commit()
        db.refresh(song)

    return song


@router.post("/{song_id}/regenerate-lyrics", response_model=SongDetail)
async def regenerate_song_lyrics(song_id: int, db: Session = Depends(get_db)) -> SongDetail:
    """Trigger lyric regeneration for an existing song."""
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    generation_manager.regenerate_lyrics(song_id, db)
    return song


@router.post("/{song_id}/live-feedback", response_model=SongDetail)
async def live_listen_feedback(
    song_id: int, file: UploadFile = UploadFile(...), db: Session = Depends(get_db)
) -> SongDetail:
    """Submit an audio file for live feedback from a multimodal LLM."""
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    if song.use_local:
        raise HTTPException(status_code=400, detail="Live Listen Feedback is not available for local models.")

    from backend.app.services.live_listen_service import process_live_listen_feedback
    
    # We must read song data as dict for the service
    song_data = {
        "lyrics": song.lyrics,
        "title": song.title,
        "user_prompt": song.user_prompt
    }

    result = await process_live_listen_feedback(song_id, file, song_data, song.use_local)

    # Update song with revised lyrics
    if "revised_lyrics" in result:
        from backend.app.models import SongVersion
        
        # Save previous lyrics to historical versions if they exist
        if song.lyrics:
            # Get the current highest version number
            current_versions = db.query(SongVersion).filter(SongVersion.song_id == song_id).all()
            next_version = len(current_versions) + 1
            
            db.add(SongVersion(
                song_id=song_id,
                version_number=next_version,
                lyrics=song.lyrics
            ))

        song.lyrics = result["revised_lyrics"]
        # We could also store the feedback in the DB if we had a column for it,
        # but for now we just update the lyrics.
        db.add(song)
        db.commit()
        db.refresh(song)

    return song
