from aiogram import Bot
from fastapi import APIRouter, Depends
from fastapi.websockets import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect

import redis
from src.competitions.dependencies import (get_redis, get_room_manager,
                                           get_websocket_manager, get_tg_bot)
from src.competitions.schemas import (CompetitionAnswerSchema,
                                      CompetitionRoomSchema, CompetitionSchema)
from src.competitions.service import (CompetitionService, RoomManager,
                                      RoomService, WebSocketManager)
from src.database import get_async_session

router = APIRouter(
    prefix="/competitions",
    tags=["competitions"]
)


@router.get("/invite-to-room")
async def send_invite_to_room(
        telegram_id: int,
        room_id: int,
        bot: Bot = Depends(get_tg_bot),
        websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    await RoomService.send_invite(telegram_id, room_id, bot, websocket_manager)


@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        session: AsyncSession = Depends(get_async_session),
        websocket_manager: WebSocketManager = Depends(get_websocket_manager),
        room_manager: RoomManager = Depends(get_room_manager)
):
    await websocket.accept()
    data = None
    try:
        while True:
            data = await websocket.receive_json()
            await websocket_manager.add_connection(data["telegram_id"], websocket)
    except WebSocketDisconnect:
        if data and "telegram_id" in data:
            await websocket_manager.remove_connections(data["telegram_id"], session, room_manager)


@router.get("/rooms")
async def get_rooms(session: AsyncSession = Depends(get_async_session),
                    room_manager: RoomManager = Depends(get_room_manager)):
    return await room_manager.get_rooms_list(session)


@router.post("/create-room")
async def create_room(room_data: CompetitionSchema,
                      session: AsyncSession = Depends(get_async_session),
                      websocket_manager: WebSocketManager = Depends(get_websocket_manager),
                      room_manager: RoomManager = Depends(get_room_manager)):
    return await room_manager.create_room(room_data, websocket_manager, session)


@router.post("/join-room")
async def join_room(room_data: CompetitionRoomSchema,
                    session: AsyncSession = Depends(get_async_session),
                    websocket_manager: WebSocketManager = Depends(get_websocket_manager),
                    room_manager: RoomManager = Depends(get_room_manager),
                    redis_client: redis.Redis = Depends(get_redis)):
    room_service = RoomService(session)
    return await room_service.update_user_room_data(room_data, "join", websocket_manager, room_manager, redis_client)


@router.patch("/leave-room")
async def leave_room(room_data: CompetitionRoomSchema,
                     session: AsyncSession = Depends(get_async_session),
                     websocket_manager: WebSocketManager = Depends(get_websocket_manager),
                     room_manager: RoomManager = Depends(get_room_manager),
                     redis_client: redis.Redis = Depends(get_redis)):
    room_service = RoomService(session)
    return await room_service.update_user_room_data(room_data, "leave", websocket_manager, room_manager, redis_client)


@router.get("/start")
async def start(room_id: int, session: AsyncSession = Depends(get_async_session),
                websocket_manager: WebSocketManager = Depends(get_websocket_manager),
                room_manager: RoomManager = Depends(get_room_manager),
                redis_client: redis.Redis = Depends(get_redis)):
    competition_service = CompetitionService(session)
    return await competition_service.start(room_id, websocket_manager, room_manager, redis_client)


@router.patch("/check_answer")
async def check_competition_answer(
        answer_data: CompetitionAnswerSchema,
        session: AsyncSession = Depends(get_async_session),
        websocket_manager: WebSocketManager = Depends(get_websocket_manager),
        room_manager: RoomManager = Depends(get_room_manager),
        redis_client: redis.Redis = Depends(get_redis)
):
    competition_service = CompetitionService(session)
    return await competition_service.check_competition_answer(
        answer_data, websocket_manager, room_manager, redis_client
    )
