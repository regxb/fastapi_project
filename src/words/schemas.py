import uuid

from pydantic import BaseModel
from src.constants import AvailableLanguages
from src.quizzes.constants import AvailablePartOfSpeech, AvailableWordLevel


class WordSchema(BaseModel):
    translation_from_language: AvailableLanguages
    word_to_translate: str
    translation_to_language: AvailableLanguages
    translation_word: str
    part_of_speech: AvailablePartOfSpeech
    level: AvailableWordLevel


class SentenceSchema(BaseModel):
    translation_from_language: AvailableLanguages
    sentence_to_translate: str
    translation_to_language: AvailableLanguages
    translation_sentence: str
    level: AvailableWordLevel
