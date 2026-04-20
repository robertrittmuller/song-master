import json
import os
import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from backend.app.db.deps import get_current_user, get_db
from backend.app.models import Album, User
from backend.app.schemas import AlbumArtGenerateRequest, AlbumCreate, AlbumRead, AlbumUpdate
from backend.shared.helpers import generate_artwork_from_prompt, get_album_storage_info, read_persona_visual_styles

router = APIRouter(prefix="/api/albums", tags=["albums"])


def _get_user_album(db: Session, current_user: User, album_id: int) -> Album:
    album = (
        db.query(Album)
        .options(joinedload(Album.songs))
        .filter(Album.id == album_id, Album.user_id == current_user.id)
        .first()
    )
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    return album


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    ordered = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(value)
    return ordered


def _extract_lyric_theme_lines(lyrics: Optional[str], limit: int = 2) -> List[str]:
    if not lyrics:
        return []

    theme_lines = []
    for raw_line in lyrics.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            continue
        if line.endswith(":") and len(line.split()) <= 4:
            continue
        if len(line) < 12:
            continue
        theme_lines.append(line)
        if len(theme_lines) >= limit:
            break
    return theme_lines


def _normalize_prompt_fragment(value: Optional[str], max_length: int = 180) -> Optional[str]:
    cleaned = _clean_optional_text(value)
    if not cleaned:
        return None
    if len(cleaned) <= max_length:
        return cleaned
    truncated = cleaned[:max_length].rsplit(" ", 1)[0].strip()
    return truncated or cleaned[:max_length].strip()


def _build_album_art_request(album: Album, prompt_direction: Optional[str] = None) -> str:
    personas = []
    persona_visual_styles = []
    song_themes = []
    lyric_imagery = []

    for song in album.songs or []:
        if song.persona:
            personas.append(song.persona.strip().title())
            visual_styles = _normalize_prompt_fragment(read_persona_visual_styles(song.persona), max_length=220)
            if visual_styles:
                persona_visual_styles.append(visual_styles)

        metadata = {}
        if song.metadata_json:
            try:
                metadata = json.loads(song.metadata_json)
            except (TypeError, ValueError):
                metadata = {}

        for candidate in [
            metadata.get("description"),
            metadata.get("mood"),
            song.user_prompt,
        ]:
            normalized = _normalize_prompt_fragment(candidate)
            if normalized:
                song_themes.append(normalized)
                break

        lyric_imagery.extend(_extract_lyric_theme_lines(song.clean_lyrics or song.lyrics, limit=2))

    personas = _dedupe_preserve_order(personas)
    persona_visual_styles = _dedupe_preserve_order(persona_visual_styles)
    song_themes = _dedupe_preserve_order(song_themes)
    lyric_imagery = _dedupe_preserve_order(lyric_imagery)
    active_prompt_direction = _normalize_prompt_fragment(
        prompt_direction if prompt_direction is not None else album.art_prompt_direction,
        max_length=320,
    )

    prompt_parts = [
        f"Album cover for the album '{album.name}'.",
        "Create one cohesive release design rather than separate single covers.",
    ]

    album_description = _normalize_prompt_fragment(album.description, max_length=220)
    if album_description:
        prompt_parts.append(f"Album description: {album_description}.")
    if personas:
        prompt_parts.append(f"Personas used across the songs: {', '.join(personas[:6])}.")
    if persona_visual_styles:
        prompt_parts.append(
            "Blend these persona-driven visual styles into a single cover: "
            f"{'; '.join(persona_visual_styles[:4])}."
        )
    if song_themes:
        prompt_parts.append(f"Recurring themes across the songs: {'; '.join(song_themes[:6])}.")
    if lyric_imagery:
        prompt_parts.append(
            "Lyric imagery to draw from: "
            + "; ".join(f'"{line}"' for line in lyric_imagery[:6])
            + "."
        )
    if active_prompt_direction:
        prompt_parts.append(f"Additional user art direction: {active_prompt_direction}.")

    return " ".join(prompt_parts)


def _album_art_mime_type(file_path: str) -> str:
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".png":
        return "image/png"
    if extension == ".webp":
        return "image/webp"
    return "image/jpeg"


@router.get("", response_model=List[AlbumRead])
def list_albums(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AlbumRead]:
    return (
        db.query(Album)
        .options(joinedload(Album.songs))
        .filter(Album.user_id == current_user.id)
        .order_by(Album.created_at.desc())
        .all()
    )


@router.post("", response_model=AlbumRead, status_code=status.HTTP_201_CREATED)
def create_album(
    payload: AlbumCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlbumRead:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Album name is required")

    album = Album(
        name=name,
        description=_clean_optional_text(payload.description),
        art_prompt_direction=_clean_optional_text(payload.art_prompt_direction),
        user_id=current_user.id,
    )
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


@router.get("/{album_id}", response_model=AlbumRead)
def get_album(
    album_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlbumRead:
    return _get_user_album(db, current_user, album_id)


@router.patch("/{album_id}", response_model=AlbumRead)
def update_album(
    album_id: int,
    payload: AlbumUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlbumRead:
    album = _get_user_album(db, current_user, album_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        name = (update_data.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Album name is required")
        album.name = name

    if "description" in update_data:
        album.description = _clean_optional_text(update_data.get("description"))

    if "art_prompt_direction" in update_data:
        album.art_prompt_direction = _clean_optional_text(update_data.get("art_prompt_direction"))

    db.add(album)
    db.commit()
    db.refresh(album)
    return album


@router.post("/{album_id}/generate-art", response_model=AlbumRead)
def generate_album_cover_art(
    album_id: int,
    payload: AlbumArtGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlbumRead:
    album = _get_user_album(db, current_user, album_id)
    prompt_direction = _clean_optional_text(payload.art_prompt_direction)

    if payload.art_prompt_direction is not None:
        album.art_prompt_direction = prompt_direction

    album_date = album.created_at.strftime("%Y-%m-%d") if album.created_at else datetime.utcnow().strftime("%Y-%m-%d")
    storage = get_album_storage_info(album.name, album.id, date=album_date)
    os.makedirs(storage["abs_folder"], exist_ok=True)

    artwork_prompt = _build_album_art_request(album, prompt_direction=prompt_direction)
    filename_suffix = f"_art_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    artwork_path = generate_artwork_from_prompt(
        artwork_prompt,
        storage["abs_image_base"],
        filename_suffix=filename_suffix,
    )

    if not artwork_path:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Album art generation failed.",
        )

    album.album_art = artwork_path
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


@router.post("/{album_id}/upload-art", response_model=AlbumRead)
async def upload_album_art(
    album_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlbumRead:
    album = _get_user_album(db, current_user, album_id)

    allowed_types = {"image/jpeg", "image/png"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPEG or PNG files are supported.")

    filename = file.filename or ""
    extension = ""
    if filename and "." in filename:
        extension = f".{filename.rsplit('.', 1)[-1].lower()}"

    if extension not in {".jpg", ".jpeg", ".png"}:
        extension = ".jpg" if file.content_type == "image/jpeg" else ".png"

    album_date = album.created_at.strftime("%Y-%m-%d") if album.created_at else datetime.utcnow().strftime("%Y-%m-%d")
    storage = get_album_storage_info(album.name, album.id, date=album_date)
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
            detail="Failed to save uploaded album art.",
        ) from exc

    album.album_art = file_path_rel
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(
    album_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete an album. Songs within it are preserved (album_id becomes NULL)."""
    album = _get_user_album(db, current_user, album_id)
    db.delete(album)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
