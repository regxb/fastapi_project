import uuid

from fastapi import APIRouter, HTTPException
import json

from fastapi import Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect

from src import CompetitionStatistics, Competitions
from src.database import get_async_session
from src.models import User
from src.quizzes.query import get_random_word_for_translate, get_random_words
from src.quizzes.service import QuizService
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
        <title>ws</title>
    </head>
    <body>
        <p id="server-message">No messages yet</p>
        <script>
            const telegram_id = 1;
            const ws = new WebSocket(`ws://localhost:8000/competitions/ws/${telegram_id}`);

            ws.onmessage = function(event) {
                document.getElementById("server-message").textContent = "Message from server: " + event.data;
            };

        </script>
    </body>
</html>

"""

active_connections = {}


@router.get("/")
async def get():
    return HTMLResponse(html)


@router.websocket("/ws/{room_id}/{telegram_id}")
async def websocket_endpoint(websocket: WebSocket, telegram_id: int):
    await websocket.accept()
    connection_id = telegram_id
    active_connections[connection_id] = websocket
    print(active_connections)
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
    except WebSocketDisconnect:
        del active_connections[connection_id]
        print("Disconnected")


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


@router.post("/join-room/{rom_id}")
async def join_room(telegram_id: int, room_id: int, session: AsyncSession = Depends(get_async_session)):
    user = await get_user(session, telegram_id)
    query = (select(CompetitionStatistics)
             .where(and_(CompetitionStatistics.competition_id == room_id, CompetitionStatistics.user_id == user.id)))
    statistics_room_exists = await session.scalar(query)
    query = select(Competitions).where(Competitions.id == room_id)
    competition_room_exists = await session.scalar(query)
    if not competition_room_exists:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    if not statistics_room_exists:
        new_competitions_statistics = CompetitionStatistics(competition_id=room_id, user_id=user.id)
        session.add(new_competitions_statistics)
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при создании статистики комнаты")
    return {"room_id": room_id, "message": f"Пользователь зашел в комнату {room_id}"}


@router.get("/start")
async def start(telegram_id: int, room_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Competitions).where(Competitions.id == room_id)
    competition_room = await session.scalar(query)
    if competition_room.status == "awaiting":
        competition_room.status = "active"
    user = await get_user(session, telegram_id)
    word_for_translate = await get_random_word_for_translate(session, user.learning_language_from_id)
    other_words = await get_random_words(session, user.learning_language_to_id, word_for_translate.id)
    add_word_for_translate_to_other_words(other_words, word_for_translate)
    shuffle_random_words(other_words)
    response = {"word_for_translate": {"name": word_for_translate.name, "id": str(word_for_translate.id)},
                "other_words": [{"name": w.name, "id": str(w.id)} for w in other_words]}
    for connection in active_connections:
        await active_connections[connection].send_text(json.dumps(response))


@router.patch("/check_answer")
async def check_competition_answer(
        word_for_translate_id: uuid.UUID,
        user_word_id: uuid.UUID,
        telegram_id: int,
        room_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    query = (select(CompetitionStatistics)
             .options(joinedload(CompetitionStatistics.user))
             .where(CompetitionStatistics.competition_id == room_id))
    result = await session.execute(query)
    users_stats = result.scalars().all()
    user = await get_user(session, telegram_id)
    quiz_service = QuizService(session)
    result = await quiz_service.check_answer(word_for_translate_id, user_word_id)
    await update_competition_statistics(user, room_id, result, session)
    return [{"user": {"telegram_id": user.user.telegram_id, "points": user.user_points}} for user in users_stats]


async def update_competition_statistics(user: User, room_id: int, result: bool, session: AsyncSession):
    query = (select(CompetitionStatistics)
             .join(Competitions)
             .where(and_(CompetitionStatistics.user_id == user.id, Competitions.id == room_id)))
    user_stats = await session.scalar(query)
    user_stats.user_points += 10 if result else -10
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при обновлении данных")
