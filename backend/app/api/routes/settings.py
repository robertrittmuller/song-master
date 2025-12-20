from fastapi import APIRouter

from backend.app.schemas import SettingsResponse
from backend.app.services.settings_service import get_settings_payload

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def read_settings() -> SettingsResponse:
    return get_settings_payload()
