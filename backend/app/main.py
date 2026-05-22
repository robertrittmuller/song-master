from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.app.api.routes import (
    albums,
    auth,
    backups,
    health,
    instruments,
    personas,
    settings as settings_routes,
    song_proposals,
    songs,
    styles,
)
from backend.app.core.config import get_settings
from backend.app.db.database import init_db
from backend.app.services.demo_track_generator import demo_track_generation_manager
from backend.app.websocket import progress as progress_ws
from backend.app.services.song_generator import generation_manager

app_settings = get_settings()

app = FastAPI(title=app_settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_origin_regex=app_settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    # Ensure songs and images directories exist
    for d in ["songs", "images"]:
        Path(d).mkdir(exist_ok=True)

@app.on_event("shutdown")
async def on_shutdown() -> None:
    await demo_track_generation_manager.shutdown()
    await generation_manager.shutdown()


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(albums.router)
app.include_router(backups.router)
app.include_router(song_proposals.router)
app.include_router(songs.router)
app.include_router(personas.router)
app.include_router(settings_routes.router)
app.include_router(styles.router)
app.include_router(instruments.router)
app.include_router(progress_ws.router)

storage_root = Path(__file__).parent.parent.parent

# Mount static files for album art and other song assets.
# Legacy album records may point at /images/albums even though album cover files
# are stored with the rest of the song assets under songs/albums.
app.mount("/images/albums", StaticFiles(directory=str(storage_root / "songs" / "albums")), name="album-images")
app.mount("/songs", StaticFiles(directory=str(storage_root / "songs")), name="songs")
app.mount("/images", StaticFiles(directory=str(storage_root / "images")), name="images")
