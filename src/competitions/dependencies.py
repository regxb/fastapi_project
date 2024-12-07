from src.competitions.service import RoomManager, WebSocketManager
from src.database import get_redis
from src.words.service import CacheRedisService

websocket_manager = WebSocketManager()
room_manager = RoomManager(get_redis())


def get_websocket_manager() -> WebSocketManager:
    return websocket_manager


def get_room_manager() -> RoomManager:
    return room_manager


def get_cache_service():
    return CacheRedisService(get_redis())
