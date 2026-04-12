import hashlib
import io
import json
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from sqlalchemy import DateTime as SQLADateTime
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from backend.app.models import Album, GenerationSession, Song, SongFile, SongVersion, User, UserSetting
from backend.app.schemas.backups import BackupRestoreResult
from backend.shared.helpers import get_repo_root

BACKUP_SCHEMA_VERSION = 1
ASSET_PREFIX = "assets/"
DATA_ENTRY = "data.json"
MANIFEST_ENTRY = "manifest.json"
USER_CONTENT_DIRECTORIES = ("songs", "personas")

EXPORT_MODELS: Tuple[Type[Any], ...] = (
    User,
    Album,
    Song,
    SongVersion,
    SongFile,
    GenerationSession,
    UserSetting,
)


def create_backup_zip(db: Session) -> io.BytesIO:
    """Create a complete account-wide backup ZIP in memory.

    The archive contains database rows in JSON plus all files referenced by song
    records and files stored under user-content asset directories.
    """
    data = _dump_database(db)
    asset_paths = _collect_asset_paths(db)
    manifest_files = []
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative_path in asset_paths:
            absolute_path = _resolve_repo_asset(relative_path)
            if not absolute_path or not absolute_path.is_file():
                continue

            checksum = _sha256_file(absolute_path)
            size = absolute_path.stat().st_size
            archive.write(absolute_path, f"{ASSET_PREFIX}{relative_path}")
            manifest_files.append({"path": relative_path, "sha256": checksum, "size": size})

        manifest = {
            "app": "song-master",
            "schema_version": BACKUP_SCHEMA_VERSION,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "tables": {table: len(rows) for table, rows in data.items()},
            "files": manifest_files,
        }
        archive.writestr(MANIFEST_ENTRY, json.dumps(manifest, indent=2, sort_keys=True))
        archive.writestr(DATA_ENTRY, json.dumps(data, indent=2, sort_keys=True))

    buffer.seek(0)
    return buffer


def restore_backup_zip(db: Session, raw_zip: bytes, dry_run: bool = False) -> BackupRestoreResult:
    """Restore a Song Master backup while skipping provable duplicates."""
    result = BackupRestoreResult(dry_run=dry_run)
    asset_path_map: Dict[str, str] = {}

    try:
        with zipfile.ZipFile(io.BytesIO(raw_zip), "r") as archive:
            _validate_archive(archive)
            manifest = json.loads(archive.read(MANIFEST_ENTRY).decode("utf-8"))
            if manifest.get("schema_version") != BACKUP_SCHEMA_VERSION:
                raise ValueError("Unsupported backup schema version.")

            data = json.loads(archive.read(DATA_ENTRY).decode("utf-8"))
            user_map = _restore_users(db, data.get("users", []), result, dry_run)
            album_map = _restore_albums(db, data.get("albums", []), user_map, result, dry_run)
            song_map = _restore_songs(
                db,
                data.get("songs", []),
                album_map,
                archive,
                asset_path_map,
                result,
                dry_run,
            )
            _restore_song_versions(db, data.get("song_versions", []), song_map, result, dry_run)
            _restore_song_files(
                db,
                data.get("song_files", []),
                song_map,
                archive,
                asset_path_map,
                result,
                dry_run,
            )
            _restore_generation_sessions(db, data.get("generation_sessions", []), song_map, result, dry_run)
            _restore_user_settings(db, data.get("user_settings", []), user_map, result, dry_run)
            _restore_unreferenced_assets(archive, asset_path_map, result, dry_run)

        if dry_run:
            db.rollback()
        else:
            db.commit()
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        db.rollback()
        raise ValueError(f"Invalid or unrestorable backup: {exc}") from exc

    return result


def _dump_database(db: Session) -> Dict[str, List[Dict[str, Any]]]:
    data: Dict[str, List[Dict[str, Any]]] = {}
    for model in EXPORT_MODELS:
        mapper = inspect(model)
        rows = []
        for record in db.query(model).order_by(model.id).all():
            row = {}
            for attribute in mapper.column_attrs:
                value = getattr(record, attribute.key)
                row[attribute.key] = _serialize_value(value)
            rows.append(row)
        data[model.__tablename__] = rows
    return data


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value[:-1] if value.endswith("Z") else value
    return datetime.fromisoformat(normalized)


def _collect_asset_paths(db: Session) -> List[str]:
    paths = set()

    for (album_art,) in db.query(Song.album_art).filter(Song.album_art.isnot(None)).all():
        safe_path = _safe_relative_path(album_art)
        if safe_path and _is_user_content_path(safe_path):
            paths.add(safe_path)

    for (file_path,) in db.query(SongFile.file_path).all():
        safe_path = _safe_relative_path(file_path)
        if safe_path and _is_user_content_path(safe_path):
            paths.add(safe_path)

    for directory in USER_CONTENT_DIRECTORIES:
        root = Path(get_repo_root()) / directory
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                paths.add(path.relative_to(get_repo_root()).as_posix())

    return sorted(paths)


def _safe_relative_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    pure_path = PurePosixPath(str(path).replace("\\", "/"))
    if pure_path.is_absolute() or ".." in pure_path.parts:
        return None
    return pure_path.as_posix()


def _is_user_content_path(path: str) -> bool:
    return PurePosixPath(path).parts[:1] in [(directory,) for directory in USER_CONTENT_DIRECTORIES]


def _resolve_repo_asset(relative_path: str) -> Optional[Path]:
    safe_path = _safe_relative_path(relative_path)
    if not safe_path:
        return None

    repo_root = Path(get_repo_root()).resolve()
    resolved = (repo_root / safe_path).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError:
        return None
    return resolved


def _validate_archive(archive: zipfile.ZipFile) -> None:
    names = set(archive.namelist())
    if MANIFEST_ENTRY not in names or DATA_ENTRY not in names:
        raise ValueError("Backup ZIP must contain manifest.json and data.json.")

    for name in names:
        pure_path = PurePosixPath(name)
        if pure_path.is_absolute() or ".." in pure_path.parts:
            raise ValueError(f"Unsafe archive path: {name}")


def _restore_asset(
    archive: zipfile.ZipFile,
    original_path: Optional[str],
    asset_path_map: Dict[str, str],
    result: BackupRestoreResult,
    dry_run: bool,
) -> Optional[str]:
    safe_path = _safe_relative_path(original_path)
    if not safe_path:
        return original_path
    if not _is_user_content_path(safe_path):
        asset_path_map[safe_path] = safe_path
        return safe_path

    if safe_path in asset_path_map:
        return asset_path_map[safe_path]

    archive_name = f"{ASSET_PREFIX}{safe_path}"
    if archive_name not in archive.namelist():
        result.warnings.append(f"Backup is missing asset file: {safe_path}")
        asset_path_map[safe_path] = safe_path
        return safe_path

    backup_bytes = archive.read(archive_name)
    backup_checksum = _sha256_bytes(backup_bytes)
    destination = _resolve_repo_asset(safe_path)
    if destination is None:
        result.warnings.append(f"Skipped unsafe asset path: {safe_path}")
        asset_path_map[safe_path] = safe_path
        return safe_path

    final_path = destination
    final_relative_path = safe_path
    if destination.exists():
        existing_checksum = _sha256_file(destination)
        if existing_checksum == backup_checksum:
            result.skipped_files += 1
            asset_path_map[safe_path] = safe_path
            return safe_path

        final_path, final_relative_path = _unique_restore_path(destination)

    result.restored_files += 1
    asset_path_map[safe_path] = final_relative_path
    if dry_run:
        return final_relative_path

    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_bytes(backup_bytes)
    return final_relative_path


def _unique_restore_path(destination: Path) -> Tuple[Path, str]:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    candidate = destination.with_name(f"{destination.stem}_restored_{timestamp}{destination.suffix}")
    counter = 1
    while candidate.exists():
        candidate = destination.with_name(
            f"{destination.stem}_restored_{timestamp}_{counter}{destination.suffix}"
        )
        counter += 1

    repo_root = Path(get_repo_root()).resolve()
    return candidate, candidate.resolve().relative_to(repo_root).as_posix()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _increment(result: BackupRestoreResult, bucket: str, table: str) -> None:
    values = getattr(result, bucket)
    values[table] = values.get(table, 0) + 1


def _row_kwargs(model: Type[Any], row: Dict[str, Any], excluded: Iterable[str]) -> Dict[str, Any]:
    mapper = inspect(model)
    excluded_set = set(excluded)
    kwargs = {}
    for attribute in mapper.column_attrs:
        if attribute.key in excluded_set or attribute.key not in row:
            continue

        column = attribute.columns[0]
        value = row[attribute.key]
        if value is not None and isinstance(column.type, SQLADateTime):
            value = _parse_datetime(value)
        kwargs[attribute.key] = value
    return kwargs


def _song_fingerprint_from_values(
    title: Optional[str],
    user_prompt: Optional[str],
    lyrics: Optional[str],
    clean_lyrics: Optional[str],
) -> str:
    payload = {
        "title": title or "",
        "user_prompt": user_prompt or "",
        "lyrics": lyrics or "",
        "clean_lyrics": clean_lyrics or "",
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _song_fingerprint(song: Song) -> str:
    return _song_fingerprint_from_values(song.title, song.user_prompt, song.lyrics, song.clean_lyrics)


def _restore_users(
    db: Session,
    rows: List[Dict[str, Any]],
    result: BackupRestoreResult,
    dry_run: bool,
) -> Dict[int, int]:
    id_map: Dict[int, int] = {}
    existing_users = db.query(User).all()

    for row in rows:
        old_id = row["id"]
        existing = next(
            (
                user
                for user in existing_users
                if user.username == row.get("username") or user.email == row.get("email")
            ),
            None,
        )
        if existing:
            id_map[old_id] = existing.id
            _increment(result, "skipped", "users")
            continue

        if dry_run:
            id_map[old_id] = old_id
            _increment(result, "imported", "users")
            continue

        user = User(**_row_kwargs(User, row, excluded={"id"}))
        db.add(user)
        db.flush()
        existing_users.append(user)
        id_map[old_id] = user.id
        _increment(result, "imported", "users")

    return id_map


def _restore_albums(
    db: Session,
    rows: List[Dict[str, Any]],
    user_map: Dict[int, int],
    result: BackupRestoreResult,
    dry_run: bool,
) -> Dict[int, int]:
    id_map: Dict[int, int] = {}
    existing_albums = db.query(Album).all()

    for row in rows:
        old_id = row["id"]
        mapped_user_id = _mapped_optional_id(row.get("user_id"), user_map)
        existing = next(
            (
                album
                for album in existing_albums
                if album.user_id == mapped_user_id and album.name == row.get("name")
            ),
            None,
        )
        if existing:
            id_map[old_id] = existing.id
            _increment(result, "skipped", "albums")
            continue

        if dry_run:
            id_map[old_id] = old_id
            _increment(result, "imported", "albums")
            continue

        kwargs = _row_kwargs(Album, row, excluded={"id", "user_id"})
        kwargs["user_id"] = mapped_user_id
        album = Album(**kwargs)
        db.add(album)
        db.flush()
        existing_albums.append(album)
        id_map[old_id] = album.id
        _increment(result, "imported", "albums")

    return id_map


def _restore_songs(
    db: Session,
    rows: List[Dict[str, Any]],
    album_map: Dict[int, int],
    archive: zipfile.ZipFile,
    asset_path_map: Dict[str, str],
    result: BackupRestoreResult,
    dry_run: bool,
) -> Dict[int, int]:
    id_map: Dict[int, int] = {}
    existing_fingerprints = {_song_fingerprint(song): song for song in db.query(Song).all()}

    for row in rows:
        old_id = row["id"]
        fingerprint = _song_fingerprint_from_values(
            row.get("title"),
            row.get("user_prompt"),
            row.get("lyrics"),
            row.get("clean_lyrics"),
        )
        existing = existing_fingerprints.get(fingerprint)
        if existing:
            id_map[old_id] = existing.id
            if row.get("album_art") and not existing.album_art:
                restored_path = _restore_asset(archive, row.get("album_art"), asset_path_map, result, dry_run)
                if not dry_run:
                    existing.album_art = restored_path
                    db.add(existing)
            _increment(result, "skipped", "songs")
            continue

        restored_album_art = _restore_asset(archive, row.get("album_art"), asset_path_map, result, dry_run)
        mapped_album_id = _mapped_optional_id(row.get("album_id"), album_map)
        if dry_run:
            id_map[old_id] = old_id
            _increment(result, "imported", "songs")
            continue

        kwargs = _row_kwargs(Song, row, excluded={"id", "album_id", "album_art"})
        kwargs["album_id"] = mapped_album_id
        kwargs["album_art"] = restored_album_art
        song = Song(**kwargs)
        db.add(song)
        db.flush()
        existing_fingerprints[fingerprint] = song
        id_map[old_id] = song.id
        _increment(result, "imported", "songs")

    return id_map


def _restore_song_versions(
    db: Session,
    rows: List[Dict[str, Any]],
    song_map: Dict[int, int],
    result: BackupRestoreResult,
    dry_run: bool,
) -> None:
    versions_by_song = defaultdict(list)
    for version in db.query(SongVersion).all():
        versions_by_song[version.song_id].append(version)

    for row in rows:
        mapped_song_id = song_map.get(row.get("song_id"))
        if not mapped_song_id:
            result.warnings.append(f"Skipped song version for missing song id {row.get('song_id')}.")
            _increment(result, "skipped", "song_versions")
            continue

        existing_versions = versions_by_song[mapped_song_id]
        duplicate = next(
            (
                version
                for version in existing_versions
                if version.version_number == row.get("version_number") and version.lyrics == row.get("lyrics")
            ),
            None,
        )
        if duplicate:
            _increment(result, "skipped", "song_versions")
            continue

        if dry_run:
            _increment(result, "imported", "song_versions")
            continue

        version_number = row.get("version_number")
        if any(version.version_number == version_number for version in existing_versions):
            version_number = max(version.version_number for version in existing_versions) + 1

        kwargs = _row_kwargs(SongVersion, row, excluded={"id", "song_id", "version_number"})
        kwargs["song_id"] = mapped_song_id
        kwargs["version_number"] = version_number
        version = SongVersion(**kwargs)
        db.add(version)
        db.flush()
        existing_versions.append(version)
        _increment(result, "imported", "song_versions")


def _restore_song_files(
    db: Session,
    rows: List[Dict[str, Any]],
    song_map: Dict[int, int],
    archive: zipfile.ZipFile,
    asset_path_map: Dict[str, str],
    result: BackupRestoreResult,
    dry_run: bool,
) -> None:
    files_by_song = defaultdict(list)
    for song_file in db.query(SongFile).all():
        files_by_song[song_file.song_id].append(song_file)

    for row in rows:
        mapped_song_id = song_map.get(row.get("song_id"))
        if not mapped_song_id:
            result.warnings.append(f"Skipped file for missing song id {row.get('song_id')}.")
            _increment(result, "skipped", "song_files")
            continue

        restored_path = _restore_asset(archive, row.get("file_path"), asset_path_map, result, dry_run)
        checksum = row.get("checksum") or _backup_asset_checksum(archive, row.get("file_path"))
        existing_files = files_by_song[mapped_song_id]
        duplicate = next(
            (
                song_file
                for song_file in existing_files
                if song_file.file_type == row.get("file_type")
                and ((checksum and song_file.checksum == checksum) or song_file.file_path == restored_path)
            ),
            None,
        )
        if duplicate:
            _increment(result, "skipped", "song_files")
            continue

        if dry_run:
            _increment(result, "imported", "song_files")
            continue

        kwargs = _row_kwargs(SongFile, row, excluded={"id", "song_id", "file_path", "file_name", "checksum"})
        kwargs["song_id"] = mapped_song_id
        kwargs["file_path"] = restored_path
        kwargs["file_name"] = Path(restored_path or row.get("file_name", "")).name
        kwargs["checksum"] = checksum

        absolute_path = _resolve_repo_asset(restored_path or "")
        if absolute_path and absolute_path.exists():
            kwargs["file_size"] = absolute_path.stat().st_size

        song_file = SongFile(**kwargs)
        db.add(song_file)
        db.flush()
        existing_files.append(song_file)
        _increment(result, "imported", "song_files")


def _restore_generation_sessions(
    db: Session,
    rows: List[Dict[str, Any]],
    song_map: Dict[int, int],
    result: BackupRestoreResult,
    dry_run: bool,
) -> None:
    existing_session_ids = {session_id for (session_id,) in db.query(GenerationSession.session_id).all()}

    for row in rows:
        mapped_song_id = song_map.get(row.get("song_id"))
        if not mapped_song_id or row.get("session_id") in existing_session_ids:
            _increment(result, "skipped", "generation_sessions")
            continue

        if dry_run:
            _increment(result, "imported", "generation_sessions")
            continue

        kwargs = _row_kwargs(GenerationSession, row, excluded={"id", "song_id"})
        kwargs["song_id"] = mapped_song_id
        session = GenerationSession(**kwargs)
        db.add(session)
        db.flush()
        existing_session_ids.add(session.session_id)
        _increment(result, "imported", "generation_sessions")


def _restore_user_settings(
    db: Session,
    rows: List[Dict[str, Any]],
    user_map: Dict[int, int],
    result: BackupRestoreResult,
    dry_run: bool,
) -> None:
    existing_settings = db.query(UserSetting).all()

    for row in rows:
        mapped_user_id = user_map.get(row.get("user_id"))
        if not mapped_user_id:
            result.warnings.append(f"Skipped setting for missing user id {row.get('user_id')}.")
            _increment(result, "skipped", "user_settings")
            continue

        existing = next(
            (
                setting
                for setting in existing_settings
                if setting.user_id == mapped_user_id
                and setting.key == row.get("key")
                and setting.category == row.get("category")
            ),
            None,
        )
        if existing:
            _increment(result, "skipped", "user_settings")
            continue

        if dry_run:
            _increment(result, "imported", "user_settings")
            continue

        kwargs = _row_kwargs(UserSetting, row, excluded={"id", "user_id"})
        kwargs["user_id"] = mapped_user_id
        setting = UserSetting(**kwargs)
        db.add(setting)
        db.flush()
        existing_settings.append(setting)
        _increment(result, "imported", "user_settings")


def _backup_asset_checksum(archive: zipfile.ZipFile, path: Optional[str]) -> Optional[str]:
    safe_path = _safe_relative_path(path)
    if not safe_path:
        return None
    archive_name = f"{ASSET_PREFIX}{safe_path}"
    if archive_name not in archive.namelist():
        return None
    return _sha256_bytes(archive.read(archive_name))


def _restore_unreferenced_assets(
    archive: zipfile.ZipFile,
    asset_path_map: Dict[str, str],
    result: BackupRestoreResult,
    dry_run: bool,
) -> None:
    for name in archive.namelist():
        if not name.startswith(ASSET_PREFIX) or name == ASSET_PREFIX:
            continue
        relative_path = name[len(ASSET_PREFIX):]
        _restore_asset(archive, relative_path, asset_path_map, result, dry_run)


def _mapped_optional_id(value: Optional[int], id_map: Dict[int, int]) -> Optional[int]:
    if value is None:
        return None
    return id_map.get(value)
