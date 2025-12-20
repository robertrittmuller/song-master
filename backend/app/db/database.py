from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import get_settings
from backend.app.db.base import Base

settings = get_settings()

# SQLite needs the check_same_thread flag disabled when used with async tasks
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create database tables on startup."""
    import backend.app.models  # noqa: F401 - ensures model metadata is registered

    Base.metadata.create_all(bind=engine)
