from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.app.api.routes import health, personas, projects, settings as settings_routes, songs, styles
from backend.app.core.config import get_settings
from backend.app.db.database import init_db
from backend.app.websocket import progress as progress_ws
from backend.app.services.song_generator import generation_manager

app_settings = get_settings()

app = FastAPI(title=app_settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    # Ensure songs directory exists for album art
    songs_dir = Path("songs")
    songs_dir.mkdir(exist_ok=True)

@app.on_event("shutdown")
async def on_shutdown() -> None:
    await generation_manager.shutdown()


app.include_router(health.router)
app.include_router(projects.router)
app.include_router(songs.router)
app.include_router(personas.router)
app.include_router(settings_routes.router)
app.include_router(styles.router)
app.include_router(progress_ws.router)

# Mount static files for album art and other song assets
app.mount("/songs", StaticFiles(directory="songs"), name="songs")

