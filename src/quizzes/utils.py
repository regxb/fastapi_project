import random
import string
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Word, TranslationWord, Sentence, TranslationSentence, FavoriteWord
from src.utils import commit_changes


def add_word_for_translate_to_other_words(other_words: list, word_for_translate: Word) -> list:
    other_words.append(word_for_translate.translation)
    return other_words


def shuffle_random_words(other_words: list) -> list:
    random.shuffle(other_words)
    return other_words


def delete_punctuation(text: str) -> str:
    new_text = text.translate(str.maketrans('', '', string.punctuation))
    return new_text


async def create_word_with_translation(
        session: AsyncSession,
        language_from: int,
        word_to_translate: str,
        language_to: int,
        translation_word: str,
        part_of_speech: str,
        level: str
):
    new_word = Word(
        name=word_to_translate,
        language_id=language_from,
        part_of_speech=part_of_speech,
        level=level.upper()
    )

    session.add(new_word)
    await session.flush()

    new_translation_word = TranslationWord(
        name=translation_word,
        to_language_id=language_to,
        from_language_id=language_from,
        word_id=new_word.id
    )
    session.add(new_translation_word)
    await commit_changes(session, "Ошибка при добавлении слова")
    return {"message": "Слово успешно добавлено"}


async def create_new_sentence_with_translation(
        session: AsyncSession,
        translation_from_language: int,
        sentence_to_translate: str,
        translation_to_language: int,
        translation_sentence: str,
        level: str
):
    new_sentence = Sentence(
        name=sentence_to_translate,
        language_id=translation_from_language,
        level=level
    )

    session.add(new_sentence)
    await session.flush()

    new_translation_sentence = TranslationSentence(
        name=translation_sentence,
        sentence_id=new_sentence.id,
        from_language_id=translation_from_language,
        to_language_id=translation_to_language,
    )
    session.add(new_translation_sentence)
    await commit_changes(session, "Ошибка при добавлении предложения")
    return {"message": "Предложение успешно добавлено"}


async def add_word_to_favorite(session: AsyncSession, user_id: int, word_id: uuid.UUID):
    new_favorite_word = FavoriteWord(
        user_id=user_id,
        word_id=word_id
    )
    session.add(new_favorite_word)
    await commit_changes(session, "Ошибка при добавлении слова в избранное")
    return {"message": "Слово успешно добавлено в избранное"}


async def delete_word_from_favorite(session: AsyncSession, user_favorite_word: uuid.UUID):
    await session.delete(user_favorite_word)
    await commit_changes(session, "Ошибка при удалении слова из избранного")
    return {"message": "Слово было удалено"}
