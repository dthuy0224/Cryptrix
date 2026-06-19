from typing import Dict, List, Set
from fastapi import WebSocket
from app.utils.logger import logger

class WebSocketManager:
    """
    Manages active real-time client WebSocket connections.
    Includes grouping clients by cryptocurrency channel (e.g. BTC, ETH).
    Ready for integration with message brokers like Kafka or Redis PubSub.
    """
    def __init__(self):
        # Master list of all active connections
        self.active_connections: Set[WebSocket] = set()
        
        # Grouped subscriptions: channels mapping to sets of clients
        self.channel_subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """Accepts a client socket connection and adds it to the pool."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New client socket accepted. Total pool size: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Removes a client socket connection from the pool and channels."""
        self.active_connections.discard(websocket)
        
        # Remove from channel groupings
        for channel, clients in list(self.channel_subscriptions.items()):
            clients.discard(websocket)
            if not clients:
                del self.channel_subscriptions[channel]
                
        logger.info(f"Client socket disconnected. Total pool size: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribes an active socket to a specific coin/metric stream."""
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
        self.channel_subscriptions[channel].add(websocket)
        logger.info(f"Socket subscribed to channel: {channel}")

    async def broadcast_to_channel(self, channel: str, message: dict):
        """Sends a JSON message to all clients subscribed to a specific channel."""
        subscribers = self.channel_subscriptions.get(channel, set())
        if not subscribers:
            return
            
        dead_sockets: List[WebSocket] = []
        for connection in subscribers:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to transmit payload on channel '{channel}': {e}")
                dead_sockets.append(connection)

        # Cleanup terminated sockets discovered during transmission
        for dead_socket in dead_sockets:
            self.disconnect(dead_socket)

    async def broadcast_global(self, message: dict):
        """Sends a JSON message to every active WebSocket client."""
        if not self.active_connections:
            return
            
        dead_sockets: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to transmit global payload: {e}")
                dead_sockets.append(connection)

        # Cleanup
        for dead_socket in dead_sockets:
            self.disconnect(dead_socket)

# Global singleton WebSocket Manager
ws_manager = WebSocketManager()
