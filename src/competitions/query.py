from typing import Sequence

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .models import Competitions, CompetitionRoomData


async def get_user_room_data(room_id: int, user_id: int, session: AsyncSession) -> CompetitionRoomData:
    query = (select(CompetitionRoomData)
             .where(and_(CompetitionRoomData.competition_id == room_id,
                         CompetitionRoomData.user_id == user_id)))
    user_room_data = await session.scalar(query)
    return user_room_data


async def get_competition(room_id: int, session: AsyncSession) -> Competitions:
    query = select(Competitions).where(Competitions.id == room_id)
    competition_room = await session.scalar(query)
    return competition_room


async def get_users_stats(room_id: int, session: AsyncSession) -> Sequence[CompetitionRoomData]:
    query = (select(CompetitionRoomData)
             .options(joinedload(CompetitionRoomData.user))
             .where(CompetitionRoomData.competition_id == room_id)
             .order_by(desc(CompetitionRoomData.user_points)))
    result = await session.execute(query)
    users_stats = result.scalars().all()
    return users_stats


async def get_rooms(session: AsyncSession):
    rooms = await session.execute(select(Competitions))
    return rooms