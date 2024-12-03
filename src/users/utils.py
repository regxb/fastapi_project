from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.users.schemas import UserCreate
from src.utils import commit_changes_or_rollback


async def create_new_user(session: AsyncSession, user_data: UserCreate):
    new_user = User(**user_data.__dict__)
    session.add(new_user)
    await commit_changes_or_rollback(session, message="Ошибка при сохранении пользователя")
    return new_user.__dict__

