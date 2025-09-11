from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "connected_at": datetime.now(),
            "last_ping": datetime.now()
        }
        logger.info(
            f"WebSocket connected: {
                self.connection_info[websocket]['client_id']}")

        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "client_id": self.connection_info[websocket]["client_id"],
            "timestamp": datetime.now().isoformat()
        }, websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            client_id = self.connection_info.get(
                websocket, {}).get(
                "client_id", "unknown")
            self.active_connections.remove(websocket)
            if websocket in self.connection_info:
                del self.connection_info[websocket]
            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return

        message["timestamp"] = datetime.now().isoformat()
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_metrics_update(self, metrics: dict):
        """Broadcast metrics update to all clients"""
        await self.broadcast({
            "type": "metrics_update",
            "metrics": metrics
        })

    async def broadcast_service_status(self, service: str, status: str):
        """Broadcast service status change"""
        await self.broadcast({
            "type": "service_status",
            "service": service,
            "status": status
        })

    async def broadcast_system_alert(self, message: str, level: str = "info"):
        """Broadcast system alert"""
        await self.broadcast({
            "type": "system_alert",
            "message": message,
            "level": level
        })

    async def broadcast_log_entry(self, log: dict):
        """Broadcast new log entry"""
        await self.broadcast({
            "type": "log_entry",
            "log": log
        })

    async def broadcast_performance_update(self, performance: dict):
        """Broadcast performance metrics update"""
        await self.broadcast({
            "type": "performance_update",
            "performance": performance
        })

    async def handle_client_message(self, websocket: WebSocket, data: dict):
        """Handle incoming messages from clients"""
        message_type = data.get("type")

        if message_type == "ping":
            await self.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }, websocket)

            # Update last ping time
            if websocket in self.connection_info:
                self.connection_info[websocket]["last_ping"] = datetime.now()

        elif message_type == "subscribe":
            # Handle subscription to specific data streams
            channels = data.get("channels", [])
            if websocket in self.connection_info:
                self.connection_info[websocket]["subscriptions"] = channels

            await self.send_personal_message({
                "type": "subscription_confirmed",
                "channels": channels
            }, websocket)

        elif message_type == "request_data":
            # Handle data requests
            data_type = data.get("data_type")
            await self.handle_data_request(websocket, data_type)

    async def handle_data_request(self, websocket: WebSocket, data_type: str):
        """Handle specific data requests from clients"""
        try:
            if data_type == "current_metrics":
                # Mock current metrics - replace with actual data fetching
                metrics = {
                    "active_sessions": 42,
                    "api_calls_today": 1247,
                    "response_time": 145,
                    "error_rate": 0.02
                }
                await self.send_personal_message({
                    "type": "metrics_update",
                    "metrics": metrics
                }, websocket)

            elif data_type == "service_status":
                # Mock service status - replace with actual service checking
                services = {
                    "youtube_automation": {
                        "status": "active", "last_run": datetime.now().isoformat()}, "content_pipeline": {
                        "status": "active", "last_run": datetime.now().isoformat()}, "marketing_agent": {
                        "status": "active", "last_run": datetime.now().isoformat()}, "financial_tracking": {
                        "status": "active", "last_run": datetime.now().isoformat()}}
                await self.send_personal_message({
                    "type": "services_update",
                    "services": services
                }, websocket)

        except Exception as e:
            logger.error(f"Error handling data request: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": "Failed to fetch requested data"
            }, websocket)

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections"""
        return [
            {
                "client_id": info["client_id"],
                "connected_at": info["connected_at"].isoformat(),
                "last_ping": info["last_ping"].isoformat(),
                "subscriptions": info.get("subscriptions", [])
            }
            for info in self.connection_info.values()
        ]

    async def start_heartbeat(self):
        """Start heartbeat to keep connections alive"""
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            if self.active_connections:
                await self.broadcast({
                    "type": "heartbeat",
                    "active_connections": self.get_connection_count()
                })


# Global WebSocket manager instance
websocket_manager = WebSocketManager()

# Background task to simulate real-time data updates


async def simulate_real_time_updates():
    """Simulate real-time data updates for demonstration"""
    import random

    while True:
        await asyncio.sleep(10)  # Update every 10 seconds

        if websocket_manager.get_connection_count() > 0:
            # Simulate metrics update
            metrics = {
                "active_sessions": random.randint(30, 100),
                "api_calls_today": random.randint(1000, 2000),
                "response_time": random.randint(50, 300),
                "error_rate": round(random.uniform(0, 0.1), 3)
            }
            await websocket_manager.broadcast_metrics_update(metrics)

            # Occasionally simulate alerts
            if random.random() < 0.1:  # 10% chance
                alert_types = ["info", "warning"]
                alert_messages = {
                    "info": "System backup completed successfully",
                    "warning": "High CPU usage detected"
                }
                alert_type = random.choice(alert_types)
                await websocket_manager.broadcast_system_alert(
                    alert_messages[alert_type],
                    alert_type
                )

            # Simulate log entries
            if random.random() < 0.3:  # 30% chance
                log_levels = ["info", "warning", "error"]
                log_messages = {
                    "info": "API request processed successfully",
                    "warning": "Slow query detected",
                    "error": "Database connection timeout"
                }
                level = random.choice(log_levels)
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "level": level,
                    "message": log_messages[level]
                }
                await websocket_manager.broadcast_log_entry(log_entry)
