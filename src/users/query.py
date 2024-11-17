import json
from typing import List, Sequence
import redis.asyncio as redis
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User


async def get_user(session: AsyncSession, telegram_id: int) -> User:
    redis_conn = await redis.from_url("redis://redis:6379")

    value = await redis_conn.get(telegram_id)
    if value:
        value = json.loads(value.decode("utf-8"))
        user = User.from_dict(value)
        return user
    query = select(User).where(User.telegram_id == telegram_id)
    user = await session.scalar(query)
    await redis_conn.set(telegram_id, json.dumps(user.to_dict()))
    return user


async def get_all_users(session: AsyncSession) -> Sequence[User]:
    result = await session.execute(select(User))
    users_list = result.scalars().all()
    return users_list


async def get_user_data(session: AsyncSession, telegram_id: int) -> User:
    user_data = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    return user_data
