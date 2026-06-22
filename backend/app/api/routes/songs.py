from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, File, Query, status, UploadFile
from sqlalchemy.orm import Session

from backend.app.db.deps import get_current_user, get_db
from backend.app.models import Album, GenerationSession, Song, SongFile, SongProposal, SongVersion, User
from backend.app.schemas import (
    DemoTrackStatus,
    SongCreate,
    SongDetail,
    SongLiveFeedbackDemoTrackRequest,
    SongLyricsUpdate,
    SongRegenerateArtRequest,
    SongRead,
    SongRegenerateLyricsRequest,
    SongStatus,
    SongUpdate,
)
from backend.app.services.demo_track_generator import demo_track_generation_manager
from backend.app.services.persona_service import sync_persona_style_tags
from backend.app.services.song_generator import generation_manager, resolve_lyrics_model

router = APIRouter(prefix="/api/songs", tags=["songs"])


def _get_user_song(db: Session, current_user: User, song_id: int) -> Song:
    song = db.query(Song).filter(Song.id == song_id, Song.user_id == current_user.id).first()
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    return song


def _ensure_user_album(db: Session, current_user: User, album_id: Optional[int]) -> Optional[Album]:
    if album_id is None:
        return None

    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    return album


def _art_mime_type(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "image/jpeg"


def _upsert_song_art_file(
    db: Session,
    song_id: int,
    file_path: str,
    is_primary: bool,
) -> SongFile:
    from backend.shared.helpers import resolve_storage_path

    path = Path(file_path)
    abs_path = Path(resolve_storage_path(file_path))
    song_file = (
        db.query(SongFile)
        .filter(SongFile.song_id == song_id, SongFile.file_path == file_path)
        .first()
    )

    if not song_file:
        song_file = SongFile(
            song_id=song_id,
            file_type="artwork",
            file_path=file_path,
            file_name=path.name,
        )

    song_file.file_type = "artwork"
    song_file.file_path = file_path
    song_file.file_name = path.name
    song_file.file_size = abs_path.stat().st_size if abs_path.exists() else None
    song_file.mime_type = _art_mime_type(file_path)
    song_file.is_primary = is_primary
    db.add(song_file)
    return song_file


def _clear_primary_art_files(db: Session, song_id: int) -> None:
    db.query(SongFile).filter(
        SongFile.song_id == song_id,
        SongFile.file_type == "artwork",
    ).update({SongFile.is_primary: False})


def _song_demo_track_status(song: Song) -> DemoTrackStatus:
    has_demo_track = any(song_file.file_type == "demo_track" for song_file in song.files or [])
    return DemoTrackStatus(
        song_id=song.id,
        progress=100 if has_demo_track else 0,
        current_stage="Demo track ready" if has_demo_track else None,
        status="completed" if has_demo_track else "idle",
        estimated_seconds_remaining=None,
        logs=[],
        error_message=None,
    )


def _extract_section(markdown: str, heading: str, level: str = "##") -> str:
    import re

    pattern = rf"{re.escape(level)} {re.escape(heading)}\n(.*?)(?=\n## |\n### |\Z)"
    match = re.search(pattern, markdown, flags=re.DOTALL)
    if not match:
        return ""
    return match.group(1).strip()


def _extract_metadata_value(block: str, label: str) -> Optional[str]:
    import re

    pattern = rf"- \*\*{re.escape(label)}\*\*:\s*(.*)"
    match = re.search(pattern, block)
    if not match:
        return None
    return match.group(1).strip()


def _parse_song_markdown(markdown: str) -> Dict[str, Optional[str]]:
    """Parse a Song Master markdown file into structured fields."""
    import re

    title = None
    description = None
    for line in markdown.splitlines():
        stripped = line.strip()
        if title is None and stripped.startswith("## "):
            title = stripped[3:].strip()
            continue
        if description is None and stripped.startswith("### "):
            heading = stripped[4:].strip()
            if heading.lower().startswith("song lyrics") or heading.lower().startswith("clean lyrics"):
                continue
            description = heading
            if title:
                break

    styles_block = _extract_section(markdown, "Suno Styles")
    exclude_block = _extract_section(markdown, "Suno Exclude-styles")
    metadata_block = _extract_section(markdown, "Additional Metadata")
    lyrics_block = _extract_section(markdown, "Song Lyrics:", level="###")
    clean_lyrics_block = _extract_section(markdown, "Clean Lyrics (No Style Tags):", level="###")

    def parse_styles(block: str) -> List[str]:
        styles_line = " ".join([line.strip() for line in block.splitlines() if line.strip()])
        if not styles_line or styles_line.lower() == "none":
            return []
        return [style.strip() for style in styles_line.split(",") if style.strip()]

    suno_styles = parse_styles(styles_block)
    suno_exclude_styles = parse_styles(exclude_block)

    emotional_arc = _extract_metadata_value(metadata_block, "Emotional Arc")
    target_audience = _extract_metadata_value(metadata_block, "Target Audience")
    commercial_potential = _extract_metadata_value(metadata_block, "Commercial Potential")
    technical_notes = _extract_metadata_value(metadata_block, "Technical Notes")
    user_prompt = _extract_metadata_value(metadata_block, "User Prompt")

    tempo = None
    key = None
    instruments = None
    if technical_notes:
        tempo_match = re.search(r"BPM:\s*([^,]+)", technical_notes)
        key_match = re.search(r"Key:\s*([^,]+)", technical_notes)
        instruments_match = re.search(r"Instruments:\s*(.*)", technical_notes)
        if tempo_match:
            tempo = tempo_match.group(1).strip()
        if key_match:
            key = key_match.group(1).strip()
        if instruments_match:
            instruments = instruments_match.group(1).strip()

    return {
        "title": title,
        "description": description,
        "suno_styles": suno_styles,
        "suno_exclude_styles": suno_exclude_styles,
        "mood": emotional_arc,
        "target_audience": target_audience,
        "commercial_potential": commercial_potential,
        "tempo": tempo,
        "key": key,
        "instruments": instruments,
        "user_prompt": user_prompt,
        "lyrics": lyrics_block,
        "clean_lyrics": clean_lyrics_block,
    }


@router.get("", response_model=List[SongRead])
def list_songs(
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
) -> List[SongRead]:
    songs_query = (
        db.query(Song)
        .filter(Song.user_id == current_user.id)
        .order_by(Song.created_at.desc())
        .offset(offset)
    )

    if limit is not None:
        songs_query = songs_query.limit(limit)

    return songs_query.all()


@router.get("/{song_id}", response_model=SongDetail)
def get_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongDetail:
    return _get_user_song(db, current_user, song_id)


@router.get("/{song_id}/status", response_model=SongStatus)
def get_song_status(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongStatus:
    song = _get_user_song(db, current_user, song_id)
    cached = generation_manager.get_status(song_id)
    if cached:
        return cached
    return SongStatus(
        song_id=song.id,
        progress=0,
        current_stage=None,
        status=song.status,
        estimated_seconds_remaining=None,
        logs=[],
        error_message=song.error_message,
    )


@router.get("/{song_id}/demo-track/status", response_model=DemoTrackStatus)
def get_demo_track_status(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DemoTrackStatus:
    song = _get_user_song(db, current_user, song_id)
    cached = demo_track_generation_manager.get_status(song_id)
    if cached:
        return cached
    return _song_demo_track_status(song)


@router.delete("/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    song = _get_user_song(db, current_user, song_id)

    # Clean up dependent rows explicitly so SQLite dev databases do not retain
    # orphaned records if foreign key enforcement was previously disabled.
    db.query(GenerationSession).filter(GenerationSession.song_id == song_id).delete()
    db.query(SongVersion).filter(SongVersion.song_id == song_id).delete()
    db.query(SongFile).filter(SongFile.song_id == song_id).delete()
    db.delete(song)
    db.commit()


@router.post("/generate", response_model=SongDetail, status_code=status.HTTP_201_CREATED)
async def create_song(
    payload: SongCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongDetail:
    """Persist a new song record and start an async generation task."""
    import json

    title = payload.title or "Untitled"
    proposal = None
    if payload.proposal_id is not None:
        proposal = (
            db.query(SongProposal)
            .filter(SongProposal.id == payload.proposal_id, SongProposal.user_id == current_user.id)
            .first()
        )
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song proposal not found")

    _ensure_user_album(db, current_user, payload.album_id)

    song = Song(
        user_id=current_user.id,
        title=title,
        user_prompt=payload.user_prompt,
        persona=payload.persona,
        style=payload.style,
        vocal_gender=payload.vocal_gender,
        use_local=payload.use_local,
        lyrics_model=resolve_lyrics_model(payload.use_local, payload.lyrics_model),
        album_id=payload.album_id,
        status="pending",
        generation_config=json.dumps(payload.generation_config) if payload.generation_config else None,
    )
    db.add(song)
    if proposal is not None:
        proposal.status = "accepted"
        proposal.accepted_at = datetime.utcnow()
    db.commit()
    db.refresh(song)
    generation_manager.start_generation(song.id, payload)
    return song


@router.post("/import", response_model=SongDetail, status_code=status.HTTP_201_CREATED)
async def import_song_markdown(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongDetail:
    """Import a song from a Song Master markdown file."""
    if not file.filename or not file.filename.lower().endswith(".md"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .md files are supported.")

    raw_content = await file.read()
    try:
        markdown = raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to decode markdown file. Please upload a UTF-8 .md file."
        ) from exc

    parsed = _parse_song_markdown(markdown)
    title = parsed.get("title") or (file.filename.rsplit(".", 1)[0] if file.filename else "Untitled")
    user_prompt = parsed.get("user_prompt") or "Imported from markdown"
    lyrics = parsed.get("lyrics") or ""
    clean_lyrics = parsed.get("clean_lyrics")

    if not clean_lyrics and lyrics:
        from backend.shared.helpers import strip_style_tags

        clean_lyrics = strip_style_tags(lyrics)

    import json

    metadata: Dict[str, object] = {}
    if parsed.get("description"):
        metadata["description"] = parsed["description"]
    if parsed.get("suno_styles") is not None:
        metadata["suno_styles"] = parsed["suno_styles"]
    if parsed.get("suno_exclude_styles") is not None:
        metadata["suno_exclude_styles"] = parsed["suno_exclude_styles"]
    if parsed.get("mood"):
        metadata["mood"] = parsed["mood"]
    if parsed.get("target_audience"):
        metadata["target_audience"] = parsed["target_audience"]
    if parsed.get("commercial_potential"):
        metadata["commercial_potential"] = parsed["commercial_potential"]
    if parsed.get("tempo"):
        metadata["tempo"] = parsed["tempo"]
    if parsed.get("key"):
        metadata["key"] = parsed["key"]
    if parsed.get("instruments"):
        metadata["instruments"] = parsed["instruments"]

    song = Song(
        user_id=current_user.id,
        title=title,
        user_prompt=user_prompt,
        lyrics=lyrics,
        clean_lyrics=clean_lyrics,
        metadata_json=json.dumps(metadata) if metadata else None,
        status="completed",
        use_local=False,
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    return song


@router.patch("/{song_id}", response_model=SongDetail)
def update_song(
    song_id: int,
    payload: SongUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongDetail:
    """Update song metadata (e.g., move to an album, change persona)."""
    import json
    from datetime import datetime

    song = _get_user_song(db, current_user, song_id)

    update_data = payload.model_dump(exclude_unset=True)

    if "album_id" in update_data and update_data["album_id"] is not None:
        _ensure_user_album(db, current_user, update_data["album_id"])

    # Handle title changes and rename files/folders
    if "title" in update_data and update_data["title"] != song.title:
        if song.status == "generating":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot rename song while it is generating"
            )

        from backend.shared.helpers import rename_song_files, get_song_storage_info
        import os
        
        old_title = song.title
        new_title = update_data["title"]
        song_date = song.created_at.strftime("%Y-%m-%d") if song.created_at else datetime.now().strftime("%Y-%m-%d")
        
        old_info = get_song_storage_info(old_title, song_date)
        new_info = get_song_storage_info(new_title, song_date)

        # check if target already exists to avoid collisions
        if os.path.exists(new_info["abs_folder"]) and old_info["folder"] != new_info["folder"]:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A song folder already exists at {new_info['folder']}"
            )

        # Do the physical rename
        rename_song_files(old_title, new_title, song_date)
        
        old_base = os.path.basename(old_info["image_base"])
        new_base = os.path.basename(new_info["image_base"])
        
        # Update database fields that contain the path/filename strings
        if song.album_art:
            song.album_art = song.album_art.replace(old_info["folder"], new_info["folder"]).replace(old_base, new_base)
             
        for song_file in song.files:
            # Update the path and filename in the database
            if old_info["folder"] in song_file.file_path:
                song_file.file_path = song_file.file_path.replace(old_info["folder"], new_info["folder"])
            
            if old_base in song_file.file_path:
                song_file.file_path = song_file.file_path.replace(old_base, new_base)
            
            if old_base in song_file.file_name:
                song_file.file_name = song_file.file_name.replace(old_base, new_base)

    # Handle description update (stored in metadata_json)
    if "description" in update_data:
        description = update_data.pop("description")
        metadata = {}
        if song.metadata_json:
            try:
                metadata = json.loads(song.metadata_json)
            except:
                pass
        metadata["description"] = description
        song.metadata_json = json.dumps(metadata)

    # Handle persona changes and sync style tags
    if "persona" in update_data:
        new_persona = update_data["persona"]
        old_persona = song.persona
        
        # Only process if there's actually a change
        if new_persona != old_persona:
            added_tags, removed_tags = sync_persona_style_tags(old_persona, new_persona)
            
            # Log the persona style tag changes
            if added_tags or removed_tags:
                print(f"Persona change: {old_persona} -> {new_persona}")
                if added_tags:
                    print(f"  Added style tags: {added_tags}")
                if removed_tags:
                    print(f"  Removed style tags: {removed_tags}")

            # Update metadata_json with the new persona's style tags
            metadata = {}
            if song.metadata_json:
                try:
                    metadata = json.loads(song.metadata_json)
                except:
                    pass

            # Get current suno_styles or default to empty list
            current_styles = metadata.get("suno_styles", [])
            if isinstance(current_styles, str):
                current_styles = [s.strip() for s in current_styles.split(",") if s.strip()]
            elif not isinstance(current_styles, list):
                current_styles = []

            # Remove old persona tags
            if removed_tags:
                current_styles = [s for s in current_styles if s not in removed_tags]

            # Add new persona tags
            if added_tags:
                current_styles.extend(added_tags)
                # Remove duplicates while preserving order
                seen = set()
                unique_styles = []
                for s in current_styles:
                    if s not in seen:
                        seen.add(s)
                        unique_styles.append(s)
                current_styles = unique_styles

            metadata["suno_styles"] = current_styles
            song.metadata_json = json.dumps(metadata)
    for key, value in update_data.items():
        setattr(song, key, value)

    db.add(song)
    db.commit()
    db.refresh(song)
    return song


@router.post("/{song_id}/lyrics", response_model=SongDetail)
def update_song_lyrics(
    song_id: int,
    payload: SongLyricsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongDetail:
    """Update song lyrics and snapshot the previous version."""
    from sqlalchemy import func
    from backend.shared.helpers import strip_style_tags

    song = _get_user_song(db, current_user, song_id)

    new_lyrics = payload.lyrics
    if song.lyrics and song.lyrics != new_lyrics:
        max_version = (
            db.query(func.max(SongVersion.version_number))
            .filter(SongVersion.song_id == song_id)
            .scalar()
        )
        next_version = (max_version or 0) + 1
        db.add(
            SongVersion(
                song_id=song_id,
                version_number=next_version,
                lyrics_model=song.lyrics_model,
                lyrics=song.lyrics,
            )
        )

    song.lyrics = new_lyrics
    song.lyrics_model = None
    song.clean_lyrics = strip_style_tags(new_lyrics) if new_lyrics else None
    db.add(song)
    db.commit()
    db.refresh(song)
    return song


@router.post("/{song_id}/regenerate-art", response_model=SongDetail)
async def regenerate_song_art(
    song_id: int,
    payload: Optional[SongRegenerateArtRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongDetail:
    """Trigger album art regeneration for an existing song."""
    song = _get_user_song(db, current_user, song_id)

    from backend.shared.helpers import extract_title, generate_album_art, normalize_album_art_aspect_ratio
    import json

    title = extract_title(song.lyrics or "", song.title)
    song_date = song.created_at.strftime("%Y-%m-%d") if song.created_at else datetime.now().strftime("%Y-%m-%d")
    filename_suffix = f"_art_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    # Extract mood from metadata_json if available
    metadata = {}
    if song.metadata_json:
        try:
            metadata = json.loads(song.metadata_json)
        except:
            pass
            
    mood = metadata.get("mood")

    generation_config = {}
    if song.generation_config:
        try:
            parsed_config = json.loads(song.generation_config)
            if isinstance(parsed_config, dict):
                generation_config = parsed_config
        except json.JSONDecodeError:
            pass

    requested_aspect_ratio = payload.aspect_ratio if payload else None
    aspect_ratio = normalize_album_art_aspect_ratio(
        requested_aspect_ratio or generation_config.get("art_aspect_ratio")
    )
    
    artwork_path = generate_album_art(
        title,
        song.user_prompt,
        persona_name=song.persona,
        style=song.style,
        mood=mood,
        vocal_gender=song.vocal_gender,
        date=song_date,
        filename_suffix=filename_suffix,
        aspect_ratio=aspect_ratio,
    )

    if artwork_path:
        if song.album_art:
            _upsert_song_art_file(db, song.id, song.album_art, is_primary=False)
        _clear_primary_art_files(db, song.id)
        song.album_art = artwork_path
        generation_config["art_aspect_ratio"] = aspect_ratio
        song.generation_config = json.dumps(generation_config)
        _upsert_song_art_file(db, song.id, artwork_path, is_primary=True)
        db.add(song)
        db.commit()
        db.refresh(song)

    return song


@router.post("/{song_id}/demo-track", response_model=DemoTrackStatus)
async def create_demo_track(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DemoTrackStatus:
    """Create a demo track for an existing song via MiniMax music generation."""
    song = _get_user_song(db, current_user, song_id)

    if song.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Demo tracks can only be created for completed songs.",
        )
    if song.use_local:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create Demo Track is not available for local-only songs.",
        )
    if not (song.clean_lyrics or song.lyrics):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Song lyrics are required before creating a demo track.",
        )

    return demo_track_generation_manager.start_generation(song.id)


@router.post("/{song_id}/upload-art", response_model=SongDetail)
async def upload_song_art(
    song_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongDetail:
    """Upload a custom album art image (JPEG or PNG) for a song."""
    song = _get_user_song(db, current_user, song_id)

    allowed_types = {"image/jpeg", "image/png"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPEG or PNG files are supported.")

    filename = file.filename or ""
    extension = ""
    if filename and "." in filename:
        extension = f".{filename.rsplit('.', 1)[-1].lower()}"

    if extension not in {".jpg", ".jpeg", ".png"}:
        extension = ".jpg" if file.content_type == "image/jpeg" else ".png"

    import os
    from backend.shared.helpers import get_song_storage_info

    song_date = song.created_at.strftime("%Y-%m-%d") if song.created_at else datetime.now().strftime("%Y-%m-%d")
    storage = get_song_storage_info(song.title, song_date)
    os.makedirs(storage["abs_folder"], exist_ok=True)

    filename_suffix = f"_custom_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    file_path_rel = f"{storage['image_base']}{filename_suffix}{extension}"
    file_path = f"{storage['abs_image_base']}{filename_suffix}{extension}"

    try:
        with open(file_path, "wb") as out_file:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                out_file.write(chunk)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded album art."
        ) from exc

    if song.album_art:
        _upsert_song_art_file(db, song.id, song.album_art, is_primary=False)
    _clear_primary_art_files(db, song.id)
    song.album_art = file_path_rel
    _upsert_song_art_file(db, song.id, file_path_rel, is_primary=True)
    db.add(song)
    db.commit()
    db.refresh(song)
    return song


@router.post("/{song_id}/regenerate-lyrics", response_model=SongDetail)
async def regenerate_song_lyrics(
    song_id: int,
    payload: Optional[SongRegenerateLyricsRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongDetail:
    """Trigger lyric regeneration for an existing song."""
    song = _get_user_song(db, current_user, song_id)

    generation_manager.regenerate_lyrics(song_id, db, lyrics_model=payload.lyrics_model if payload else None)
    return song


@router.post("/{song_id}/live-feedback", response_model=SongDetail)
async def live_listen_feedback(
    song_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongDetail:
    """Submit an audio file for live feedback from a multimodal LLM."""
    song = _get_user_song(db, current_user, song_id)

    from backend.app.services.live_listen_service import process_live_listen_feedback
    
    # We must read song data as dict for the service
    song_data = {
        "lyrics": song.lyrics,
        "title": song.title,
        "user_prompt": song.user_prompt
    }

    try:
        result = await process_live_listen_feedback(song_id, file, song_data, song.use_local)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

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
                lyrics_model=song.lyrics_model,
                lyrics=song.lyrics
            ))

        song.lyrics = result["revised_lyrics"]
        song.live_feedback = result.get("feedback")
        # We could also store the feedback in the DB if we had a column for it,
        # but for now we just update the lyrics.
        db.add(song)
        db.commit()
        db.refresh(song)

    return song


@router.post("/{song_id}/live-feedback/demo-track", response_model=SongDetail)
async def live_listen_feedback_from_demo_track(
    song_id: int,
    payload: SongLiveFeedbackDemoTrackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongDetail:
    """Submit an existing song demo track for live feedback from a multimodal LLM."""
    song = _get_user_song(db, current_user, song_id)

    demo_track = (
        db.query(SongFile)
        .filter(
            SongFile.song_id == song_id,
            SongFile.file_type == "demo_track",
            SongFile.file_path == payload.file_path,
        )
        .first()
    )
    if not demo_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo track not found for this song.",
        )

    from backend.app.services.live_listen_service import process_live_listen_feedback_from_path
    from backend.shared.helpers import resolve_storage_path

    audio_path = Path(resolve_storage_path(demo_track.file_path))
    if not audio_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo track file is missing from storage.",
        )

    song_data = {
        "lyrics": song.lyrics,
        "title": song.title,
        "user_prompt": song.user_prompt,
    }

    try:
        result = await process_live_listen_feedback_from_path(
            song_id,
            str(audio_path),
            song_data,
            song.use_local,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if "revised_lyrics" in result:
        from backend.app.models import SongVersion

        if song.lyrics:
            current_versions = db.query(SongVersion).filter(SongVersion.song_id == song_id).all()
            next_version = len(current_versions) + 1

            db.add(SongVersion(
                song_id=song_id,
                version_number=next_version,
                lyrics_model=song.lyrics_model,
                lyrics=song.lyrics
            ))

        song.lyrics = result["revised_lyrics"]
        song.live_feedback = result.get("feedback")
        db.add(song)
        db.commit()
        db.refresh(song)

    return song
