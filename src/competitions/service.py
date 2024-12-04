import asyncio
import json

import redis.asyncio as redis
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.websockets import WebSocket

from .models import CompetitionRoom, CompetitionRoomData
from .query import get_user_rooms_data, get_competition, get_all_users_stats, get_rooms, get_users_count_in_room, \
    get_room_data, get_user_room_data, check_user_in_room
from .schemas import CompetitionRoomSchema, CompetitionAnswerSchema, CompetitionSchema, CompetitionsAnswersSchema, \
    CompetitionAnswerError
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
        await RoomService.change_user_status(telegram_id, "offline", session)
        await room_manager.remove_user_from_room(telegram_id, self, session)

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
    async def get_rooms_list(session: AsyncSession) -> list:
        async with session:
            rooms = await get_rooms(session)
            rooms_list = []
            for room, online_count in rooms:
                room = room.__dict__
                room.update({"online_count": online_count})
                rooms_list.append(room)
            return rooms_list

    async def create_room(
            self, room_data: CompetitionSchema, websocket_manager: WebSocketManager, session: AsyncSession
    ) -> None:
        async with session as session:
            user = await get_user(session, room_data.telegram_id)
            new_room = CompetitionRoom(owner_id=user.id, **room_data.dict(exclude={"telegram_id"}))
            session.add(new_room)
            await commit_changes_or_rollback(session, "Ошибка при создании комнаты")
            await websocket_manager.notify_all_users(self.__create_room_message(new_room, user))

    async def add_user_to_room(self, telegram_id: int, room_id: int) -> None:
        await self.redis.sadd(f"room:{room_id}", telegram_id)
        await self.redis.hset("user_room_map", telegram_id, room_id)

    async def remove_user_from_room(
            self, telegram_id: int, websocket_manager: WebSocketManager, session: AsyncSession, room_id: int = None
    ) -> None:
        if room_id is None:
            room_id = await self.redis.hget("user_room_map", telegram_id)
            if not room_id:
                return
            user = await get_user(session, telegram_id)
            room_data = await get_room_data(int(room_id), session)
            users_count = await get_users_count_in_room(int(room_id), session)
            await RoomService.update_room_status(int(room_id), session, "pause")
            users_stats = await get_all_users_stats(int(room_id), session)
            await websocket_manager.notify_all_users(RoomService.create_user_message("leave", user, room_data,
                                                                                     users_count, users_stats))
        await self.redis.srem(f"room:{int(room_id)}", telegram_id)
        await self.redis.hdel("user_room_map", telegram_id)

    async def get_users_in_room(self, room_id: int) -> list[int]:
        users = await self.redis.smembers(f"room:{room_id}")
        return [int(user) for user in users]

    def __create_room_message(self, room: CompetitionRoom, user: User) -> str:
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
        async with self.session as session:
            telegram_id, room_id = room_data.telegram_id, room_data.room_id
            user = await get_user(session, telegram_id)
            room_data = await get_room_data(room_id, session)
            user_room_data = await get_user_room_data(room_id, user.id, session)

            if action == "join":
                await self.user_join(room_id, telegram_id, user.id, user_room_data, room_manager)

            elif action == "leave":
                await self.user_leave(room_id, telegram_id, user_room_data, room_manager, websocket_manager)

            users_count = await get_users_count_in_room(room_id, session)
            users_stats = await get_all_users_stats(room_id, self.session)
            await websocket_manager.notify_all_users(self.create_user_message(action, user, room_data, users_count,
                                                                              users_stats))

    async def user_join(self, room_id: int, telegram_id: int, user_id: int, user_room_data: CompetitionRoomData,
                        room_manager: RoomManager):
        room_data = await get_room_data(room_id, self.session)
        user = await get_user(self.session, telegram_id)
        if room_data.owner_id == user.id:
            await self.update_room_status(room_id, self.session, "active")
            await commit_changes_or_rollback(self.session, "Ошибка при обновлении данных")
        await self.__change_user_status_to_online(room_id, user_id, user_room_data)
        await room_manager.add_user_to_room(telegram_id, room_id)

    async def user_leave(self, room_id: int, telegram_id: int, user_room_data: CompetitionRoomData,
                         room_manager: RoomManager, websocket_manager: WebSocketManager):
        room_data = await get_room_data(room_id, self.session)
        user = await get_user(self.session, telegram_id)
        if room_data.owner_id == user.id:
            await self.update_room_status(room_id, self.session, "pause")
            await commit_changes_or_rollback(self.session, "Ошибка при обновлении данных")
        await self.__change_user_status_to_offline(user_room_data)
        await room_manager.remove_user_from_room(telegram_id, websocket_manager, self.session, room_id)

    async def __change_user_status_to_offline(self, user_room_data: CompetitionRoomData) -> None:
        async with self.session as session:
            user_room_data.user_status = "offline"
            await commit_changes_or_rollback(session, "Ошибка при обновлении данных")

    async def __change_user_status_to_online(self, room_id: int, user_id: int,
                                             user_room_data: CompetitionRoomData) -> None:
        async with self.session as session:
            if not user_room_data:
                await self.__create_user_room_data(room_id, user_id)
            else:
                user_room_data.user_status = "online"
                await commit_changes_or_rollback(session, "Ошибка при подключении в комнату")

    async def __create_user_room_data(self, room_id: int, user_id: int) -> None:
        async with self.session as session:
            new_user_room_data = CompetitionRoomData(competition_id=room_id, user_id=user_id, user_status="online")
            session.add(new_user_room_data)
            await commit_changes_or_rollback(session, "Ошибка при подключении в комнату")

    @staticmethod
    def create_user_message(action: str, user: User, room_data: CompetitionRoom, users_count: int,
                            users_stats: Sequence[CompetitionRoomData]) -> str:
        return json.dumps({
            "type": f"user_{action}",
            "room_id": room_data.id,
            "username": user.username,
            "status_room": room_data.status,
            "users_count": users_count,
            "users": [{
                "username": user.user.username,
                "user_photo_url": user.user.photo_url,
                "points": user.user_points} for user in users_stats]
        })

    @staticmethod
    async def change_user_status(telegram_id: int, status: str, session: AsyncSession) -> None:
        async with session:
            user = await get_user(session, telegram_id)
            user_rooms_data = await get_user_rooms_data(user.id, session)
            for room in user_rooms_data:
                room.user_status = status
            await commit_changes_or_rollback(session, "Ошибка при обновлении данных")

    @staticmethod
    async def update_room_status(room_id: int, session: AsyncSession, status: str = None) -> None:
        competition_room = await get_competition(room_id, session)
        if status:
            competition_room.status = status
            await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
            return
        if competition_room.status != "active":
            competition_room.status = "active"
            await commit_changes_or_rollback(session, "Ошибка при обновлении данных")


class CompetitionService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def start(self, room_id: int, websocket_manager: WebSocketManager, room_manager: RoomManager):
        async with self.session as session:
            owner_in_room = await check_user_in_room(room_id, session)
            if not owner_in_room:
                return await websocket_manager.room_broadcast_message(
                    room_id, json.dumps({"type": "error", "message": "owner_not_in_room"}), room_manager
                )
            await RoomService.update_room_status(room_id, session)
            room_data = await get_competition(room_id, session)
            response = await CompetitionService.prepare_competition_words(room_data, session)
            await websocket_manager.room_broadcast_message(room_id, response.json(), room_manager)

    @staticmethod
    async def prepare_competition_words(room_data: CompetitionRoom, session: AsyncSession) -> RandomWordResponse:
        async with session:
            word_service = WordService(session)
            random_words = await word_service.get_random_words(room_data.language_from_id, room_data.language_to_id)
            return ResponseService.create_random_word_response(random_words["word_for_translate"],
                                                               random_words["other_words"])

    async def check_competition_answer(self, answer_data: CompetitionAnswerSchema,
                                       websocket_manager: WebSocketManager, room_manager: RoomManager):
        result = await self.__check_answer(answer_data)
        await self.__update_user_statistics(answer_data, result)
        users_stats = await self.get_users_stats(answer_data.room_id)
        response = await ResponseCompetitionsService.create_competition_answer_response(
            answer_data, result, users_stats, self.session
        )
        room_data = await get_room_data(answer_data.room_id, self.session)
        if room_data.status == "active":
            await websocket_manager.room_broadcast_message(answer_data.room_id, response.json(), room_manager)
            await asyncio.sleep(3)
            new_question = await ResponseCompetitionsService.create_new_questions_response(answer_data, self.session)
            await websocket_manager.room_broadcast_message(answer_data.room_id, new_question.json(), room_manager)
            return
        response = {"type": "error", "room_id": answer_data.room_id, "message": "owner_not_in_room"}
        await websocket_manager.room_broadcast_message(answer_data.room_id, CompetitionAnswerError(**response).json(),
                                                       room_manager)

    async def __check_answer(self, answer_data: CompetitionAnswerSchema) -> bool:
        async with self.session as session:
            translation_word = await get_translation_words(session, answer_data.word_for_translate_id)
            return answer_data.user_word_id == translation_word.id

    async def __update_user_statistics(self, answer_data: CompetitionAnswerSchema, result: bool) -> None:
        async with self.session as session:
            user = await get_user(session, answer_data.telegram_id)
            await self.__update_competition_statistics(user, answer_data.room_id, result)

    async def get_users_stats(self, room_id: int) -> Sequence[CompetitionRoomData]:
        async with self.session as session:
            return await get_all_users_stats(room_id, session)

    async def __update_competition_statistics(self, user: User, room_id: int, result: bool) -> None:
        async with self.session as session:
            user_room_data = await get_user_room_data(room_id, user.id, session)
            user_room_data.user_points += 10 if result else -10
            await commit_changes_or_rollback(session, "Ошибка при обновлении данных")


class ResponseCompetitionsService:

    @staticmethod
    async def create_competition_answer_response(
            answer_data: CompetitionAnswerSchema, result: bool,
            users_stats: Sequence[CompetitionRoomData], session: AsyncSession):
        async with session:
            room_data = await get_room_data(answer_data.room_id, session)
            if room_data.status == "active":
                user = await get_user(session, answer_data.telegram_id)
                translation_word = await get_translation_words(session, answer_data.word_for_translate_id)

                response_data = {
                    "type": "check_competition_answer",
                    "answered_user": {
                        "username": user.username, "user_photo_url": user.photo_url, "success": result},
                    "selected_word_id": str(answer_data.user_word_id),
                    "correct_word_id": str(translation_word.id),
                    "users": [{
                        "username": user.user.username,
                        "user_photo_url": user.user.photo_url,
                        "points": user.user_points} for user in users_stats]
                }
                response = CompetitionsAnswersSchema(**response_data)
                return response
            response = {"type": "error", "room_id": answer_data.room_id, "message": "owner_leave"}
            return CompetitionAnswerError(**response)

    @staticmethod
    async def create_new_questions_response(answer_data: CompetitionAnswerSchema, session: AsyncSession):
        room_data = await get_room_data(answer_data.room_id, session)
        if room_data.status == "active":
            new_question = await CompetitionService.prepare_competition_words(room_data, session)
            return new_question
        response = {"type": "error", "room_id": answer_data.room_id, "message": "owner_leave"}
        return CompetitionAnswerError(**response)
