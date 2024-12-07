from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import levels
from src.models import User
from src.users.query import get_all_users, get_user, get_user_data
from src.users.schemas import UserCreate, UserInfo, UserUpdate
from src.utils import commit_changes_or_rollback


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_data: UserCreate):
        async with self.session as session:
            user = await get_user(session, user_data.telegram_id)
            if user:
                raise HTTPException(status_code=203, detail="Пользователь уже зарегистрирован")
            new_user_data = self.prepare_data_for_create_user(user_data)
            new_user = User(**new_user_data)
            session.add(new_user)
            await commit_changes_or_rollback(session, "Ошибка при сохранении пользователя")
            return UserInfo(**new_user.__dict__)

    def prepare_data_for_create_user(self, user_data: UserCreate):
        user_data = user_data.dict()
        user_data["learning_language_from_id"] = user_data["learning_language_from_id"].value
        user_data["learning_language_to_id"] = user_data["learning_language_to_id"].value
        return user_data

    async def change_user_language(self, user_data: UserUpdate):
        async with self.session as session:
            user = await get_user(session, user_data.telegram_id)
            user.learning_language_to_id = user_data.learning_language_to_id.value
            user.learning_language_from_id = user_data.learning_language_from_id.value
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

    @staticmethod
    async def update_user_rating(user_rating: str) -> str:
        return levels[user_rating]
