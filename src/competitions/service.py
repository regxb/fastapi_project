import json
from asyncio import Lock
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.websockets import WebSocket

from .models import Competitions, CompetitionRoomData
from .query import get_user_room_data, get_competition, get_users_stats, get_rooms
from .schemas import CompetitionRoomSchema, CompetitionAnswerSchema
from ..models import User
from ..quizzes.service import AnswerService, WordService
from ..users.query import get_user
from ..utils import commit_changes_or_rollback


class WebSocketManager:
    def __init__(self):
        self.active_connections = defaultdict(dict)
        self.lock = Lock()

    async def add_connection(self, telegram_id: int, websocket: WebSocket) -> None:
        async with self.lock:
            self.active_connections["non_room"][telegram_id] = websocket

    async def remove_connections(self, telegram_id: int, session: AsyncSession) -> None:
        async with self.lock:
            for room, room_data in self.active_connections.items():
                if telegram_id in room_data:
                    del self.active_connections[room][telegram_id]

                    if room != "non_room":
                        user = await get_user(session, telegram_id)
                        user_room_data = await get_user_room_data(room, user.id, session)
                        await RoomService.change_user_status(user_room_data, "offline", session)
                        await self.room_broadcast_message(room, "Пользователь вышел")

                    return

    async def room_broadcast_message(self, room_id: int, message: str) -> None:
        if room_id in self.active_connections:
            for ws in self.active_connections[room_id].values():
                await ws.send_text(message)

    async def add_websocket_to_room(self, room_id: int, telegram_id: int) -> None:
        async with self.lock:
            ws = self.active_connections["non_room"].pop(telegram_id, None)
            if ws:
                self.active_connections[room_id][telegram_id] = ws

    async def remove_websocket_from_room(self, room_id: int, telegram_id: int) -> None:
        async with self.lock:
            ws = self.active_connections[room_id].pop(telegram_id, None)
            if ws:
                self.active_connections["non_room"][telegram_id] = ws


class RoomService:

    def __init__(self, session: AsyncSession, websocket_manager: WebSocketManager):
        self.session = session
        self.websocket_manager = websocket_manager

    async def get_rooms_list(self):
        return await get_rooms(self.session)

    async def create_room(self):
        new_competitions = Competitions()
        self.session.add(new_competitions)
        await commit_changes_or_rollback(self.session, "Ошибка при создании комнаты")
        return {"room_id": new_competitions.id}

    async def update_user_room_data(self, room_data: CompetitionRoomSchema, action: str):
        telegram_id, room_id = room_data.telegram_id, room_data.room_id
        user = await get_user(self.session, telegram_id)
        user_room_data = await get_user_room_data(room_id, user.id, self.session)

        if action == "join":
            await self.connect_user_to_room(room_id, user.id, user_room_data)
            await self.websocket_manager.room_broadcast_message(room_id, "Пользователь зашел в комнату")
            await self.websocket_manager.add_websocket_to_room(room_id, telegram_id)
        elif action == "leave":
            await self.disconnect_user_from_room(user_room_data)
            await self.websocket_manager.add_websocket_to_room(room_id, telegram_id)
            await self.websocket_manager.room_broadcast_message(room_id, "Пользователь вышел из комнаты")

    async def disconnect_user_from_room(self, user_room_data: CompetitionRoomData):
        user_room_data.user_status = "offline"
        await commit_changes_or_rollback(self.session, "Ошибка при обновлении данных")

    async def connect_user_to_room(self, room_id: int, user_id: int, user_room_data: CompetitionRoomData):
        if not user_room_data:

            new_user_room_data = CompetitionRoomData(competition_id=room_id, user_id=user_id,
                                                     user_status="online")
            self.session.add(new_user_room_data)
            await commit_changes_or_rollback(self.session, "Ошибка при подключении в комнату")
        else:
            user_room_data.user_status = "online"
            await commit_changes_or_rollback(self.session, "Ошибка при подключении в комнату")

    @staticmethod
    async def change_user_status(user_room_data: CompetitionRoomData, status: str, session: AsyncSession) -> None:
        user_room_data.user_status = status
        await commit_changes_or_rollback(session, "Ошибка при обновлении данных")

    @staticmethod
    async def update_room_status(room_id: int, session: AsyncSession) -> None:
        competition_room = await get_competition(room_id, session)
        if competition_room.status == "awaiting":
            competition_room.status = "active"
            await session.commit()


class CompetitionService:

    def __init__(self, session: AsyncSession, websocket_manager: WebSocketManager):
        self.session = session
        self.websocket_manager = websocket_manager

    async def start(self, telegram_id: int, room_id: int):
        await RoomService.update_room_status(room_id, self.session)
        word_service = WordService(self.session)
        response = await word_service.get_random_word(telegram_id)

        await self.websocket_manager.room_broadcast_message(room_id, response.json())

    async def check_competition_answer(self, answer_data: CompetitionAnswerSchema):
        answer_service = AnswerService(self.session)
        result = await answer_service.check_answer(answer_data.word_for_translate_id, answer_data.user_word_id)
        user = await get_user(self.session, answer_data.telegram_id)
        await self.update_competition_statistics(user, answer_data.room_id, result)
        users_stats = await get_users_stats(answer_data.room_id, self.session)
        response = [{"user": {"telegram_id": user.user.telegram_id, "points": user.user_points}} for user in
                    users_stats]

        await self.websocket_manager.room_broadcast_message(answer_data.room_id, json.dumps(response))

    async def update_competition_statistics(self, user: User, room_id: int, result: bool):
        user_room_data = await get_user_room_data(room_id, user.id, self.session)
        user_room_data.user_points += 10 if result else -10
        await commit_changes_or_rollback(self.session, "Ошибка при обновлении данных")
