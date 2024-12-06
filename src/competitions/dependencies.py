import redis.asyncio as redis

from src.competitions.service import RoomManager, WebSocketManager

websocket_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    return websocket_manager


redis_pool = redis.ConnectionPool.from_url("redis://redis:6379", max_connections=10)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)


room_manager = RoomManager(get_redis())


def get_room_manager() -> RoomManager:
    return room_manager
