from fastapi import APIRouter, Depends

from backend.app.db.deps import get_current_user
from backend.app.models import User
from backend.app.schemas import SettingsResponse
from backend.app.services.settings_service import get_settings_payload

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def read_settings(current_user: User = Depends(get_current_user)) -> SettingsResponse:
    del current_user
    return get_settings_payload()
