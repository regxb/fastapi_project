from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.competitions.dependencies import get_websocket_manager
from src.competitions.service import WebSocketManager
from src.database import get_async_session
from src.users.schemas import UserCreate, UserInfo, UserUpdate, UsersSchema
from src.users.service import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"]
)


@router.post("", response_model=UserInfo)
async def create_user(user_data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    user = UserService(session)
    return await user.create_user(user_data)


@router.get("", response_model=UsersSchema)
async def get_users(
        page: int = Query(ge=1, default=0),
        size: int = Query(ge=1, le=100),
        session: AsyncSession = Depends(get_async_session)
):
    user = UserService(session)
    return await user.get_users(page, size)


@router.get("/online-users", response_model=UsersSchema)
async def get_online_users(
        page: int = Query(ge=1, default=0),
        size: int = Query(ge=1, le=100),
        session: AsyncSession = Depends(get_async_session),
        websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    user = UserService(session)
    return await user.get_online_users(page, size, websocket_manager)


@router.get("/find-user")
async def find_user_by_username(username: str, session: AsyncSession = Depends(get_async_session)):
    user = UserService(session)
    return await user.find_user_by_username(username)


@router.get("/{telegram_id}", response_model=UserInfo)
async def get_user_info(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    user = UserService(session)
    return await user.get_user_info(telegram_id)


@router.patch("/change-user-language")
async def change_user_language(user_data: UserUpdate, session: AsyncSession = Depends(get_async_session)):
    user = UserService(session)
    return await user.change_user_language(user_data)
