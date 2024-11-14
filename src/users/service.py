from fastapi import HTTPException

from src.database import async_session_maker
from src.models import User
from src.users.query import get_user, get_all_users, get_user_data
from src.users.schemas import UserCreate, UserUpdate


class UserService:
    def __init__(self):
        self.session = async_session_maker()

    async def create_user(self, user_data: UserCreate):
        async with self.session as session:
            user = await get_user(session, user_data.telegram_id)
            if user:
                raise HTTPException(status_code=203, detail="Пользователь уже зарегистрирован")
            new_user = User(
                telegram_id=user_data.telegram_id,
                learning_language_from_id=user_data.learning_language_from_id,
                learning_language_to_id=user_data.learning_language_to_id
            )
            session.add(new_user)
            try:
                await session.commit()
                await session.refresh(new_user)
            except Exception:
                await session.rollback()
                raise HTTPException(status_code=500, detail="Ошибка при сохранении пользователя")

            return {"response": f"Пользователь с id {new_user.id} успешно создан"}

    async def change_user_language(self, user_data: UserUpdate):
        async with self.session as session:
            user = await get_user(session, user_data.telegram_id)
            user.learning_language_to_id = user_data.learning_language_to_id
            user.learning_language_from_id = user_data.learning_language_from_id
            try:
                await session.commit()
                return {"message": "Данные успешно обновлены"}
            except Exception:
                await session.rollback()
                raise HTTPException(status_code=500, detail="Ошибка при обновлении данных")

    async def get_users_list(self):
        async with self.session as session:
            return await get_all_users(session)

    async def get_user_info(self, telegram_id: int):
        async with self.session as session:
            user_data = await get_user_data(session, telegram_id)
            if user_data is None:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
            return user_data
