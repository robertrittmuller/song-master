from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import get_settings
from backend.app.db.base import Base

settings = get_settings()

connect_args = {}
if settings.database_url.startswith("sqlite"):
    # SQLite needs the check_same_thread flag disabled when used with async tasks
    connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=connect_args)

if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def cleanup_song_integrity() -> None:
    """Remove stale child rows left behind by prior SQLite deletes or ID reuse."""
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM song_versions WHERE song_id NOT IN (SELECT id FROM songs)")
        )
        connection.execute(
            text("DELETE FROM song_files WHERE song_id NOT IN (SELECT id FROM songs)")
        )
        connection.execute(
            text(
                """
                DELETE FROM song_versions
                WHERE EXISTS (
                    SELECT 1
                    FROM songs
                    WHERE songs.id = song_versions.song_id
                      AND songs.created_at IS NOT NULL
                      AND song_versions.created_at < songs.created_at
                )
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM song_files
                WHERE EXISTS (
                    SELECT 1
                    FROM songs
                    WHERE songs.id = song_files.song_id
                      AND songs.created_at IS NOT NULL
                      AND song_files.created_at < songs.created_at
                )
                """
            )
        )


def init_db() -> None:
    """Create database tables on startup."""
    import backend.app.models  # noqa: F401 - ensures model metadata is registered

    Base.metadata.create_all(bind=engine)
    cleanup_song_integrity()
