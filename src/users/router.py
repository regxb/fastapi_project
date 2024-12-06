from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.users.schemas import UserCreate, UserInfo, UserUpdate
from src.users.service import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"]
)


@router.post("", response_model=UserInfo)
async def create_user(user_data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    user = UserService(session)
    return await user.create_user(user_data)


@router.get("", response_model=List[UserInfo])
async def get_users_list(session: AsyncSession = Depends(get_async_session)):
    user = UserService(session)
    return await user.get_users_list()


@router.get("/{telegram_id}", response_model=UserInfo)
async def get_user_info(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    user = UserService(session)
    return await user.get_user_info(telegram_id)


@router.patch("/change-user-language")
async def change_user_language(user_data: UserUpdate, session: AsyncSession = Depends(get_async_session)):
    user = UserService(session)
    return await user.change_user_language(user_data)
