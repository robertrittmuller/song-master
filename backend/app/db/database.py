from sqlalchemy import create_engine, event, inspect, text
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
    _ensure_song_proposal_schema()
    _ensure_auth_schema()
    cleanup_song_integrity()


def _ensure_song_proposal_schema() -> None:
    inspector = inspect(engine)
    if "song_proposals" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("song_proposals")}
    with engine.begin() as connection:
        if "status" not in existing_columns:
            connection.execute(
                text("ALTER TABLE song_proposals ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'open'")
            )
        if "accepted_at" not in existing_columns:
            connection.execute(text("ALTER TABLE song_proposals ADD COLUMN accepted_at DATETIME"))
        connection.execute(text("UPDATE song_proposals SET status = 'open' WHERE status IS NULL"))


def _ensure_auth_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        if "songs" in table_names:
            song_columns = {column["name"] for column in inspector.get_columns("songs")}
            if "user_id" not in song_columns:
                connection.execute(
                    text(
                        "ALTER TABLE songs ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"
                    )
                )
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_songs_user_id ON songs(user_id)"))

        if "song_proposals" in table_names:
            proposal_columns = {column["name"] for column in inspector.get_columns("song_proposals")}
            if "user_id" not in proposal_columns:
                connection.execute(
                    text(
                        "ALTER TABLE song_proposals ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"
                    )
                )
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS idx_song_proposals_user_id ON song_proposals(user_id)")
            )

        if "albums" in table_names:
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_albums_user_id ON albums(user_id)"))

        if "songs" in table_names and "albums" in table_names:
            connection.execute(
                text(
                    """
                    UPDATE songs
                    SET user_id = (
                        SELECT albums.user_id
                        FROM albums
                        WHERE albums.id = songs.album_id
                    )
                    WHERE user_id IS NULL
                      AND album_id IS NOT NULL
                      AND EXISTS (
                          SELECT 1
                          FROM albums
                          WHERE albums.id = songs.album_id
                            AND albums.user_id IS NOT NULL
                      )
                    """
                )
            )
