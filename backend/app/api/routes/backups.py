from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.deps import get_db
from backend.app.schemas.backups import BackupRestoreResult
from backend.app.services.backup_service import create_backup_zip, restore_backup_zip

router = APIRouter(prefix="/api/backups", tags=["backups"])


@router.get("/export")
def export_backup(db: Session = Depends(get_db)) -> StreamingResponse:
    """Download a ZIP backup containing all database rows and content files."""
    buffer = create_backup_zip(db)
    filename = f"song-master-backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore", response_model=BackupRestoreResult)
async def restore_backup(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> BackupRestoreResult:
    """Restore a ZIP backup, creating missing records and skipping duplicates."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .zip backup files are supported.",
        )

    raw_zip = await file.read()
    try:
        return restore_backup_zip(db, raw_zip, dry_run=dry_run)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
