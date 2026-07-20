from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import base64
import json

router = APIRouter()

# Simple face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@router.websocket("/ws/proctoring/{candidate_id}")
async def proctoring_endpoint(websocket: WebSocket, candidate_id: int):
    await manager.connect(websocket)
    integrity_score = 100
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # Expecting base64 encoded image frame
            if "frame" in payload:
                frame_data = payload["frame"].split(',')[1]
                img_bytes = base64.b64decode(frame_data)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if img is not None:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    alerts = []
                    if len(faces) == 0:
                        alerts.append("No face detected!")
                        integrity_score = max(0, integrity_score - 2)
                    elif len(faces) > 1:
                        alerts.append("Multiple persons detected!")
                        integrity_score = max(0, integrity_score - 5)
                        
                    await websocket.send_json({
                        "type": "proctor_result",
                        "alerts": alerts,
                        "integrity_score": integrity_score,
                        "faces_count": len(faces)
                    })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
