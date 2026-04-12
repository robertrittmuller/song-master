from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from backend.app.db.deps import get_current_user, get_db
from backend.app.models import Album, User
from backend.app.schemas import AlbumCreate, AlbumRead

router = APIRouter(prefix="/api/albums", tags=["albums"])


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
    album = Album(name=payload.name, description=payload.description, user_id=current_user.id)
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
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    return album


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(
    album_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete an album. Songs within it are preserved (album_id becomes NULL)."""
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == current_user.id).first()
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    db.delete(album)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
