from src.competitions.service import RoomManager, WebSocketManager

room_manager = RoomManager()
websocket_manager = WebSocketManager()


def get_room_manager() -> RoomManager:
    return room_manager


def get_websocket_manager() -> WebSocketManager:
    return websocket_manager
