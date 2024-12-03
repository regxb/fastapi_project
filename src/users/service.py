from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.query import get_user, get_all_users, get_user_data
from src.users.schemas import UserCreate, UserUpdate, UserInfo
from src.users.utils import create_new_user
from src.utils import commit_changes_or_rollback


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_data: UserCreate):
        async with self.session as session:
            user = await get_user(session, user_data.telegram_id)
            if user:
                raise HTTPException(status_code=203, detail="Пользователь уже зарегистрирован")

            result = await create_new_user(session, user_data)
            return UserInfo(**result)

    async def change_user_language(self, user_data: UserUpdate):
        async with self.session as session:
            user = await get_user(session, user_data.telegram_id)
            user.learning_language_to_id = user_data.learning_language_to_id
            user.learning_language_from_id = user_data.learning_language_from_id
            await commit_changes_or_rollback(session, message="Ошибка при обновлении данных")
            return {"message": "Данные успешно обновлены"}

    async def get_users_list(self):
        async with self.session as session:
            return await get_all_users(session)

    async def get_user_info(self, telegram_id: int) -> UserInfo:
        async with self.session as session:
            user_data = await get_user_data(session, telegram_id)
            if user_data is None:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
            return UserInfo(**user_data.__dict__)
