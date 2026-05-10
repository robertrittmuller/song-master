from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash, verify_password
from backend.app.models import Album, Song, SongProposal, User
from backend.app.schemas.auth import AuthTokenResponse, AuthUserRead


def _normalize_identifier(identifier: str) -> str:
    return identifier.strip().lower()


def get_user_by_identifier(db: Session, identifier: str) -> Optional[User]:
    normalized = _normalize_identifier(identifier)
    return (
        db.query(User)
        .filter(
            or_(
                func.lower(User.username) == normalized,
                func.lower(User.email) == normalized,
            )
        )
        .first()
    )


def _password_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def validate_new_password(password: str) -> None:
    if len(password) < 8:
        raise _password_error("Password must be at least 8 characters long")
    if password.isdigit() or password.isalpha():
        raise _password_error("Password must include a mix of letters or symbols and numbers")


def _ensure_unique_user(db: Session, username: str, email: str) -> None:
    normalized_username = username.strip().lower()
    normalized_email = email.strip().lower()

    existing = (
        db.query(User)
        .filter(
            or_(
                func.lower(User.username) == normalized_username,
                func.lower(User.email) == normalized_email,
            )
        )
        .first()
    )
    if not existing:
        return

    if existing.username.lower() == normalized_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already in use")
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already in use")


def claim_orphaned_content_for_user(db: Session, user: User) -> None:
    db.query(Album).filter(Album.user_id.is_(None)).update(
        {Album.user_id: user.id},
        synchronize_session=False,
    )
    db.query(Song).filter(Song.user_id.is_(None)).update(
        {Song.user_id: user.id},
        synchronize_session=False,
    )
    db.query(SongProposal).filter(SongProposal.user_id.is_(None)).update(
        {SongProposal.user_id: user.id},
        synchronize_session=False,
    )


def create_user(db: Session, username: str, email: str, password: str) -> User:
    validate_new_password(password)
    _ensure_unique_user(db, username, email)

    is_first_user = db.query(User).count() == 0
    user = User(
        username=username.strip(),
        email=email.strip().lower(),
        password_hash=get_password_hash(password),
        is_active=True,
        last_login_at=datetime.utcnow(),
    )
    db.add(user)
    db.flush()

    if is_first_user:
        claim_orphaned_content_for_user(db, user)

    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> User:
    user = get_user_by_identifier(db, identifier)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username, email, or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive",
        )

    user.last_login_at = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def build_auth_response(user: User) -> AuthTokenResponse:
    access_token = create_access_token(str(user.id))
    return AuthTokenResponse(access_token=access_token, user=AuthUserRead.model_validate(user))


def change_password(db: Session, user: User, current_password: str, new_password: str) -> User:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    validate_new_password(new_password)
    if verify_password(new_password, user.password_hash):
        raise _password_error("New password must be different from the current password")

    user.password_hash = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user