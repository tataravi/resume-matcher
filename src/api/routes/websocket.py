import json
import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.websockets import WebSocketState
from datetime import datetime
import logging

from src.api.auth import verify_token, TokenData
from src.api.dependencies import get_orchestrator_agent
from src.agents.orchestrator_agent import OrchestratorAgent


logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store analysis subscriptions (analysis_id -> set of user_ids)
        self.analysis_subscriptions: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected via WebSocket")
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection_established",
            "message": "WebSocket connection established",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty user connection sets
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
        # Remove from analysis subscriptions
        for analysis_id, subscribers in list(self.analysis_subscriptions.items()):
            subscribers.discard(user_id)
            if not subscribers:
                del self.analysis_subscriptions[analysis_id]
                
        logger.info(f"User {user_id} disconnected from WebSocket")
        
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message via WebSocket: {e}")
                
    async def send_message_to_user(self, message: dict, user_id: str):
        """Send a message to all connections of a specific user."""
        if user_id in self.active_connections:
            disconnected_connections = set()
            
            for websocket in self.active_connections[user_id]:
                if websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"Failed to send message to user {user_id}: {e}")
                        disconnected_connections.add(websocket)
                else:
                    disconnected_connections.add(websocket)
            
            # Clean up disconnected connections
            for websocket in disconnected_connections:
                self.active_connections[user_id].discard(websocket)
                
    async def subscribe_to_analysis(self, user_id: str, analysis_id: str):
        """Subscribe a user to analysis updates."""
        if analysis_id not in self.analysis_subscriptions:
            self.analysis_subscriptions[analysis_id] = set()
        
        self.analysis_subscriptions[analysis_id].add(user_id)
        logger.info(f"User {user_id} subscribed to analysis {analysis_id}")
        
    async def unsubscribe_from_analysis(self, user_id: str, analysis_id: str):
        """Unsubscribe a user from analysis updates."""
        if analysis_id in self.analysis_subscriptions:
            self.analysis_subscriptions[analysis_id].discard(user_id)
            
            if not self.analysis_subscriptions[analysis_id]:
                del self.analysis_subscriptions[analysis_id]
                
        logger.info(f"User {user_id} unsubscribed from analysis {analysis_id}")
        
    async def broadcast_analysis_update(self, analysis_id: str, update: dict):
        """Broadcast an analysis update to all subscribers."""
        if analysis_id in self.analysis_subscriptions:
            for user_id in self.analysis_subscriptions[analysis_id]:
                message = {
                    "type": "analysis_update",
                    "analysis_id": analysis_id,
                    "update": update,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message_to_user(message, user_id)


# Global connection manager instance
manager = ConnectionManager()


async def authenticate_websocket(websocket: WebSocket) -> str:
    """Authenticate WebSocket connection using query parameter token."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        raise HTTPException(status_code=4001, detail="Missing authentication token")
    
    try:
        token_data = verify_token(token)
        return token_data.user_id
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid authentication token")
        raise HTTPException(status_code=4001, detail="Invalid authentication token")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
):
    """WebSocket endpoint for real-time communication."""
    
    # Authenticate the connection
    try:
        user_id = await authenticate_websocket(websocket)
    except HTTPException:
        return
    
    # Connect the user
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive and process messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(message, user_id, websocket, orchestrator)
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Failed to process message",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


async def handle_websocket_message(
    message: dict, 
    user_id: str, 
    websocket: WebSocket,
    orchestrator: OrchestratorAgent
):
    """Handle incoming WebSocket messages."""
    
    message_type = message.get("type")
    
    if message_type == "subscribe_analysis":
        analysis_id = message.get("analysis_id")
        if analysis_id:
            await manager.subscribe_to_analysis(user_id, analysis_id)
            await manager.send_personal_message({
                "type": "subscription_confirmed",
                "analysis_id": analysis_id,
                "message": f"Subscribed to analysis {analysis_id}",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
            
            # Send current status
            status = orchestrator.get_workflow_status(analysis_id)
            if status:
                await manager.send_personal_message({
                    "type": "analysis_status",
                    "analysis_id": analysis_id,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
    elif message_type == "unsubscribe_analysis":
        analysis_id = message.get("analysis_id")
        if analysis_id:
            await manager.unsubscribe_from_analysis(user_id, analysis_id)
            await manager.send_personal_message({
                "type": "unsubscription_confirmed",
                "analysis_id": analysis_id,
                "message": f"Unsubscribed from analysis {analysis_id}",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
            
    elif message_type == "ping":
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
    elif message_type == "get_status":
        analysis_id = message.get("analysis_id")
        if analysis_id:
            status = orchestrator.get_workflow_status(analysis_id)
            await manager.send_personal_message({
                "type": "analysis_status",
                "analysis_id": analysis_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": "Missing analysis_id in get_status request",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
            
    else:
        await manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)


# Analysis progress monitoring (would be called by orchestrator)
async def notify_analysis_progress(analysis_id: str, progress_data: dict):
    """Notify subscribers about analysis progress."""
    await manager.broadcast_analysis_update(analysis_id, progress_data)


# Export the manager for use in other parts of the application
__all__ = ["manager", "notify_analysis_progress"]