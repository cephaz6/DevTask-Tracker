from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
from collections import defaultdict

router = APIRouter()

# Track connections per task_id
active_connections: Dict[str, List[WebSocket]] = defaultdict(list)

@router.websocket("/ws/comments/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    active_connections[task_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection open
    except WebSocketDisconnect:
        active_connections[task_id].remove(websocket)
