from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.quizzes.query import get_random_word_for_translate, get_random_words, check_word_in_favorite
from src.quizzes.schemas import RandomWordResponse
from src.quizzes.utils import get_language_from_id, get_language_to_id, add_word_for_translate_to_other_words, \
    shuffle_random_words
from src.schemas import WordInfo
from src.users.query import get_user


class QuizService:
    def __init__(self):
        self.session = get_async_session()

    async def get_random_word(
            self,
            telegram_id: int) -> RandomWordResponse:
        user = await get_user(self.session, telegram_id)
        language_from_id = get_language_from_id(user)
        language_to_id = get_language_to_id(user)

        word_for_translate = await get_random_word_for_translate(self.session, language_from_id)
        other_words = await get_random_words(self.session, language_to_id, word_for_translate.id)

        add_word_for_translate_to_other_words(other_words, word_for_translate)
        shuffle_random_words(other_words)

        in_favorite = await check_word_in_favorite(self.session, word_for_translate.id, user.id)

        response = RandomWordResponse(
            word_for_translate=WordInfo(name=word_for_translate.name, id=word_for_translate.id),
            other_words=[WordInfo(name=w.name, id=w.id) for w in other_words],
            in_favorite=in_favorite
        )
        return response
