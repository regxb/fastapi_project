import json
import uuid

import redis.asyncio as redis
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.websockets import WebSocket

from .models import CompetitionRoom, CompetitionRoomData
from .query import get_user_rooms_data, get_competition, get_users_stats, get_rooms, get_users_count_in_room, \
    get_room_data, get_user_room_data
from .schemas import CompetitionRoomSchema, CompetitionAnswerSchema, CompetitionsSchema, CompetitionsAnswersSchema
from ..models import User
from ..quizzes.query import get_translation_words
from ..quizzes.schemas import RandomWordResponse
from ..quizzes.service import WordService, ResponseService
from ..users.query import get_user
from ..utils import commit_changes_or_rollback


class WebSocketManager:
    def __init__(self):
        self.websockets = {}

    async def add_connection(self, telegram_id: int, websocket: WebSocket) -> None:
        self.websockets[telegram_id] = websocket

    async def remove_connections(self, telegram_id: int, session: AsyncSession, room_manager: "RoomManager") -> None:
        self.websockets.pop(telegram_id, None)
        await room_manager.remove_user_from_room(telegram_id)
        await RoomService.change_user_status(telegram_id, "offline", session)

    async def room_broadcast_message(self, room_id: int, message: str, room_manager: "RoomManager") -> None:
        telegram_ids = await room_manager.get_users_in_room(room_id)
        for telegram_id in telegram_ids:
            websocket = self.websockets.get(int(telegram_id))
            if websocket:
                await websocket.send_text(message)

    async def notify_all_users(self, message: str) -> None:
        for websocket in self.websockets.values():
            await websocket.send_text(message)


class RoomManager:

    def __init__(self):
        self.redis = self.redis = redis.from_url("redis://redis:6379")

    @staticmethod
    async def get_rooms_list(session: AsyncSession) -> list[CompetitionRoom]:
        return await get_rooms(session)

    async def create_room(
            self, room_data: CompetitionsSchema, websocket_manager: WebSocketManager, session: AsyncSession
    ) -> None:
        user = await get_user(session, room_data.telegram_id)
        new_room = CompetitionRoom(owner_id=user.id, **room_data.dict(exclude={"telegram_id"}))
        session.add(new_room)
        await commit_changes_or_rollback(session, "Ошибка при создании комнаты")
        await websocket_manager.notify_all_users(self.create_room_message(new_room, user))

    async def add_user_to_room(self, telegram_id: int, room_id: int) -> None:
        await self.redis.sadd(f"room:{room_id}", telegram_id)
        await self.redis.hset("user_room_map", telegram_id, room_id)

    async def remove_user_from_room(self, telegram_id: int, room_id: int = None) -> None:
        if room_id is None:
            room_id = await self.redis.hget("user_room_map", telegram_id)
            if not room_id:
                return
        await self.redis.srem(f"room:{room_id}", telegram_id)
        await self.redis.hdel("user_room_map", telegram_id)

    async def get_users_in_room(self, room_id: int) -> list[int]:
        users = await self.redis.smembers(f"room:{room_id}")
        return [int(user) for user in users]

    @staticmethod
    def create_room_message(room: CompetitionRoom, user: User) -> str:
        return json.dumps({
            "type": "created_new_room",
            "room_data": {
                "room_id": room.id, "owner": user.username,
                "language_from_id": room.language_from_id,
                "language_to_id": room.language_to_id
            }
        })


class RoomService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_user_room_data(
            self, room_data: CompetitionRoomSchema, action: str, websocket_manager: WebSocketManager,
            room_manager: RoomManager
    ):
        telegram_id, room_id = room_data.telegram_id, room_data.room_id
        user = await get_user(self.session, telegram_id)
        room_data = await get_room_data(room_id, self.session)
        user_room_data = await get_user_room_data(room_id, user.id, self.session)

        if action == "join":
            await self.connect_user_to_room(room_id, user.id, user_room_data)
            users_count = await get_users_count_in_room(room_id, self.session)
            await room_manager.add_user_to_room(telegram_id, room_id)
            await websocket_manager.notify_all_users(self.create_user_message("join", user, room_data,
                                                                              users_count))
        elif action == "leave":
            await self.disconnect_user_from_room(user_room_data)
            users_count = await get_users_count_in_room(room_id, self.session)
            await websocket_manager.notify_all_users(self.create_user_message("leave", user, room_data,
                                                                              users_count))
            await room_manager.remove_user_from_room(telegram_id, room_id)

    async def disconnect_user_from_room(self, user_room_data: CompetitionRoomData) -> None:
        user_room_data.user_status = "offline"
        await commit_changes_or_rollback(self.session, "Ошибка при обновлении данных")

    async def connect_user_to_room(self, room_id: int, user_id: int, user_room_data: CompetitionRoomData) -> None:
        if not user_room_data:
            new_user_room_data = CompetitionRoomData(competition_id=room_id, user_id=user_id, user_status="online")
            self.session.add(new_user_room_data)
            await commit_changes_or_rollback(self.session, "Ошибка при подключении в комнату")
        else:
            user_room_data.user_status = "online"
            await commit_changes_or_rollback(self.session, "Ошибка при подключении в комнату")

    @staticmethod
    def create_user_message(action: str, user: User, room_data: CompetitionRoom, users_count: int) -> str:
        return json.dumps({
            "type": f"user_{action}",
            "room_id": room_data.id,
            "username": user.username,
            "status_room": room_data.status,
            "users_count": users_count
        })

    @staticmethod
    async def change_user_status(telegram_id: int, status: str, session: AsyncSession) -> None:
        user = await get_user(session, telegram_id)
        user_rooms_data = await get_user_rooms_data(user.id, session)
        for room in user_rooms_data:
            room.user_status = status
        await commit_changes_or_rollback(session, "Ошибка при обновлении данных")

    @staticmethod
    async def update_room_status(room_id: int, session: AsyncSession) -> None:
        competition_room = await get_competition(room_id, session)
        if competition_room.status == "created":
            competition_room.status = "active"
            await session.commit()


class CompetitionService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def start(self, room_id: int, websocket_manager: WebSocketManager, room_manager: RoomManager) -> None:
        await RoomService.update_room_status(room_id, self.session)
        room_data = await get_competition(room_id, self.session)
        response = await CompetitionService.prepare_competition_words(room_data, self.session)
        await websocket_manager.room_broadcast_message(room_id, response.json(), room_manager)

    @staticmethod
    async def prepare_competition_words(room_data: CompetitionRoom, session: AsyncSession) -> RandomWordResponse:
        word_service = WordService(session)
        random_words = await word_service.get_random_words(room_data.language_from_id, room_data.language_to_id)
        return ResponseService.create_random_word_response(random_words["word_for_translate"],
                                                           random_words["other_words"])

    async def check_competition_answer(self, answer_data: CompetitionAnswerSchema,
                                       websocket_manager: WebSocketManager, room_manager: RoomManager) -> None:
        word_id = answer_data.word_for_translate_id
        translation_word = await get_translation_words(self.session, word_id)
        result = word_id == translation_word.word_id
        user = await get_user(self.session, answer_data.telegram_id)
        await self.update_competition_statistics(user, answer_data.room_id, result)
        users_stats = await get_users_stats(answer_data.room_id, self.session)

        response = await ResponseCompetitionsService.create_competition_answer_response(
            answer_data, user, result, translation_word.id, users_stats, self.session
        )
        await websocket_manager.room_broadcast_message(answer_data.room_id, response.json(), room_manager)

    async def update_competition_statistics(self, user: User, room_id: int, result: bool) -> None:
        user_room_data = await get_user_room_data(room_id, user.id, self.session)
        user_room_data.user_points += 10 if result else -10
        await commit_changes_or_rollback(self.session, "Ошибка при обновлении данных")


class ResponseCompetitionsService:

    @staticmethod
    async def create_competition_answer_response(
            answer_data: CompetitionAnswerSchema, user: User, result: bool, translation_word_id: uuid.UUID,
            users_stats: Sequence[CompetitionRoomData], session: AsyncSession
    ) -> CompetitionsAnswersSchema:
        room_data = await get_room_data(answer_data.room_id, session)
        response_data = {
            "type": "check_competition_answer",
            "answered_user": {
                "username": user.username, "user_photo_url": user.photo_url, "success": result},
            "selected_word_id": str(answer_data.user_word_id),
            "correct_word_id": str(translation_word_id),
            "users": [{
                "username": user.user.username,
                "user_photo_url": user.user.photo_url,
                "points": user.user_points} for user in users_stats],
            "new_question": await CompetitionService.prepare_competition_words(room_data, session)}
        response = CompetitionsAnswersSchema(**response_data)
        return response
