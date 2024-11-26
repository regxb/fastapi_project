import uuid

from fastapi import HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import AvailableLanguages
from src.models import Word, FavoriteWord, TranslationWord, Sentence, TranslationSentence
from src.quizzes.constants import AvailablePartOfSpeech, AvailableWordLevel
from src.quizzes.query import get_random_word_for_translate, get_random_words, get_user_favorite_words, \
    get_user_favorite_word, get_random_user_favorite_word, get_random_sentence_for_translate, \
    get_random_words_for_sentence, get_sentence, get_random_words_for_match, get_translation_words, get_language_to, \
    get_language_from
from src.quizzes.schemas import RandomWordResponse, UserFavoriteWord, RandomSentenceResponse
from src.quizzes.utils import add_word_for_translate_to_other_words, shuffle_random_words, delete_punctuation, \
    create_word_with_translation
from src.schemas import WordInfo, SentenceInfo
from src.users.query import get_user


class WordService:
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

            result = await create_word_with_translation(self.session, language_from.id, word_to_translate,
                                                        language_to.id, translation_word, part_of_speech.name,
                                                        level.name)

            return result

    async def get_random_word(
            self,
            telegram_id: int) -> RandomWordResponse:
        async with self.session as session:
            user = await get_user(session, telegram_id)
            word_for_translate = await get_random_word_for_translate(session, user.learning_language_from_id)
            other_words = await get_random_words(session, user.learning_language_to_id, word_for_translate.id)

            add_word_for_translate_to_other_words(other_words, word_for_translate)
            shuffle_random_words(other_words)

            in_favorite = await get_user_favorite_words(session, word_for_translate.id, user.id)

            response = RandomWordResponse(
                word_for_translate=WordInfo(name=word_for_translate.name, id=word_for_translate.id),
                other_words=[WordInfo(name=w.name, id=w.id) for w in other_words],
                in_favorite=False if in_favorite is None else True
            )
            return response

    async def get_match_words(self, telegram_id: int):
        async with self.session as session:
            user = await get_user(session, telegram_id)
            words = await get_random_words_for_match(session, user.learning_language_from_id)
            words_list = [{"id": w.id, "name": w.name} for w in words]
            translation_words_list = [{"id": w.translation.id, "name": w.translation.name} for w in words]
            shuffle_random_words(words_list)
            shuffle_random_words(translation_words_list)
            response = {"words": words_list, "translation_words": translation_words_list}
            return response


class FavoriteWordService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_favorite_word(self, data: UserFavoriteWord):
        async with self.session as session:
            user = await get_user(session, data.telegram_id)
            word = await session.get(Word, data.word_id)
            new_favorite_word_is_exists = await get_user_favorite_words(session, word.id, user.id)

            if user is None:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
            if word is None:
                raise HTTPException(status_code=404, detail="Слово не найдено")
            if new_favorite_word_is_exists:
                raise HTTPException(status_code=201, detail="Данное слово уже добавлено пользователем")

            new_favorite_word = FavoriteWord(
                user_id=user.id,
                word_id=word.id
            )
            session.add(new_favorite_word)

            try:
                await session.commit()
                return {"message": "Слово успешно добавлено"}
            except Exception:
                await session.rollback()
                raise HTTPException(status_code=500, detail="Ошибка при добавлении слова в избранное")

    async def delete_favorite_word(self, data: UserFavoriteWord):
        async with self.session as session:

            user_favorite_word = await get_user_favorite_word(session, data.telegram_id, data.word_id)

            if user_favorite_word is None:
                raise HTTPException(status_code=404, detail="У пользователя нет такого слова в избранном")

            try:
                await session.delete(user_favorite_word)
                await session.commit()
                return {"message": "Слово было удалено"}
            except Exception:
                await session.rollback()
                raise HTTPException(status_code=500, detail="Ошибка при удалении слова из избранного")

    async def get_random_favorite_word(self, telegram_id: int):
        async with self.session as session:
            user = await get_user(session, telegram_id)
            random_user_favorite_word = await get_random_user_favorite_word(session, user.id)
            other_words = await get_random_words(session, user.learning_language_to_id,
                                                 random_user_favorite_word.word.id)

            add_word_for_translate_to_other_words(other_words, random_user_favorite_word.word)
            shuffle_random_words(other_words)

            response = RandomWordResponse(
                word_for_translate=WordInfo(name=random_user_favorite_word.word.name,
                                            id=random_user_favorite_word.word_id),
                other_words=[WordInfo(name=w.name, id=w.id) for w in other_words],
                in_favorite=True
            )
            return response


class SentenceService:
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
            new_sentence = Sentence(
                name=sentence_to_translate,
                language_id=translation_from_language.name,
                level=level.name
            )
            session.add(new_sentence)
            await session.flush()

            new_translation_sentence = TranslationSentence(
                name=translation_sentence,
                sentence_id=new_sentence.id,
                from_language_id=translation_from_language.name,
                to_language_id=translation_to_language.name,
            )
            session.add(new_translation_sentence)
            try:
                await session.commit()
                return {"message": "Предложение успешно добавлено"}
            except Exception:
                await session.rollback()
                raise HTTPException(status_code=500, detail="Ошибка при добавлении предложения")

    async def get_random_sentence(self, telegram_id: int):
        async with self.session as session:
            user = await get_user(session, telegram_id)
            language_to_id = user.learning_language_to_id
            random_sentence_for_translate = await get_random_sentence_for_translate(session, language_to_id,
                                                                                    user.learning_language_from_id)

            words_for_sentence = delete_punctuation(random_sentence_for_translate.name).split()
            random_words_for_sentence = await get_random_words_for_sentence(session, language_to_id, words_for_sentence)

            words_for_sentence.extend(random_words_for_sentence)
            shuffle_random_words(words_for_sentence)

            response = RandomSentenceResponse(
                sentence_for_translate=SentenceInfo(
                    id=random_sentence_for_translate.id,
                    name=random_sentence_for_translate.translation.name
                ),
                words_for_sentence=words_for_sentence
            )
            return response


class AnswerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_answer(self, word_for_translate_id: uuid.UUID, user_word_id: uuid.UUID):
        async with self.session as session:
            word = await get_translation_words(session, user_word_id)
            return word_for_translate_id == word.word_id

    async def check_sentence_answer(self, sentence_id: uuid.UUID, user_words: list[str] = Query(...), ):
        async with self.session as session:
            sentence = await get_sentence(session, sentence_id)
            return delete_punctuation(sentence.name).lower() == " ".join(user_words).lower()
