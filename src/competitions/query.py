from typing import Sequence, List

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .models import CompetitionRoom, CompetitionRoomData


async def get_room_data(room_id: int, session: AsyncSession):
    query = select(CompetitionRoom).where(CompetitionRoom.id == room_id)
    result = await session.scalar(query)
    return result


async def get_user_rooms_data(user_id: int, session: AsyncSession) -> Sequence[CompetitionRoomData]:
    query = (select(CompetitionRoomData)
             .where(and_(CompetitionRoomData.user_status == "online",
                         CompetitionRoomData.user_id == user_id)))
    result = await session.execute(query)
    user_room_data = result.scalars().all()
    return user_room_data


async def get_user_room_data(room_id: int, user_id: int, session: AsyncSession) -> CompetitionRoomData:
    query = (select(CompetitionRoomData)
             .where(and_(CompetitionRoomData.competition_id == room_id,
                         CompetitionRoomData.user_id == user_id)))
    user_room_data = await session.scalar(query)
    return user_room_data


async def get_competition(room_id: int, session: AsyncSession) -> CompetitionRoom:
    query = select(CompetitionRoom).where(CompetitionRoom.id == room_id)
    competition_room = await session.scalar(query)
    return competition_room


async def get_all_users_stats(room_id: int, session: AsyncSession) -> Sequence[CompetitionRoomData]:
    query = (select(CompetitionRoomData)
             .options(joinedload(CompetitionRoomData.user))
             .where(and_(CompetitionRoomData.competition_id == room_id, CompetitionRoomData.user_status == "online"))
             .order_by(desc(CompetitionRoomData.user_points)))
    result = await session.execute(query)
    users_stats = result.scalars().all()
    return users_stats


async def get_rooms(session: AsyncSession):
    query = select(
        CompetitionRoom,
        func.count().filter(
            and_(
                CompetitionRoomData.user_status == "online",
                CompetitionRoomData.competition_id == CompetitionRoom.id
            )
        ).label("online_count")
    ).group_by(CompetitionRoom.id)

    result = await session.execute(query)
    rooms = result.all()
    return rooms


async def get_users_count_in_room(room_id: int, session: AsyncSession) -> int:
    query = (select(func.count())
             .select_from(CompetitionRoomData)
             .where(and_(CompetitionRoomData.competition_id == room_id, CompetitionRoomData.user_status == "online"))
             )
    result = await session.scalar(query)
    return result


async def check_user_in_room(room_id: int, session: AsyncSession):
    query = (select(CompetitionRoomData)
             .join(CompetitionRoom)
             .where(and_(CompetitionRoomData.competition_id == room_id,
                         CompetitionRoom.owner_id == CompetitionRoomData.user_id,
                         CompetitionRoomData.user_status == "online")))
    result = await session.scalar(query)
    return result
