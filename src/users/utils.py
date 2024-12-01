from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.utils import commit_changes_or_rollback


async def create_new_user(session: AsyncSession, telegram_id: int, learning_language_from_id: int,
                          learning_language_to_id: int):
    new_user = User(
        telegram_id=telegram_id,
        learning_language_from_id=learning_language_from_id,
        learning_language_to_id=learning_language_to_id
    )
    session.add(new_user)
    await commit_changes_or_rollback(session, message="Ошибка при сохранении пользователя")

    return {"response": f"Пользователь успешно создан"}
