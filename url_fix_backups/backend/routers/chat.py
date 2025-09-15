#!/usr / bin / env python3
""""""
TRAE.AI Chat Integration Router

Comprehensive chat system with real - time messaging, AI integration,
and connection to all existing integrations (images, news, weather, pets).

Features:
- WebSocket real - time messaging
- AI - powered responses using multiple providers
- Integration with all existing services
- Chat history persistence
- Multi - user support
- Rich media support (images, links, embeds)
""""""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import httpx
from fastapi import (APIRouter, Body, Depends, HTTPException, Query, WebSocket,

# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     WebSocketDisconnect)

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import chat persistence
try:

    from backend.database.chat_db import (add_message, chat_db, create_conversation,

# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         get_conversations, get_messages)
except ImportError:
    # Fallback for different import paths
    try:

        from database.chat_db import (add_message, chat_db, create_conversation,

# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             get_conversations, get_messages)
    except ImportError:
        logger.warning("Chat persistence not available - running without database")
        chat_db = None

# Import existing integrations
try:

    from integrations_hub import _providers, get_secret

except ImportError:
    _providers = {}


    def get_secret(key: str) -> Optional[str]:
        return None

try:

    from content_sources import router as content_router

except ImportError:
    content_router = None

# Configure logging
logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/chat", tags=["chat"])

# Models


class ChatMessage(BaseModel):
    id: str = Field(default_factory = lambda: str(uuid4()))
    user_id: str
    content: str
    message_type: str = "text"  # text, image, system, ai_response
    timestamp: datetime = Field(default_factory = datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory = dict)
    integration_data: Optional[Dict[str, Any]] = None


class ChatRoom(BaseModel):
    id: str = Field(default_factory = lambda: str(uuid4()))
    name: str
    created_at: datetime = Field(default_factory = datetime.utcnow)
    participants: List[str] = Field(default_factory = list)
    last_activity: datetime = Field(default_factory = datetime.utcnow)
    settings: Dict[str, Any] = Field(default_factory = dict)


class AIRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    integration_type: Optional[str] = None  # news, weather, images, pets
    provider: Optional[str] = None  # openai, anthropic, etc.


class IntegrationRequest(BaseModel):
    type: str  # news, weather, images, pets
    query: str
    parameters: Optional[Dict[str, Any]] = None

# Connection Manager


class ConnectionManager:


    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.room_connections: Dict[str, List[str]] = {}
        self.user_rooms: Dict[str, List[str]] = {}
        self.user_conversations: Dict[str, str] = {}  # user_id -> conversation_id


    async def connect(
        self, websocket: WebSocket, user_id: str, room_id: str = "general"
# BRACKET_SURGEON: disabled
#     ):
        await websocket.accept()
        connection_id = f"{user_id}_{room_id}_{uuid4()}"
        self.active_connections[connection_id] = websocket

        # Add to room
        if room_id not in self.room_connections:
            self.room_connections[room_id] = []
        self.room_connections[room_id].append(connection_id)

        # Add to user rooms
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = []
        if room_id not in self.user_rooms[user_id]:
            self.user_rooms[user_id].append(room_id)

        # Create or get conversation for user
        if chat_db and user_id not in self.user_conversations:
            conversation_id = create_conversation(user_id)
            self.user_conversations[user_id] = conversation_id

        logger.info(f"User {user_id} connected to room {room_id}")
        return connection_id


    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

            # Remove from rooms
            for room_id, connections in self.room_connections.items():
                if connection_id in connections:
                    connections.remove(connection_id)
                    break

            logger.info(f"Connection {connection_id} disconnected")


    async def send_personal_message(self, message: str, connection_id: str):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            await websocket.send_text(message)


    async def broadcast_to_room(
        self, message: str, room_id: str, exclude_connection: Optional[str] = None
# BRACKET_SURGEON: disabled
#     ):
        if room_id in self.room_connections:
            for connection_id in self.room_connections[room_id]:
                if (
                    connection_id != exclude_connection
                    and connection_id in self.active_connections
# BRACKET_SURGEON: disabled
#                 ):
                    websocket = self.active_connections[connection_id]
                    try:
                        await websocket.send_text(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to {connection_id}: {e}")
                        self.disconnect(connection_id)


    async def broadcast_to_all(self, message: str):
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                self.disconnect(connection_id)

# Global connection manager
manager = ConnectionManager()

# In - memory storage (replace with database in production)
chat_history: Dict[str, List[ChatMessage]] = {}
rooms: Dict[str, ChatRoom] = {"general": ChatRoom(id="general", name="General Chat")}

# AI Integration Functions


async def get_ai_response(
    message: str, provider: str = "openai", context: Optional[Dict] = None
# BRACKET_SURGEON: disabled
# ) -> str:
    """Get AI response from specified provider"""
    try:
        if provider == "openai" and get_secret("OPENAI_API_KEY"):
            return await get_openai_response(message, context)
        elif provider == "anthropic" and get_secret("ANTHROPIC_API_KEY"):
            return await get_anthropic_response(message, context)
        elif provider == "google_gemini" and get_secret("GOOGLE_API_KEY"):
            return await get_gemini_response(message, context)
        else:
            return "I'm sorry, but I don't have access to AI services right now. Please check the integrations configuration."
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return f"I encountered an error while processing your request: {str(e)}"


async def get_openai_response(message: str, context: Optional[Dict] = None) -> str:
    """Get response from OpenAI"""
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API key not configured."

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com / v1 / chat / completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                "model": "gpt - 3.5 - turbo",
                    "messages": [
                    {
                        "role": "system",
                            "content": "You are a helpful assistant integrated into TRAE.AI production system. Be concise \"
#     and helpful.",
# BRACKET_SURGEON: disabled
#                             },
                        {"role": "user", "content": message},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                    "max_tokens": 500,
# BRACKET_SURGEON: disabled
#                     },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"OpenAI API error: {response.status_code}"


async def get_anthropic_response(message: str, context: Optional[Dict] = None) -> str:
    """Get response from Anthropic Claude"""
    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        return "Anthropic API key not configured."

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com / v1 / messages",
                headers={"x - api - key": api_key, "anthropic - version": "2023 - 06 - 01"},
                json={
                "model": "claude - 3 - sonnet - 20240229",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": message}],
# BRACKET_SURGEON: disabled
#                     },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        if response.status_code == 200:
            data = response.json()
            return data["content"][0]["text"]
        else:
            return f"Anthropic API error: {response.status_code}"


async def get_gemini_response(message: str, context: Optional[Dict] = None) -> str:
    """Get response from Google Gemini"""
    api_key = get_secret("GOOGLE_API_KEY")
    if not api_key:
        return "Google API key not configured."

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com / v1beta / models / gemini - pro:generateContent?key={api_key}",
                json={
                "contents": [{"parts": [{"text": message}]}],
                    "generationConfig": {"maxOutputTokens": 500},
# BRACKET_SURGEON: disabled
#                     },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"Gemini API error: {response.status_code}"

# Integration Functions


async def get_integration_data(
    integration_type: str, query: str, parameters: Optional[Dict] = None
) -> Dict[str, Any]:
    """Get data from various integrations"""
    try:
        if integration_type == "weather":
            return await get_weather_data(query, parameters)
        elif integration_type == "news":
            return await get_news_data(query, parameters)
        elif integration_type == "images":
            return await get_image_data(query, parameters)
        elif integration_type == "pets":
            return await get_pet_data(query, parameters)
        else:
            return {"error": f"Unknown integration type: {integration_type}"}
    except Exception as e:
        logger.error(f"Integration error for {integration_type}: {e}")
        return {"error": str(e)}


async def get_weather_data(
    query: str, parameters: Optional[Dict] = None
) -> Dict[str, Any]:
    """Get weather data"""
    api_key = get_secret("OPENWEATHER_KEY")
    if not api_key:
        return {"error": "OpenWeather API key not configured"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.openweathermap.org / data / 2.5 / weather?q={query}&appid={api_key}&units = metric"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        if response.status_code == 200:
            data = response.json()
            return {
                "type": "weather",
                    "location": data["name"],
                    "temperature": data["main"]["temp"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
# BRACKET_SURGEON: disabled
#                     }
        else:
            return {"error": f"Weather API error: {response.status_code}"}


async def get_news_data(
    query: str, parameters: Optional[Dict] = None
) -> Dict[str, Any]:
    """Get news data"""
    api_key = get_secret("NEWSAPI_KEY")
    if not api_key:
        return {"error": "NewsAPI key not configured"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://newsapi.org / v2 / everything?q={query}&apiKey={api_key}&pageSize = 5"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        if response.status_code == 200:
            data = response.json()
            articles = []
            for article in data.get("articles", [])[:3]:
                articles.append(
                    {
                        "title": article["title"],
                            "description": article["description"],
                            "url": article["url"],
                            "source": article["source"]["name"],
# BRACKET_SURGEON: disabled
#                             }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            return {"type": "news", "articles": articles}
        else:
            return {"error": f"News API error: {response.status_code}"}


async def get_image_data(
    query: str, parameters: Optional[Dict] = None
) -> Dict[str, Any]:
    """Get image data"""
    api_key = get_secret("UNSPLASH_KEY")
    if not api_key:
        return {"error": "Unsplash API key not configured"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.unsplash.com / search / photos?query={query}&per_page = 3",
                headers={"Authorization": f"Client - ID {api_key}"},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        if response.status_code == 200:
            data = response.json()
            images = []
            for photo in data.get("results", []):
                images.append(
                    {
                        "url": photo["urls"]["small"],
                            "description": photo["alt_description"],
                            "photographer": photo["user"]["name"],
# BRACKET_SURGEON: disabled
#                             }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            return {"type": "images", "images": images}
        else:
            return {"error": f"Image API error: {response.status_code}"}


async def get_pet_data(query: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
    """Get pet data"""
    # Use existing pet endpoints
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8000 / pets / search?animal={query}&limit = 3"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            if response.status_code == 200:
                data = response.json()
                return {"type": "pets", "pets": data.get("animals", [])}
            else:
                return {"error": f"Pet API error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Pet data error: {str(e)}"}

# WebSocket endpoint
@router.websocket("/ws/{user_id}")


async def websocket_endpoint(
    websocket: WebSocket, user_id: str, room_id: str = Query("general")
# BRACKET_SURGEON: disabled
# ):
    connection_id = await manager.connect(websocket, user_id, room_id)
    conversation_id = manager.user_conversations.get(user_id)

    # Send welcome message
    welcome_msg = {
        "type": "system",
            "content": f"Welcome to {rooms.get(room_id, {}).get('name', room_id)}! You can ask me about weather, news, images, \"
#     or pets.",
            "timestamp": datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#             }
    await manager.send_personal_message(json.dumps(welcome_msg), connection_id)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            message_type = message_data.get("type", "message")
            content = message_data.get("content", "")

            if message_type == "message":
                # Create chat message
                chat_message = ChatMessage(
                    user_id = user_id,
                        content = content,
                        message_type="text",
                        metadata = message_data.get("metadata", {}),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                # Store message in memory
                if room_id not in chat_history:
                    chat_history[room_id] = []
                chat_history[room_id].append(chat_message)

                # Save user message to database
                if chat_db and conversation_id:
                    add_message(
                        conversation_id,
                            "user",
                            content,
                            "text",
                            {"room_id": room_id, "user_id": user_id},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )

                # Broadcast message to room
                broadcast_data = {
                    "type": "message",
                        "user_id": user_id,
                        "content": chat_message.content,
                        "message_type": chat_message.message_type,
                        "timestamp": chat_message.timestamp.isoformat(),
                        "id": chat_message.id,
# BRACKET_SURGEON: disabled
#                         }
                await manager.broadcast_to_room(
                    json.dumps(broadcast_data),
                        room_id,
                        exclude_connection = connection_id,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                # Check for AI triggers or integration requests
                content_lower = content.lower()
                response = None
                response_type = "ai_response"

                if content_lower.startswith("/ai ") or content_lower.startswith("@ai "):
                    # AI request
                    ai_query = content_lower.replace("/ai ", "").replace("@ai ", "")
                    response = await get_ai_response(ai_query)
                    response_type = "ai_response"

                elif content_lower.startswith("/weather "):
                    # Weather request
                    location = content_lower.replace("/weather ", "")
                    weather_data = await get_weather_data(location)
                    response = f"Weather in {weather_data.get('location',"
    location)}: {weather_data.get('description', 'N / A')}, {weather_data.get('temperature', 'N / A')}°C""
                    response_type = "integration_response"

                elif content_lower.startswith("/news "):
                    # News request
                    query = content_lower.replace("/news ", "")
                    news_data = await get_news_data(query)
                    if "articles" in news_data:
                        articles = news_data["articles"][:3]
                        response = "Latest news:\\n" + "\\n".join(
                            [f"• {article['title']}" for article in articles]
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                    else:
                        response = (
                            f"News error: {news_data.get('error', 'Unknown error')}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                    response_type = "integration_response"

                elif content_lower.startswith("/images "):
                    # Image request
                    query = content_lower.replace("/images ", "")
                    image_data = await get_image_data(query)
                    if "images" in image_data:
                        images = image_data["images"][:3]
                        response = f"Found {len(images)} images for '{query}'"
                    else:
                        response = (
                            f"Image error: {image_data.get('error', 'Unknown error')}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                    response_type = "integration_response"

                elif content_lower.startswith("/pets "):
                    # Pet request
                    animal = content_lower.replace("/pets ", "")
                    pet_data = await get_pet_data(animal)
                    if "pets" in pet_data:
                        pets = pet_data["pets"]
                        response = f"Found {len(pets)} {animal}s available for adoption"
                    else:
                        response = (
                            f"Pet error: {pet_data.get('error', 'Unknown error')}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                    response_type = "integration_response"

                # Send AI / integration response
                if response:
                    # Save assistant response to database
                    if chat_db and conversation_id:
                        add_message(
                            conversation_id,
                                "assistant",
                                response,
                                response_type,
                                {
                                "room_id": room_id,
                                    "command": (
                                    content.split()[0]
                                    if content.startswith("/")
                                    else None
# BRACKET_SURGEON: disabled
#                                 ),
# BRACKET_SURGEON: disabled
#                                     },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )

                    ai_message = {
                        "type": response_type,
                            "user_id": "assistant",
                            "content": response,
                            "timestamp": datetime.utcnow().isoformat(),
                            "id": str(uuid4()),
# BRACKET_SURGEON: disabled
#                             }
                    await manager.broadcast_to_room(json.dumps(ai_message), room_id)

            elif message_type == "get_history":
                # Send chat history to user
                if chat_db and conversation_id:
                    messages = get_messages(conversation_id, limit = 50)
                    history_data = {
                        "type": "history",
                            "messages": messages,
                            "conversation_id": conversation_id,
# BRACKET_SURGEON: disabled
#                             }
                    await websocket.send_text(json.dumps(history_data))

            elif message_type == "ping":
                await websocket.send_text(
                    json.dumps(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

    except WebSocketDisconnect:
        manager.disconnect(connection_id)

        # Notify room of disconnection
        disconnect_msg = {
            "type": "system",
                "content": f"User {user_id} has left the chat",
                "timestamp": datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#                 }
        await manager.broadcast_to_room(json.dumps(disconnect_msg), room_id)

# REST API Endpoints
@router.get("/rooms")


async def get_rooms():
    """Get all chat rooms"""
    return {"rooms": list(rooms.values())}

@router.post("/rooms")


async def create_room(room: ChatRoom):
    """Create a new chat room"""
    rooms[room.id] = room
    return {"message": "Room created", "room": room}

@router.get("/rooms/{room_id}/history")


async def get_chat_history(room_id: str, limit: int = Query(50, ge = 1, le = 200)):
    """Get chat history for a room"""
    if room_id not in chat_history:
        return {"messages": []}

    messages = chat_history[room_id][-limit:]
    return {"messages": [msg.dict() for msg in messages]}

@router.post("/ai")


async def ai_chat(request: AIRequest):
    """Get AI response via REST API"""
    provider = request.provider or "openai"
    response = await get_ai_response(request.message, provider, request.context)

    return {
        "response": response,
            "provider": provider,
            "timestamp": datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#             }

@router.post("/integrations")


async def integration_request(request: IntegrationRequest):
    """Get data from integrations via REST API"""
    data = await get_integration_data(request.type, request.query, request.parameters)

    return {
        "type": request.type,
            "query": request.query,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#             }

@router.get("/status")


async def chat_status():
    """Get chat system status"""
    return {
        "active_connections": len(manager.active_connections),
            "rooms": len(rooms),
            "total_messages": sum(len(messages) for messages in chat_history.values()),
            "integrations_available": {
            "ai_providers": [
                "openai" if get_secret("OPENAI_API_KEY") else None,
                    "anthropic" if get_secret("ANTHROPIC_API_KEY") else None,
                    "google_gemini" if get_secret("GOOGLE_API_KEY") else None,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ],
                "weather": bool(get_secret("OPENWEATHER_KEY")),
                "news": bool(get_secret("NEWSAPI_KEY")),
                "images": bool(get_secret("UNSPLASH_KEY")),
                "pets": True,  # Uses internal API
# BRACKET_SURGEON: disabled
#         },
            "timestamp": datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#             }

@router.delete("/rooms/{room_id}/history")


async def clear_chat_history(room_id: str):
    """Clear chat history for a room"""
    if room_id in chat_history:
        chat_history[room_id] = []
        return {"message": f"Chat history cleared for room {room_id}"}
    else:
        raise HTTPException(status_code = 404, detail="Room not found")

# Health check
@router.get("/health")


async def health_check():
    """Health check endpoint"""
    stats = {}
    if chat_db:
        stats = chat_db.get_stats()

    return {
        "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_connections": len(manager.active_connections),
            "rooms": list(manager.room_connections.keys()),
            "database_stats": stats,
# BRACKET_SURGEON: disabled
#             }

# Chat History and Conversation Management Endpoints

@router.get("/conversations/{user_id}")


async def get_user_conversations(user_id: str, limit: int = 50):
    """Get conversations for a user"""
    if not chat_db:
        raise HTTPException(status_code = 503, detail="Chat persistence not available")

    try:
        conversations = get_conversations(user_id, limit)
        return {
            "user_id": user_id,
                "conversations": conversations,
                "total": len(conversations),
# BRACKET_SURGEON: disabled
#                 }
    except Exception as e:
        logger.error(f"Failed to get conversations for user {user_id}: {e}")
        raise HTTPException(status_code = 500,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     detail="Failed to retrieve conversations")

@router.get("/conversations/{user_id}/{conversation_id}/messages")


async def get_conversation_messages(
    user_id: str, conversation_id: str, limit: int = 100
# BRACKET_SURGEON: disabled
# ):
    """Get messages for a specific conversation"""
    if not chat_db:
        raise HTTPException(status_code = 503, detail="Chat persistence not available")

    try:
        messages = get_messages(conversation_id, limit)
        return {
            "conversation_id": conversation_id,
                "user_id": user_id,
                "messages": messages,
                "total": len(messages),
# BRACKET_SURGEON: disabled
#                 }
    except Exception as e:
        logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
        raise HTTPException(status_code = 500, detail="Failed to retrieve messages")

@router.post("/conversations/{user_id}")


async def create_new_conversation(user_id: str, title: str = None):
    """Create a new conversation for a user"""
    if not chat_db:
        raise HTTPException(status_code = 503, detail="Chat persistence not available")

    try:
        conversation_id = create_conversation(user_id, title)
        return {
            "conversation_id": conversation_id,
                "user_id": user_id,
                "title": title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "created_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }
    except Exception as e:
        logger.error(f"Failed to create conversation for user {user_id}: {e}")
        raise HTTPException(status_code = 500, detail="Failed to create conversation")

@router.put("/conversations/{conversation_id}/title")


async def update_conversation_title(conversation_id: str, title: str):
    """Update conversation title"""
    if not chat_db:
        raise HTTPException(status_code = 503, detail="Chat persistence not available")

    try:
        success = chat_db.update_conversation_title(conversation_id, title)
        if not success:
            raise HTTPException(status_code = 404, detail="Conversation not found")

        return {
            "conversation_id": conversation_id,
                "title": title,
                "updated_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation title {conversation_id}: {e}")
        raise HTTPException(
            status_code = 500, detail="Failed to update conversation title"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

@router.delete("/conversations/{conversation_id}")


async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages"""
    if not chat_db:
        raise HTTPException(status_code = 503, detail="Chat persistence not available")

    try:
        success = chat_db.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code = 404, detail="Conversation not found")

        return {
            "conversation_id": conversation_id,
                "deleted": True,
                "deleted_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {e}")
        raise HTTPException(status_code = 500, detail="Failed to delete conversation")

@router.get("/search/{user_id}")


async def search_user_messages(user_id: str, q: str, limit: int = 50):
    """Search messages for a user"""
    if not chat_db:
        raise HTTPException(status_code = 503, detail="Chat persistence not available")

    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code = 400, detail="Search query must be at least 2 characters"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

    try:

        from backend.database.chat_db import search_chat

        results = search_chat(q.strip(), user_id, limit)
        return {
            "query": q,
                "user_id": user_id,
                "results": results,
                "total": len(results),
# BRACKET_SURGEON: disabled
#                 }
    except Exception as e:
        logger.error(f"Failed to search messages for user {user_id}: {e}")
        raise HTTPException(status_code = 500, detail="Failed to search messages")

@router.get("/stats")


async def get_chat_stats():
    """Get chat system statistics"""
    if not chat_db:
        return {"database_available": False}

    try:
        stats = chat_db.get_stats()
        stats["database_available"] = True
        stats["active_connections"] = len(manager.active_connections)
        stats["active_rooms"] = len(manager.room_connections)
        return stats
    except Exception as e:
        logger.error(f"Failed to get chat stats: {e}")
        raise HTTPException(status_code = 500, detail="Failed to retrieve statistics")