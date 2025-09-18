"""WebSocket handler for real-time chat functionality."""

import json
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, List
import asyncio

from app.config.database import get_database
from app.schemas.chat import ChatMessageRequest
from app.services.chat_service import chat_service


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        # conversation_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: str):
        """Accept a WebSocket connection."""
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, conversation_id: str):
        """Remove a WebSocket connection."""
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def broadcast_to_conversation(self, message: str, conversation_id: str):
        """Broadcast a message to all connections in a conversation."""
        if conversation_id in self.active_connections:
            connections = self.active_connections[conversation_id].copy()
            for connection in connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Error broadcasting message: {e}")
                    # Remove broken connection
                    self.disconnect(connection, conversation_id)


# Global connection manager
manager = ConnectionManager()


async def websocket_chat_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    db: Session = Depends(get_database)
):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket, conversation_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse message data
                message_data = json.loads(data)
                
                # Create chat request
                chat_request = ChatMessageRequest(
                    message=message_data.get("message", ""),
                    conversation_id=conversation_id,
                    provider=message_data.get("provider", "openai"),
                    model=message_data.get("model"),
                    temperature=message_data.get("temperature", 0.7),
                    max_tokens=message_data.get("max_tokens", 1000),
                    stream=True
                )
                
                # Send acknowledgment
                await manager.send_personal_message(
                    json.dumps({
                        "type": "message_received",
                        "status": "processing"
                    }),
                    websocket
                )
                
                # Stream response
                full_response = ""
                async for chunk_data in chat_service.stream_message(chat_request, db):
                    # Send chunk to client
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "chunk",
                            **chunk_data
                        }),
                        websocket
                    )
                    
                    if not chunk_data.get("is_complete", False):
                        full_response += chunk_data.get("content", "")
                    
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)
                
                # Send completion message
                await manager.send_personal_message(
                    json.dumps({
                        "type": "message_complete",
                        "full_response": full_response,
                        "conversation_id": conversation_id
                    }),
                    websocket
                )
                
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }),
                    websocket
                )
            except Exception as e:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": f"Processing error: {str(e)}"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, conversation_id)