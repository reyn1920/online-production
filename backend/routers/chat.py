#!/usr/bin/env python3
"""
TRAE Chat Integration Router

Comprehensive chat system with real-time messaging capabilities.
Secure WebSocket connections and message handling.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory storage for demo purposes
chat_sessions: Dict[str, List[Dict[str, Any]]] = {}
active_connections: List[WebSocket] = []

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"
    user_id: str = "anonymous"

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    session_id: str

@router.post("/send", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage):
    """Send a chat message and get AI response."""
    try:
        # Initialize session if not exists
        if chat_message.session_id not in chat_sessions:
            chat_sessions[chat_message.session_id] = []
        
        # Add user message to session
        user_msg = {
            "role": "user",
            "content": chat_message.message,
            "timestamp": datetime.now().isoformat(),
            "user_id": chat_message.user_id
        }
        chat_sessions[chat_message.session_id].append(user_msg)
        
        # Simple AI response (placeholder)
        ai_response = f"I received your message: '{chat_message.message}'. This is a demo response."
        
        # Add AI response to session
        ai_msg = {
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        chat_sessions[chat_message.session_id].append(ai_msg)
        
        return ChatResponse(
            response=ai_response,
            timestamp=datetime.now().isoformat(),
            session_id=chat_message.session_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    if session_id not in chat_sessions:
        return {"messages": []}
    
    return {"messages": chat_sessions[session_id]}

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            chat_message = ChatMessage(
                message=message_data.get("message", ""),
                session_id=session_id,
                user_id=message_data.get("user_id", "anonymous")
            )
            
            # Send response back
            response = await send_message(chat_message)
            await websocket.send_text(json.dumps({
                "type": "response",
                "data": response.dict()
            }))
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"WebSocket error: {str(e)}"
        }))
        active_connections.remove(websocket)

@router.get("/health")
async def chat_health():
    """Check chat system health."""
    return {
        "ok": True,
        "active_sessions": len(chat_sessions),
        "active_connections": len(active_connections),
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session."""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    
    raise HTTPException(status_code=404, detail="Session not found")