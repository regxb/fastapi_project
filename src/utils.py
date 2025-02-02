from typing import Dict, List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


async def commit_changes_or_rollback(session: AsyncSession, message: str):
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"{message}")


def uuid_to_str(uuid: Dict) -> List[str]:
    return [str(value) for value in uuid.values()]
