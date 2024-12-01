from fastapi import APIRouter

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect

from src.competitions.schemas import CompetitionRoomSchema, CompetitionAnswerSchema
from src.competitions.service import WebSocketManager, RoomService, CompetitionService
from src.database import get_async_session
from fastapi.websockets import WebSocket


router = APIRouter(
    prefix="/competitions",
    tags=["competitions"]
)

websocket_manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session: AsyncSession = Depends(get_async_session)):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await websocket_manager.add_connection(data["telegram_id"], websocket)
            print(websocket_manager.active_connections)
    except WebSocketDisconnect:
        await websocket_manager.remove_connections(data["telegram_id"], session)
        print(websocket_manager.active_connections)


@router.get("/rooms")
async def get_rooms(session: AsyncSession = Depends(get_async_session)):
    return await get_rooms


@router.post("/create-room")
async def create_room(session: AsyncSession = Depends(get_async_session)):
    room_service = RoomService(session, websocket_manager)
    return await room_service.create_room()


@router.post("/join-room")
async def join_room(room_data: CompetitionRoomSchema, session: AsyncSession = Depends(get_async_session)):
    room_service = RoomService(session, websocket_manager)
    await room_service.update_user_room_data(room_data, "join")


@router.patch("/leave-room")
async def leave_room(room_data: CompetitionRoomSchema, session: AsyncSession = Depends(get_async_session)):
    room_service = RoomService(session, websocket_manager)
    await room_service.update_user_room_data(room_data, "leave")


@router.get("/start")
async def start(telegram_id: int, room_id: int, session: AsyncSession = Depends(get_async_session)):
    competition_service = CompetitionService(session, websocket_manager)
    await competition_service.start(telegram_id, room_id)


@router.patch("/check_answer")
async def check_competition_answer(
        answer_data: CompetitionAnswerSchema,
        session: AsyncSession = Depends(get_async_session)
):
    competition_service = CompetitionService(session, websocket_manager)
    await competition_service.check_competition_answer(answer_data)
