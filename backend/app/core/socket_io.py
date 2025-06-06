import socketio
from app.core.config import settings

# Define the Socket.IO server instance in a central place
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_origins,
    logger=True,
    engineio_logger=True
) 