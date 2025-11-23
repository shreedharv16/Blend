"""WebSocket endpoint for real-time chat."""
from fastapi import WebSocket, WebSocketDisconnect
import json
import uuid
from typing import Dict
from app.models.schemas import AgentState, FileMetadata
from app.services.vector_service import vector_service
from app.agents.graph import run_agent_workflow
from app.utils.chunking import create_table_name
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: dict):
        """Send message to client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)


manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket):
    """Handle WebSocket connection."""
    client_id = str(uuid.uuid4())
    
    try:
        await manager.connect(websocket, client_id)
        
        # Send connection confirmation
        await manager.send_message(client_id, {
            "type": "connection",
            "client_id": client_id,
            "status": "connected"
        })
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type", "chat")
            
            if message_type == "chat":
                await handle_chat_message(client_id, message_data)
            elif message_type == "ping":
                await manager.send_message(client_id, {"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)


async def handle_chat_message(client_id: str, message_data: dict):
    """Handle chat message."""
    try:
        user_message = message_data.get("message")
        file_id = message_data.get("file_id")
        conversation_id = message_data.get("conversation_id", str(uuid.uuid4()))
        
        # Send acknowledgment
        await manager.send_message(client_id, {
            "type": "status",
            "status": "processing",
            "conversation_id": conversation_id
        })
        
        # Get file metadata if needed
        file_metadata = None
        table_name = None
        
        if file_id:
            metadata_dict = await vector_service.get_file_metadata(file_id)
            if metadata_dict:
                file_metadata = FileMetadata(**metadata_dict)
                table_name = create_table_name(file_id)
        
        # Create state
        state_dict = {
            "user_query": user_message,
            "file_id": file_id,
            "conversation_id": conversation_id,
            "file_metadata": file_metadata,
            "table_name": table_name
        }
        
        # Run workflow
        result = await run_agent_workflow(state_dict)
        
        # Send response
        await manager.send_message(client_id, {
            "type": "response",
            "conversation_id": conversation_id,
            "message": result.get("insights", "No response generated"),
            "query_type": str(result.get("query_type")),
            "data": {
                "results": result.get("query_results", [])[:50],
                "count": len(result.get("query_results", [])),
                "sql": result.get("sql_query")
            } if result.get("query_results") else None,
            "visualizations": result.get("visualizations")
        })
    
    except Exception as e:
        logger.error(f"Error handling chat message: {e}", exc_info=True)
        await manager.send_message(client_id, {
            "type": "error",
            "message": str(e)
        })

