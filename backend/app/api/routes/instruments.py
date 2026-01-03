from typing import List
from fastapi import APIRouter
from helpers import get_instrument_tags

router = APIRouter(prefix="/api/instruments", tags=["instruments"])


@router.get("", response_model=List[str])
def get_instruments() -> List[str]:
    """Get list of available instrument tags parsed from default-tags.txt."""
    return get_instrument_tags()
