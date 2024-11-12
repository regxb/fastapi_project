import random

from src.models import User, Word


def get_language_from_id(user: User) -> int:
    learning_language_from_id = user.learning_language_from_id
    return learning_language_from_id


def get_language_to_id(user: User) -> int:
    learning_language_to_id = user.learning_language_to_id
    return learning_language_to_id


def add_word_for_translate_to_other_words(other_words: list, word_for_translate: Word) -> list:
    other_words.append(word_for_translate.translation)
    return other_words


def shuffle_random_words(other_words: list) -> list:
    random.shuffle(other_words)
    return other_words
