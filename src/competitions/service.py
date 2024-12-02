import json
import uuid
import redis.asyncio as redis
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.websockets import WebSocket

from .models import CompetitionRoom, CompetitionRoomData
from .query import get_user_room_data, get_competition, get_users_stats, get_rooms, get_users_count_in_room
from .schemas import CompetitionRoomSchema, CompetitionAnswerSchema, CompetitionsSchema, CompetitionsAnswersSchema
from ..models import User
from ..quizzes.query import get_translation_words
from ..quizzes.service import WordService, ResponseService
from ..users.query import get_user
from ..utils import commit_changes_or_rollback


class WebSocketManager:
    def __init__(self):
        self.redis = redis.from_url("redis://redis:6379")
        self.websockets = {}

    async def add_connection(self, telegram_id: int, websocket: WebSocket) -> None:
        self.websockets[telegram_id] = websocket
        await self.redis.sadd("non_room", telegram_id)

    async def remove_connections(self, telegram_id: int) -> None:
        self.websockets.pop(telegram_id, None)
        room_id = await self.redis.hget("user_room_map", telegram_id)
        if room_id:
            await self.redis.srem(f"room:{room_id.decode()}", telegram_id)
            await self.redis.hdel("user_room_map", telegram_id)
        await self.redis.srem("non_room", telegram_id)

    async def room_broadcast_message(self, room_id: int, message: str) -> None:
        telegram_ids = await self.redis.smembers(f"room:{room_id}")

        for telegram_id in telegram_ids:
            telegram_id = int(telegram_id)
            websocket = self.websockets.get(telegram_id)
            if websocket:
                await websocket.send_text(message)

    async def add_websocket_to_room(self, room_id: int, telegram_id: int) -> None:
        await self.redis.srem("non_room", telegram_id)
        await self.redis.sadd(f"room:{room_id}", telegram_id)
        await self.redis.hset("user_room_map", telegram_id, room_id)

    async def remove_websocket_from_room(self, room_id: int, telegram_id: int) -> None:
        await self.redis.srem(f"room:{room_id}", telegram_id)
        await self.redis.hdel("user_room_map", telegram_id)
        await self.redis.sadd("non_room", telegram_id)


class RoomService:

    def __init__(self, session: AsyncSession, websocket_manager: WebSocketManager):
        self.session = session
        self.websocket_manager = websocket_manager

    async def get_rooms_list(self):
        return await get_rooms(self.session)

    async def create_room(self, room_data: CompetitionsSchema):
        user = await get_user(self.session, room_data.telegram_id)
        new_competitions = CompetitionRoom(owner_id=user.id, **room_data.dict(exclude={"telegram_id"}))
        self.session.add(new_competitions)
        await commit_changes_or_rollback(self.session, "Ошибка при создании комнаты")
        return {"room_id": new_competitions.id}

    async def update_user_room_data(self, room_data: CompetitionRoomSchema, action: str):
        telegram_id, room_id = room_data.telegram_id, room_data.room_id
        user = await get_user(self.session, telegram_id)
        user_room_data = await get_user_room_data(room_id, user.id, self.session)

        if action == "join":
            await self.connect_user_to_room(room_id, user.id, user_room_data)
            users_count = await get_users_count_in_room(room_id, self.session)
            await self.websocket_manager.add_websocket_to_room(room_id, telegram_id)
            await self.websocket_manager.room_broadcast_message(room_id, json.dumps({"action": "join",
                                                                                     "id": telegram_id,
                                                                                     "users_count": users_count}))
        elif action == "leave":
            await self.disconnect_user_from_room(user_room_data)
            users_count = await get_users_count_in_room(room_id, self.session)
            await self.websocket_manager.room_broadcast_message(room_id, json.dumps({"action": "leave",
                                                                                     "id": telegram_id,
                                                                                     "users_count": users_count}))
            await self.websocket_manager.remove_websocket_from_room(room_id, telegram_id)

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
        if competition_room.status == "created":
            competition_room.status = "active"
            await session.commit()


class CompetitionService:

    def __init__(self, session: AsyncSession, websocket_manager: WebSocketManager):
        self.session = session
        self.websocket_manager = websocket_manager

    async def start(self, room_id: int):
        await RoomService.update_room_status(room_id, self.session)
        room_data = await get_competition(room_id, self.session)
        word_service = WordService(self.session)
        random_words = await word_service.get_random_words(room_data.language_from_id, room_data.language_to_id)
        response = ResponseService.create_random_word_response(random_words["word_for_translate"],
                                                               random_words["other_words"])

        await self.websocket_manager.room_broadcast_message(room_id, response.json())

    async def check_competition_answer(self, answer_data: CompetitionAnswerSchema):
        word_id = answer_data.word_for_translate_id
        translation_word = await get_translation_words(self.session, word_id)
        result = word_id == translation_word.word_id
        user = await get_user(self.session, answer_data.telegram_id)
        await self.update_competition_statistics(user, answer_data.room_id, result)
        users_stats = await get_users_stats(answer_data.room_id, self.session)

        response = ResponseCompetitionsService.create_competition_answer_response(answer_data, result,
                                                                                  translation_word.id, users_stats)
        await self.websocket_manager.room_broadcast_message(answer_data.room_id, response.json())

    async def update_competition_statistics(self, user: User, room_id: int, result: bool):
        user_room_data = await get_user_room_data(room_id, user.id, self.session)
        user_room_data.user_points += 10 if result else -10
        await commit_changes_or_rollback(self.session, "Ошибка при обновлении данных")


class ResponseCompetitionsService:

    @staticmethod
    def create_competition_answer_response(answer_data: CompetitionAnswerSchema, result: bool,
                                           translation_word_id: uuid.UUID, users_stats: Sequence[CompetitionRoomData]):
        response_data = {"answered_user": {"telegram_id": answer_data.telegram_id, "success": result},
                         "selected_word_id": str(answer_data.user_word_id),
                         "correct_word_id": str(translation_word_id),
                         "users": [{"telegram_id": user.user.telegram_id, "points": user.user_points} for user in
                                   users_stats]}
        response = CompetitionsAnswersSchema(**response_data)
        return response
