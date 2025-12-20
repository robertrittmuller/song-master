import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.services.song_generator import generation_manager

router = APIRouter()


@router.websocket("/ws/songs/{song_id}/progress")
async def song_progress(websocket: WebSocket, song_id: int) -> None:
    await websocket.accept()
    try:
        while True:
            status = generation_manager.get_status(song_id)
            if status:
                await websocket.send_json(status.model_dump(mode="json"))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return
