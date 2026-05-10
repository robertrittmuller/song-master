import json
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends

from backend.app.db.deps import get_current_user
from backend.app.models import User

router = APIRouter(prefix="/api/styles", tags=["styles"])


def load_styles() -> List[str]:
    """Load core styles from styles.json file."""
    styles_path = Path(__file__).parent.parent.parent.parent.parent / "styles" / "styles.json"
    with open(styles_path, "r") as f:
        data = json.load(f)
        styles = data.get("core_styles", [])
        return sorted(styles)


@router.get("", response_model=List[str])
def get_styles(current_user: User = Depends(get_current_user)) -> List[str]:
    """Get list of available core styles."""
    del current_user
    return load_styles()
