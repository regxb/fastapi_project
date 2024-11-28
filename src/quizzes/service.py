import uuid

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.quizzes.query import (get_random_word_for_translate, get_random_words, get_user_favorite_words,
                               get_random_user_favorite_word, get_random_sentence_for_translate,
                               get_random_words_for_sentence, get_sentence, get_random_words_for_match,
                               get_translation_words)
from src.quizzes.schemas import RandomWordResponse, RandomSentenceResponse
from src.quizzes.utils import add_word_for_translate_to_other_words, shuffle_random_words, delete_punctuation
from src.schemas import WordInfo, SentenceInfo
from src.users.query import get_user


class WordService:
    def __init__(self, session: AsyncSession):
        self.session = session

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
                type="random_word",
                word_for_translate=WordInfo(**word_for_translate.__dict__),
                other_words=[WordInfo(**word.__dict__) for word in other_words],
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

    async def get_random_favorite_word(self, telegram_id: int):
        async with self.session as session:
            user = await get_user(session, telegram_id)
            random_user_favorite_word = await get_random_user_favorite_word(session, user.id)
            other_words = await get_random_words(session, user.learning_language_to_id,
                                                 random_user_favorite_word.id)

            add_word_for_translate_to_other_words(other_words, random_user_favorite_word)
            shuffle_random_words(other_words)

            response = RandomWordResponse(
                type="random_word",
                word_for_translate=WordInfo(**random_user_favorite_word.__dict__),
                other_words=[WordInfo(**word.__dict__) for word in other_words],
                in_favorite=True
            )
            return response


class SentenceService:
    def __init__(self, session: AsyncSession):
        self.session = session

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
                type="random_sentence",
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
