from typing import Sequence

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User:
    query = select(User).where(User.telegram_id == telegram_id)
    user = await session.scalar(query)
    return user


async def get_user_by_username(username: str, session: AsyncSession) -> Sequence[User]:
    query = select(User).where(User.username.like(f"%{username}%"))
    result = await session.execute(query)
    users = result.scalars().all()
    return users


async def get_online_users(page: int, size: int, session: AsyncSession, telegram_ids: Sequence[int]):
    query = (select(User)
             .where(User.telegram_id.in_(telegram_ids))
             .limit(size)
             .offset((page - 1) * size)
             .order_by(User.id))
    result = await session.execute(query)
    users = result.scalars().all()
    return users


async def get_users_list(page: int, size: int, session: AsyncSession) -> Sequence[User]:
    query = select(User).limit(size).offset((page - 1) * size).order_by(User.id)
    result = await session.execute(query)
    users = result.scalars().all()
    return users


async def get_users_count(session: AsyncSession) -> int:
    query = select(func.count(User.id))
    users_count = await session.scalar(query)
    return users_count


async def get_online_users_count(telegram_ids: Sequence[int], session: AsyncSession) -> int:
    query = select(func.count(User.telegram_id)).where(User.telegram_id.in_(telegram_ids))
    users_count = await session.scalar(query)
    return users_count


async def get_user_data(session: AsyncSession, telegram_id: int) -> User:
    user_data = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    return user_data
