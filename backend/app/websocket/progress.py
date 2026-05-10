import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.db.database import SessionLocal
from backend.app.db.deps import resolve_user_from_token
from backend.app.models import Song
from backend.app.services.song_generator import generation_manager

router = APIRouter()


@router.websocket("/ws/songs/{song_id}/progress")
async def song_progress(websocket: WebSocket, song_id: int) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    session = SessionLocal()
    try:
        user = resolve_user_from_token(session, token)
        song = session.query(Song).filter(Song.id == song_id, Song.user_id == user.id).first()
        if not song:
            await websocket.close(code=1008)
            return
    except Exception:
        session.close()
        await websocket.close(code=1008)
        return
    finally:
        session.close()

    await websocket.accept()
    try:
        while True:
            status = generation_manager.get_status(song_id)
            if status:
                await websocket.send_json(status.model_dump(mode="json"))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return
