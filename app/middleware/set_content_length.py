from starlette.types import ASGIApp, Receive, Scope, Send, Message
from typing import List, Tuple, Optional

class SetContentLengthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Buffer to collect response data
        response_started = False
        start_message: Optional[Message] = None
        body_parts: List[bytes] = []
        
        async def send_wrapper(message: Message):
            nonlocal response_started, start_message, body_parts
            
            if message["type"] == "http.response.start":
                # Buffer the start message until we have the complete body
                start_message = message
                response_started = True
                
            elif message["type"] == "http.response.body":
                # Collect body parts
                body = message.get("body", b"")
                if body:
                    body_parts.append(body)
                
                # If this is the last body message, calculate total length and send everything
                if not message.get("more_body", False):
                    # Calculate total body length using user's code snippet
                    total_body = b"".join(body_parts)
                    body_bytes = total_body if isinstance(total_body, (bytes, bytearray)) else str(total_body).encode("utf-8")
                    
                    # Prepare headers with Content-Length
                    headers = list(start_message.get("headers", []))
                    
                    # Remove any existing Content-Length header
                    headers = [(k, v) for k, v in headers if k.lower() != b"content-length"]
                    
                    # Add Content-Length header using user's code snippet logic
                    headers.append((b"content-length", str(len(body_bytes)).encode()))
                    
                    # Send the start message with updated headers
                    updated_start_message = {**start_message, "headers": headers}
                    await send(updated_start_message)
                    
                    # Send the complete body
                    body_message = {
                        "type": "http.response.body",
                        "body": body_bytes,
                        "more_body": False
                    }
                    await send(body_message)
                else:
                    # More body parts coming, just buffer this one
                    pass
            else:
                # Pass through other message types
                await send(message)
        
        await self.app(scope, receive, send_wrapper)