import json
from pathlib import Path
from typing import List

from fastapi import APIRouter

router = APIRouter(prefix="/api/styles", tags=["styles"])


def load_styles() -> List[str]:
    """Load core styles from styles.json file."""
    styles_path = Path(__file__).parent.parent.parent.parent.parent / "styles" / "styles.json"
    with open(styles_path, "r") as f:
        data = json.load(f)
        return data.get("core_styles", [])


@router.get("", response_model=List[str])
def get_styles() -> List[str]:
    """Get list of available core styles."""
    return load_styles()
