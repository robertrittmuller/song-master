from typing import List
from fastapi import APIRouter, Depends

from backend.app.db.deps import get_current_user
from backend.app.models import User
from backend.shared.helpers import get_instrument_tags

router = APIRouter(prefix="/api/instruments", tags=["instruments"])


@router.get("", response_model=List[str])
def get_instruments(current_user: User = Depends(get_current_user)) -> List[str]:
    """Get list of available instrument tags parsed from default-tags.txt."""
    del current_user
    return get_instrument_tags()
