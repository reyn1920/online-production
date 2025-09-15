from starlette.types import ASGIApp, Receive, Scope, Send, Message

class StripContentLengthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                # Drop any Content-Length header that a handler/middleware may have set
                headers = [
                    (k, v) for (k, v) in message["headers"]
                    if k.lower() != b"content-length"
# BRACKET_SURGEON: disabled
#                 ]
                message = {**message, "headers": headers}
            await send(message)
        await self.app(scope, receive, send_wrapper)