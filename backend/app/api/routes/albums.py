from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from backend.app.db.deps import get_db
from backend.app.models import Album
from backend.app.schemas import AlbumCreate, AlbumRead

router = APIRouter(prefix="/api/albums", tags=["albums"])


@router.get("", response_model=List[AlbumRead])
def list_albums(db: Session = Depends(get_db)) -> List[AlbumRead]:
    return db.query(Album).options(joinedload(Album.songs)).order_by(Album.created_at.desc()).all()


@router.post("", response_model=AlbumRead, status_code=status.HTTP_201_CREATED)
def create_album(payload: AlbumCreate, db: Session = Depends(get_db)) -> AlbumRead:
    album = Album(name=payload.name, description=payload.description)
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


@router.get("/{album_id}", response_model=AlbumRead)
def get_album(album_id: int, db: Session = Depends(get_db)) -> AlbumRead:
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    return album


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(album_id: int, db: Session = Depends(get_db)) -> Response:
    """Delete an album. Songs within it are preserved (album_id becomes NULL)."""
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    db.delete(album)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
