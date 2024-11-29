import uuid

from fastapi import APIRouter, HTTPException
import json

from fastapi import Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect

from src import CompetitionRoomData, Competitions
from src.competitions.schemas import CompetitionRoomSchema
from src.database import get_async_session
from src.models import User
from src.quizzes.query import get_random_word_for_translate, get_random_words
from src.quizzes.service import AnswerService
from src.quizzes.utils import add_word_for_translate_to_other_words, shuffle_random_words
from src.users.query import get_user
from fastapi.websockets import WebSocket

router = APIRouter(
    prefix="/competitions",
    tags=["competitions"]
)

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Example</title>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <p id="server-message">No messages yet</p>
        <script>
            const ws = new WebSocket("ws://localhost:1234/competitions/ws");

            ws.onmessage = function(event) {
                document.getElementById("server-message").textContent = "Message from server: " + event.data;
            };

            ws.onopen = function() {
                ws.send("hello!");
            };
        </script>
    </body>
</html>
"""

active_connections = {"non_room": {}}


@router.get("/")
async def get():
    return HTMLResponse(html)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session: AsyncSession = Depends(get_async_session)):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            telegram_id = data["telegram_id"]
            active_connections["non_room"].update({telegram_id: websocket})
    except WebSocketDisconnect:
        for room, room_data in active_connections.items():
            if telegram_id in room_data:
                room_id = room
        del active_connections[room_id][telegram_id]
        user = await get_user(session, telegram_id)
        query = (select(CompetitionRoomData)
                 .where(and_(CompetitionRoomData.competition_id == room_id,
                             CompetitionRoomData.user_id == user.id)))
        user_room_data = await session.scalar(query)
        user_room_data.user_status = "offline"
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при подключении в комнату")
        for ws in active_connections[room_id].values():
            await ws.send_text("Потеряно соединения с пользователем")


@router.post("/create-room")
async def create_room(session: AsyncSession = Depends(get_async_session)):
    new_competitions = Competitions()
    session.add(new_competitions)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при создании комнаты")
    return {"room_id": new_competitions.id}


@router.post("/join-room")
async def join_room(room_data: CompetitionRoomSchema, session: AsyncSession = Depends(get_async_session)):
    user = await get_user(session, room_data.telegram_id)
    query = (select(CompetitionRoomData)
             .where(and_(CompetitionRoomData.competition_id == room_data.room_id,
                         CompetitionRoomData.user_id == user.id)))
    user_room_data = await session.scalar(query)
    if not user_room_data:
        new_user_room_data = CompetitionRoomData(competition_id=room_data.room_id, user_id=user.id,
                                                 user_status="online")
        session.add(new_user_room_data)
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при подключении в комнату")
    else:
        user_room_data.user_status = "online"
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при подключении в комнату")
    telegram_id = room_data.telegram_id
    room_id = room_data.room_id
    if active_connections.get(room_id):
        for ws in active_connections[room_id].values():
            await ws.send_text("Пользователь зашел в комнату")
    ws = active_connections["non_room"][telegram_id]
    if not active_connections.get(room_id):
        active_connections[room_id] = {telegram_id: ws}
    else:
        active_connections[room_id].update({telegram_id: ws})
    del active_connections["non_room"][telegram_id]


@router.patch("/leave-room")
async def leave_room(room_data: CompetitionRoomSchema, session: AsyncSession = Depends(get_async_session)):
    telegram_id = room_data.telegram_id
    room_id = room_data.room_id
    user = await get_user(session, telegram_id)
    query = (select(CompetitionRoomData)
             .where(and_(CompetitionRoomData.competition_id == room_id,
                         CompetitionRoomData.user_id == user.id)))
    user_room_data = await session.scalar(query)
    user_room_data.user_status = "offline"
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при подключении в комнату")
    print(active_connections)
    ws = active_connections[room_id][telegram_id]
    del active_connections[room_id][telegram_id]
    active_connections["non_room"].update({telegram_id: ws})
    print(active_connections)
    for ws in active_connections[room_id].values():
        await ws.send_text("Пользователь вышел из комнату")


@router.get("/start")
async def start(telegram_id: int, room_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Competitions).where(Competitions.id == room_id)
    competition_room = await session.scalar(query)
    if competition_room.status == "awaiting":
        competition_room.status = "active"
        await session.commit()
    user = await get_user(session, telegram_id)
    word_for_translate = await get_random_word_for_translate(session, user.learning_language_from_id)
    other_words = await get_random_words(session, user.learning_language_to_id, word_for_translate.id)
    add_word_for_translate_to_other_words(other_words, word_for_translate)
    shuffle_random_words(other_words)
    response = {"word_for_translate": {"name": word_for_translate.name, "id": str(word_for_translate.id)},
                "other_words": [{"name": w.name, "id": str(w.id)} for w in other_words]}
    for connection in active_connections[room_id].values():
        await connection.send_text(json.dumps(response))


@router.patch("/check_answer")
async def check_competition_answer(
        word_for_translate_id: uuid.UUID,
        user_word_id: uuid.UUID,
        telegram_id: int,
        room_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    user = await get_user(session, telegram_id)
    answer_service = AnswerService(session)
    result = await answer_service.check_answer(word_for_translate_id, user_word_id)
    await update_competition_statistics(user, room_id, result, session)
    query = (select(CompetitionRoomData)
             .options(joinedload(CompetitionRoomData.user))
             .where(CompetitionRoomData.competition_id == room_id))
    result = await session.execute(query)
    users_stats = result.scalars().all()
    response = [{"user": {"telegram_id": user.user.telegram_id, "points": user.user_points}} for user in users_stats]
    for connection in active_connections[room_id].values():
        await connection.send_text(json.dumps(response))


async def update_competition_statistics(user: User, room_id: int, result: bool, session: AsyncSession):
    query = (select(CompetitionRoomData)
             .join(Competitions)
             .where(and_(CompetitionRoomData.user_id == user.id, Competitions.id == room_id)))
    user_stats = await session.scalar(query)
    user_stats.user_points += 10 if result else -10
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при обновлении данных")
    return user_stats
