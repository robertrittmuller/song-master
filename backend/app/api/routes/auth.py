from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.deps import get_current_user, get_db
from backend.app.models import User
from backend.app.schemas import (
    AuthMessageResponse,
    AuthTokenResponse,
    AuthUserRead,
    ChangePasswordRequest,
    LoginRequest,
    SignUpRequest,
)
from backend.app.services.auth_service import (
    authenticate_user,
    build_auth_response,
    change_password,
    create_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def sign_up(payload: SignUpRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    user = create_user(db, payload.username, payload.email, payload.password)
    return build_auth_response(user)


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    user = authenticate_user(db, payload.identifier, payload.password)
    return build_auth_response(user)


@router.get("/me", response_model=AuthUserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> AuthUserRead:
    return AuthUserRead.model_validate(current_user)


@router.post("/change-password", response_model=AuthMessageResponse)
def update_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuthMessageResponse:
    change_password(db, current_user, payload.current_password, payload.new_password)
    return AuthMessageResponse(message="Password updated successfully")