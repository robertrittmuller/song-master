from typing import List

from fastapi import APIRouter, Depends

from backend.app.db.deps import get_current_user
from backend.app.models import User
from backend.shared.helpers import get_default_lyric_tags

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=List[str])
def get_tags(current_user: User = Depends(get_current_user)) -> List[str]:
    """Get lyric block tags parsed from tags/default-tags.txt."""
    del current_user
    return get_default_lyric_tags()
