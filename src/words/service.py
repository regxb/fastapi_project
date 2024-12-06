from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import AvailableLanguages
from src.models import (FavoriteWord, Sentence, TranslationSentence,
                        TranslationWord, Word)
from src.quizzes.constants import AvailablePartOfSpeech, AvailableWordLevel
from src.quizzes.query import (get_language_from, get_language_to,
                               get_user_favorite_word, get_user_favorite_words)
from src.quizzes.schemas import UserFavoriteWord
from src.users.query import get_user
from src.utils import commit_changes_or_rollback


class WordManagementService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_word(
            self,
            language_from: AvailableLanguages,
            word_to_translate: str,
            language_to: AvailableLanguages,
            translation_word: str,
            part_of_speech: AvailablePartOfSpeech,
            level: AvailableWordLevel
    ):
        async with self.session as session:
            language_to = await get_language_to(session, language_to)
            language_from = await get_language_from(session, language_from)

            new_word = Word(
                name=word_to_translate,
                language_id=language_from.id,
                part_of_speech=part_of_speech.name,
                level=level.name.upper()
            )

            session.add(new_word)
            await session.flush()

            new_translation_word = TranslationWord(
                name=translation_word,
                to_language_id=language_to.id,
                from_language_id=language_from.id,
                word_id=new_word.id
            )
            session.add(new_translation_word)
            await commit_changes_or_rollback(session, "Ошибка при добавлении слова")
            return {"message": "Слово успешно добавлено"}


class FavoriteWordManagementService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_favorite_word(self, data: UserFavoriteWord):
        async with self.session as session:
            user = await get_user(session, data.telegram_id)
            word = await session.get(Word, data.word_id)
            new_favorite_word_is_exists = await get_user_favorite_words(session, word.id, user.id)

            if word is None:
                raise HTTPException(status_code=404, detail="Слово не найдено")
            if new_favorite_word_is_exists:
                raise HTTPException(status_code=201, detail="Данное слово уже добавлено пользователем")

            new_favorite_word = FavoriteWord(
                user_id=user.id,
                word_id=word.id
            )
            session.add(new_favorite_word)
            await commit_changes_or_rollback(session, "Ошибка при добавлении слова в избранное")
            return {"message": "Слово успешно добавлено в избранное"}

    async def delete_favorite_word(self, data: UserFavoriteWord):
        async with self.session as session:
            user_favorite_word = await get_user_favorite_word(session, data.telegram_id, data.word_id)

            if user_favorite_word is None:
                raise HTTPException(status_code=404, detail="Пользователь не добавлял это слово в избранное")

            await session.delete(user_favorite_word)
            await commit_changes_or_rollback(session, "Ошибка при удалении слова из избранного")
            return {"message": "Слово было удалено"}


class SentenceManagementService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_sentence(
            self,
            translation_from_language: AvailableLanguages,
            sentence_to_translate: str,
            translation_to_language: AvailableLanguages,
            translation_sentence: str,
            level: AvailableWordLevel):
        async with self.session as session:
            language_to = await get_language_to(session, translation_to_language)
            language_from = await get_language_from(session, translation_from_language)

            new_sentence = Sentence(
                name=sentence_to_translate,
                language_id=language_from.id,
                level=level.value
            )

            session.add(new_sentence)
            await session.flush()

            new_translation_sentence = TranslationSentence(
                name=translation_sentence,
                sentence_id=new_sentence.id,
                from_language_id=language_from.id,
                to_language_id=language_to.id,
            )
            session.add(new_translation_sentence)
            await commit_changes_or_rollback(session, "Ошибка при добавлении предложения")
            return {"message": "Предложение успешно добавлено"}
