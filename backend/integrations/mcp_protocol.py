#!/usr/bin/env python3
"""
TRAE.AI Model Context Protocol (MCP) Implementation

Provides standardized AI model communication and context sharing
for the autonomous AI CEO framework. Enables seamless integration
between different AI models, agents, and external services.

Features:
- Standardized message protocol for AI model communication
- Context sharing and state management
- Tool registration and discovery
- Resource management and access control
- Real-time bidirectional communication
- Multi-model orchestration
- Context persistence and retrieval

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp
import websockets

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.secret_store import SecretStore

try:
    import jsonschema

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class MCPMessageType(Enum):
    """MCP message types."""

    # Core protocol messages
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    PING = "ping"
    PONG = "pong"

    # Tool management
    LIST_TOOLS = "tools/list"
    CALL_TOOL = "tools/call"
    TOOL_RESULT = "tools/result"

    # Resource management
    LIST_RESOURCES = "resources/list"
    READ_RESOURCE = "resources/read"
    SUBSCRIBE_RESOURCE = "resources/subscribe"
    UNSUBSCRIBE_RESOURCE = "resources/unsubscribe"
    RESOURCE_UPDATED = "resources/updated"

    # Context management
    GET_CONTEXT = "context/get"
    SET_CONTEXT = "context/set"
    UPDATE_CONTEXT = "context/update"
    CLEAR_CONTEXT = "context/clear"

    # Prompt management
    LIST_PROMPTS = "prompts/list"
    GET_PROMPT = "prompts/get"

    # Notifications
    NOTIFICATION = "notification"
    ERROR = "error"

    # Custom extensions
    AGENT_REGISTER = "agent/register"
    AGENT_UNREGISTER = "agent/unregister"
    WORKFLOW_START = "workflow/start"
    WORKFLOW_STATUS = "workflow/status"
    WORKFLOW_COMPLETE = "workflow/complete"


class MCPCapability(Enum):
    """MCP server capabilities."""

    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"
    LOGGING = "logging"
    SAMPLING = "sampling"
    CONTEXT = "context"
    WORKFLOWS = "workflows"
    AGENTS = "agents"


class MCPResourceType(Enum):
    """MCP resource types."""

    TEXT = "text"
    BINARY = "binary"
    JSON = "json"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    DATABASE = "database"
    API = "api"


@dataclass
class MCPMessage:
    """Base MCP message structure."""

    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {"jsonrpc": self.jsonrpc}

        if self.id is not None:
            data["id"] = self.id
        if self.method is not None:
            data["method"] = self.method
        if self.params is not None:
            data["params"] = self.params
        if self.result is not None:
            data["result"] = self.result
        if self.error is not None:
            data["error"] = self.error

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMessage":
        """Create from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error"),
        )


@dataclass
class MCPTool:
    """MCP tool definition."""

    name: str
    description: str
    inputSchema: Dict[str, Any]
    outputSchema: Optional[Dict[str, Any]] = None
    handler: Optional[Callable] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MCPResource:
    """MCP resource definition."""

    uri: str
    name: str
    description: str
    mimeType: str
    resourceType: MCPResourceType
    metadata: Optional[Dict[str, Any]] = None
    content: Optional[Any] = None
    lastModified: Optional[datetime] = None


@dataclass
class MCPPrompt:
    """MCP prompt definition."""

    name: str
    description: str
    template: str
    arguments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MCPContext:
    """MCP context data."""

    id: str
    name: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MCPServerInfo:
    """MCP server information."""

    name: str
    version: str
    capabilities: List[MCPCapability]
    description: Optional[str] = None
    author: Optional[str] = None
    homepage: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MCPServer:
    """
    Model Context Protocol (MCP) Server implementation.
    Provides standardized AI model communication and context sharing.
    """

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        host: str = "localhost",
        port: int = 8765,
        capabilities: Optional[List[MCPCapability]] = None,
    ):

        self.logger = setup_logger(f"mcp_server_{name}")

        # Server configuration
        self.info = MCPServerInfo(
            name=name,
            version=version,
            capabilities=capabilities
            or [MCPCapability.TOOLS, MCPCapability.RESOURCES, MCPCapability.CONTEXT],
            description=f"TRAE.AI MCP Server - {name}",
            author="TRAE.AI System",
        )

        self.host = host
        self.port = port

        # Registry for tools, resources, and prompts
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}

        # Context storage
        self.contexts: Dict[str, MCPContext] = {}

        # Client connections
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}

        # Message handlers
        self.handlers: Dict[str, Callable] = {
            MCPMessageType.INITIALIZE.value: self._handle_initialize,
            MCPMessageType.PING.value: self._handle_ping,
            MCPMessageType.LIST_TOOLS.value: self._handle_list_tools,
            MCPMessageType.CALL_TOOL.value: self._handle_call_tool,
            MCPMessageType.LIST_RESOURCES.value: self._handle_list_resources,
            MCPMessageType.READ_RESOURCE.value: self._handle_read_resource,
            MCPMessageType.LIST_PROMPTS.value: self._handle_list_prompts,
            MCPMessageType.GET_PROMPT.value: self._handle_get_prompt,
            MCPMessageType.GET_CONTEXT.value: self._handle_get_context,
            MCPMessageType.SET_CONTEXT.value: self._handle_set_context,
            MCPMessageType.UPDATE_CONTEXT.value: self._handle_update_context,
            MCPMessageType.CLEAR_CONTEXT.value: self._handle_clear_context,
        }

        # Server state
        self.running = False
        self.server = None

        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=10)

        self.logger.info(f"MCP Server '{name}' initialized")

    def register_tool(self, tool: MCPTool):
        """Register a tool with the server."""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")

    def register_resource(self, resource: MCPResource):
        """Register a resource with the server."""
        self.resources[resource.uri] = resource
        self.logger.info(f"Registered resource: {resource.uri}")

    def register_prompt(self, prompt: MCPPrompt):
        """Register a prompt with the server."""
        self.prompts[prompt.name] = prompt
        self.logger.info(f"Registered prompt: {prompt.name}")

    async def start(self):
        """Start the MCP server."""
        if self.running:
            self.logger.warning("Server is already running")
            return

        try:
            self.server = await websockets.serve(
                self._handle_client, self.host, self.port
            )

            self.running = True
            self.logger.info(f"MCP Server started on {self.host}:{self.port}")

            # Keep server running
            await self.server.wait_closed()

        except Exception as e:
            self.logger.error(f"Failed to start MCP server: {e}")
            raise

    async def stop(self):
        """Stop the MCP server."""
        if not self.running:
            return

        self.running = False

        # Close all client connections
        for client_id, websocket in list(self.clients.items()):
            try:
                await websocket.close()
            except Exception as e:
                self.logger.error(f"Error closing client {client_id}: {e}")

        self.clients.clear()

        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        self.logger.info("MCP Server stopped")

    async def _handle_client(self, websocket, path):
        """Handle new client connection."""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket

        self.logger.info(f"Client connected: {client_id}")

        try:
            async for message in websocket:
                await self._process_message(client_id, message)

        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]

    async def _process_message(self, client_id: str, raw_message: str):
        """Process incoming message from client."""
        try:
            # Parse JSON-RPC message
            data = json.loads(raw_message)
            message = MCPMessage.from_dict(data)

            # Handle the message
            if message.method in self.handlers:
                handler = self.handlers[message.method]
                response = await handler(client_id, message)

                if response:
                    await self._send_message(client_id, response)
            else:
                # Unknown method
                error_response = MCPMessage(
                    id=message.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {message.method}",
                    },
                )
                await self._send_message(client_id, error_response)

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON from client {client_id}: {e}")
            error_response = MCPMessage(
                error={"code": -32700, "message": "Parse error"}
            )
            await self._send_message(client_id, error_response)
        except Exception as e:
            self.logger.error(f"Error processing message from client {client_id}: {e}")
            error_response = MCPMessage(
                id=getattr(message, "id", None) if "message" in locals() else None,
                error={"code": -32603, "message": "Internal error"},
            )
            await self._send_message(client_id, error_response)

    async def _send_message(self, client_id: str, message: MCPMessage):
        """Send message to client."""
        if client_id not in self.clients:
            self.logger.warning(f"Client {client_id} not found")
            return

        try:
            websocket = self.clients[client_id]
            json_data = json.dumps(message.to_dict())
            await websocket.send(json_data)

        except Exception as e:
            self.logger.error(f"Error sending message to client {client_id}: {e}")

    async def broadcast_message(
        self, message: MCPMessage, exclude_client: Optional[str] = None
    ):
        """Broadcast message to all connected clients."""
        for client_id in list(self.clients.keys()):
            if exclude_client and client_id == exclude_client:
                continue
            await self._send_message(client_id, message)

    # Message handlers
    async def _handle_initialize(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle initialization request."""
        return MCPMessage(
            id=message.id,
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": [cap.value for cap in self.info.capabilities],
                "serverInfo": {
                    "name": self.info.name,
                    "version": self.info.version,
                    "description": self.info.description,
                    "author": self.info.author,
                },
            },
        )

    async def _handle_ping(self, client_id: str, message: MCPMessage) -> MCPMessage:
        """Handle ping request."""
        return MCPMessage(
            id=message.id,
            result={"pong": True, "timestamp": datetime.now().isoformat()},
        )

    async def _handle_list_tools(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle list tools request."""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                    "outputSchema": tool.outputSchema,
                    "metadata": tool.metadata,
                }
            )

        return MCPMessage(id=message.id, result={"tools": tools_list})

    async def _handle_call_tool(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle tool call request."""
        params = message.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            return MCPMessage(
                id=message.id,
                error={"code": -32602, "message": f"Tool not found: {tool_name}"},
            )

        tool = self.tools[tool_name]

        try:
            # Validate input if schema is available
            if JSONSCHEMA_AVAILABLE and tool.inputSchema:
                jsonschema.validate(arguments, tool.inputSchema)

            # Call tool handler
            if tool.handler:
                if asyncio.iscoroutinefunction(tool.handler):
                    result = await tool.handler(**arguments)
                else:
                    # Run in executor for blocking functions
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.executor, lambda: tool.handler(**arguments)
                    )
            else:
                result = {
                    "message": f"Tool {tool_name} executed",
                    "arguments": arguments,
                }

            return MCPMessage(
                id=message.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                json.dumps(result)
                                if not isinstance(result, str)
                                else result
                            ),
                        }
                    ]
                },
            )

        except Exception as e:
            self.logger.error(f"Error calling tool {tool_name}: {e}")
            return MCPMessage(
                id=message.id,
                error={"code": -32603, "message": f"Tool execution failed: {str(e)}"},
            )

    async def _handle_list_resources(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle list resources request."""
        resources_list = []
        for resource in self.resources.values():
            resources_list.append(
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mimeType,
                    "resourceType": resource.resourceType.value,
                    "metadata": resource.metadata,
                }
            )

        return MCPMessage(id=message.id, result={"resources": resources_list})

    async def _handle_read_resource(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle read resource request."""
        params = message.params or {}
        uri = params.get("uri")

        if uri not in self.resources:
            return MCPMessage(
                id=message.id,
                error={"code": -32602, "message": f"Resource not found: {uri}"},
            )

        resource = self.resources[uri]

        return MCPMessage(
            id=message.id,
            result={
                "contents": [
                    {
                        "uri": resource.uri,
                        "mimeType": resource.mimeType,
                        "text": str(resource.content) if resource.content else "",
                    }
                ]
            },
        )

    async def _handle_list_prompts(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle list prompts request."""
        prompts_list = []
        for prompt in self.prompts.values():
            prompts_list.append(
                {
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": prompt.arguments,
                    "metadata": prompt.metadata,
                }
            )

        return MCPMessage(id=message.id, result={"prompts": prompts_list})

    async def _handle_get_prompt(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle get prompt request."""
        params = message.params or {}
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})

        if prompt_name not in self.prompts:
            return MCPMessage(
                id=message.id,
                error={"code": -32602, "message": f"Prompt not found: {prompt_name}"},
            )

        prompt = self.prompts[prompt_name]

        # Simple template substitution
        rendered_template = prompt.template
        for key, value in arguments.items():
            rendered_template = rendered_template.replace(f"{{{key}}}", str(value))

        return MCPMessage(
            id=message.id,
            result={
                "description": prompt.description,
                "messages": [
                    {
                        "role": "user",
                        "content": {"type": "text", "text": rendered_template},
                    }
                ],
            },
        )

    async def _handle_get_context(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle get context request."""
        params = message.params or {}
        context_id = params.get("id")

        if context_id not in self.contexts:
            return MCPMessage(
                id=message.id,
                error={"code": -32602, "message": f"Context not found: {context_id}"},
            )

        context = self.contexts[context_id]

        # Check if context has expired
        if context.expires_at and context.expires_at < datetime.now():
            del self.contexts[context_id]
            return MCPMessage(
                id=message.id,
                error={"code": -32602, "message": f"Context expired: {context_id}"},
            )

        return MCPMessage(
            id=message.id,
            result={
                "context": {
                    "id": context.id,
                    "name": context.name,
                    "data": context.data,
                    "created_at": context.created_at.isoformat(),
                    "updated_at": context.updated_at.isoformat(),
                    "metadata": context.metadata,
                }
            },
        )

    async def _handle_set_context(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle set context request."""
        params = message.params or {}
        context_id = params.get("id", str(uuid.uuid4()))
        name = params.get("name", f"Context-{context_id[:8]}")
        data = params.get("data", {})
        expires_in = params.get("expires_in")  # seconds
        metadata = params.get("metadata")

        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=expires_in)

        context = MCPContext(
            id=context_id,
            name=name,
            data=data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            expires_at=expires_at,
            metadata=metadata,
        )

        self.contexts[context_id] = context

        return MCPMessage(
            id=message.id, result={"context_id": context_id, "created": True}
        )

    async def _handle_update_context(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle update context request."""
        params = message.params or {}
        context_id = params.get("id")
        data_updates = params.get("data", {})

        if context_id not in self.contexts:
            return MCPMessage(
                id=message.id,
                error={"code": -32602, "message": f"Context not found: {context_id}"},
            )

        context = self.contexts[context_id]

        # Update context data
        context.data.update(data_updates)
        context.updated_at = datetime.now()

        return MCPMessage(
            id=message.id, result={"context_id": context_id, "updated": True}
        )

    async def _handle_clear_context(
        self, client_id: str, message: MCPMessage
    ) -> MCPMessage:
        """Handle clear context request."""
        params = message.params or {}
        context_id = params.get("id")

        if context_id:
            # Clear specific context
            if context_id in self.contexts:
                del self.contexts[context_id]
                return MCPMessage(id=message.id, result={"cleared": context_id})
            else:
                return MCPMessage(
                    id=message.id,
                    error={
                        "code": -32602,
                        "message": f"Context not found: {context_id}",
                    },
                )
        else:
            # Clear all contexts
            cleared_count = len(self.contexts)
            self.contexts.clear()
            return MCPMessage(id=message.id, result={"cleared_count": cleared_count})


class MCPClient:
    """
    Model Context Protocol (MCP) Client implementation.
    Connects to MCP servers and provides standardized communication.
    """

    def __init__(self, name: str = "TRAE.AI MCP Client"):
        self.logger = setup_logger("mcp_client")
        self.name = name

        # Connection state
        self.websocket = None
        self.connected = False
        self.server_info = None

        # Message tracking
        self.message_id = 0
        self.pending_requests = {}

        # Event handlers
        self.event_handlers = {}

        self.logger.info(f"MCP Client '{name}' initialized")

    async def connect(self, uri: str) -> bool:
        """Connect to MCP server."""
        try:
            self.websocket = await websockets.connect(uri)
            self.connected = True

            # Initialize connection
            init_response = await self.send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": self.name, "version": "1.0.0"},
                },
            )

            if init_response and "result" in init_response:
                self.server_info = init_response["result"]
                self.logger.info(
                    f"Connected to MCP server: {self.server_info.get('serverInfo', {}).get('name', 'Unknown')}"
                )
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        self.connected = False
        self.server_info = None
        self.pending_requests.clear()

        self.logger.info("Disconnected from MCP server")

    async def send_request(
        self, method: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Send request to MCP server and wait for response."""
        if not self.connected or not self.websocket:
            self.logger.error("Not connected to MCP server")
            return None

        self.message_id += 1
        message = MCPMessage(id=self.message_id, method=method, params=params)

        try:
            # Send message
            await self.websocket.send(json.dumps(message.to_dict()))

            # Wait for response
            response_data = await self.websocket.recv()
            response = json.loads(response_data)

            return response

        except Exception as e:
            self.logger.error(f"Error sending request {method}: {e}")
            return None

    async def list_tools(self) -> List[Dict]:
        """List available tools on the server."""
        response = await self.send_request("tools/list")
        if response and "result" in response:
            return response["result"].get("tools", [])
        return []

    async def call_tool(self, name: str, arguments: Dict = None) -> Optional[Dict]:
        """Call a tool on the server."""
        response = await self.send_request(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )
        if response and "result" in response:
            return response["result"]
        return None

    async def list_resources(self) -> List[Dict]:
        """List available resources on the server."""
        response = await self.send_request("resources/list")
        if response and "result" in response:
            return response["result"].get("resources", [])
        return []

    async def read_resource(self, uri: str) -> Optional[Dict]:
        """Read a resource from the server."""
        response = await self.send_request("resources/read", {"uri": uri})
        if response and "result" in response:
            return response["result"]
        return None

    async def get_context(self, context_id: str) -> Optional[Dict]:
        """Get context from the server."""
        response = await self.send_request("context/get", {"id": context_id})
        if response and "result" in response:
            return response["result"].get("context")
        return None

    async def set_context(
        self, context_id: str, name: str, data: Dict, expires_in: Optional[int] = None
    ) -> bool:
        """Set context on the server."""
        params = {"id": context_id, "name": name, "data": data}
        if expires_in:
            params["expires_in"] = expires_in

        response = await self.send_request("context/set", params)
        return (
            response
            and "result" in response
            and response["result"].get("created", False)
        )


# Example usage and testing
if __name__ == "__main__":

    async def test_mcp_protocol():
        # Create MCP server
        server = MCPServer(
            "TRAE-AI-MCP",
            capabilities=[
                MCPCapability.TOOLS,
                MCPCapability.RESOURCES,
                MCPCapability.CONTEXT,
            ],
        )

        # Register a sample tool
        def sample_tool(message: str = "Hello") -> str:
            return f"Tool executed with message: {message}"

        server.register_tool(
            MCPTool(
                name="sample_tool",
                description="A sample tool for testing",
                inputSchema={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                },
                handler=sample_tool,
            )
        )

        # Register a sample resource
        server.register_resource(
            MCPResource(
                uri="trae://sample/data",
                name="Sample Data",
                description="Sample data resource",
                mimeType="application/json",
                resourceType=MCPResourceType.JSON,
                content={"key": "value", "timestamp": datetime.now().isoformat()},
            )
        )

        print("MCP Server configured with sample tools and resources")
        print(f"Server info: {server.info.name} v{server.info.version}")
        print(f"Capabilities: {[cap.value for cap in server.info.capabilities]}")
        print(f"Tools: {list(server.tools.keys())}")
        print(f"Resources: {list(server.resources.keys())}")

        # Start server (would run indefinitely in real usage)
        print("\nTo start the server, run: await server.start()")
        print(
            "To connect a client, use: client = MCPClient() and await client.connect('ws://localhost:8765')"
        )

    # Run test
    asyncio.run(test_mcp_protocol())
