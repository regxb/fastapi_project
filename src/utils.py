from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


async def commit_changes(session: AsyncSession, message: str):
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"{message}")
