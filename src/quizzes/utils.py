import random
import string

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User, Word, TranslationWord
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
