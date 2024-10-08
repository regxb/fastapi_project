from typing import List

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.users.schemas import UserCreate, UserInfo
from src.database import get_async_session

router = APIRouter(
    prefix="/user",
    tags=["user"]
)


@router.post("")
async def create_user(user_data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    existing_user = await session.scalar(select(User).where(User.telegram_id == user_data.telegram_id))
    if existing_user:
        raise HTTPException(status_code=203, detail="Пользователь уже зарегистрирован")
    new_user = User(
        telegram_id=user_data.telegram_id,
        learning_language_from_id=user_data.learning_language_from_id,
        learning_language_to_id=user_data.learning_language_to_id
    )
    session.add(new_user)
    try:
        await session.commit()
        await session.refresh(new_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при сохранении пользователя")

    return {"response": f"Пользователь с id {new_user.id} успешно создан"}


@router.get("", response_model=List[UserInfo])
async def get_users_list(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User))
    users_list = result.scalars().all()
    return users_list


@router.get("/{telegram_id}", response_model=UserInfo)
async def get_user_info(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    user_data = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user_data is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user_data
