from fastapi import APIRouter

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect

from src.competitions.schemas import CompetitionRoomSchema, CompetitionAnswerSchema, CompetitionsSchema
from src.competitions.service import WebSocketManager, RoomService, CompetitionService
from src.database import get_async_session
from fastapi.websockets import WebSocket


router = APIRouter(
    prefix="/competitions",
    tags=["competitions"]
)

websocket_manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await websocket_manager.add_connection(data["telegram_id"], websocket)
    except WebSocketDisconnect:
        await websocket_manager.remove_connections(data["telegram_id"])


@router.get("/rooms")
async def get_rooms(session: AsyncSession = Depends(get_async_session)):
    room_service = RoomService(session, websocket_manager)
    return await room_service.get_rooms_list()


@router.post("/create-room")
async def create_room(room_data: CompetitionsSchema, session: AsyncSession = Depends(get_async_session)):
    room_service = RoomService(session, websocket_manager)
    return await room_service.create_room(room_data)


@router.post("/join-room")
async def join_room(room_data: CompetitionRoomSchema, session: AsyncSession = Depends(get_async_session)):
    room_service = RoomService(session, websocket_manager)
    await room_service.update_user_room_data(room_data, "join")


@router.patch("/leave-room")
async def leave_room(room_data: CompetitionRoomSchema, session: AsyncSession = Depends(get_async_session)):
    room_service = RoomService(session, websocket_manager)
    await room_service.update_user_room_data(room_data, "leave")


@router.get("/start")
async def start(room_id: int, session: AsyncSession = Depends(get_async_session)):
    competition_service = CompetitionService(session, websocket_manager)
    await competition_service.start(room_id)


@router.patch("/check_answer")
async def check_competition_answer(
        answer_data: CompetitionAnswerSchema,
        session: AsyncSession = Depends(get_async_session)
):
    competition_service = CompetitionService(session, websocket_manager)
    await competition_service.check_competition_answer(answer_data)
