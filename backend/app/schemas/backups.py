from typing import Dict, List

from pydantic import BaseModel, Field


class BackupRestoreResult(BaseModel):
    """Summary returned after restoring a Song Master backup."""

    dry_run: bool = False
    imported: Dict[str, int] = Field(default_factory=dict)
    skipped: Dict[str, int] = Field(default_factory=dict)
    restored_files: int = 0
    skipped_files: int = 0
    warnings: List[str] = Field(default_factory=list)
