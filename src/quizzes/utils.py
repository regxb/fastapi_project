import random
import string

from src.models import User, Word


def add_word_for_translate_to_other_words(other_words: list, word_for_translate: Word) -> list:
    other_words.append(word_for_translate.translation)
    return other_words


def shuffle_random_words(other_words: list) -> list:
    random.shuffle(other_words)
    return other_words


def delete_punctuation(text: str) -> str:
    new_text = text.translate(str.maketrans('', '', string.punctuation))
    return new_text
