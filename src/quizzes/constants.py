from enum import Enum


class AvailableLanguages(str, Enum):
    en = "en"
    ru = "ru"


class AvailableWordLevel(str, Enum):
    a1 = 'A1'
    a2 = 'A2'
    b1 = 'B1'
    b2 = 'B2'
    c1 = 'C1'
    c2 = 'C2'


class AvailablePartOfSpeech(str, Enum):
    noun = "Существительное"
    pronoun = "Местоимение"
    verb = "Глагол"
    adjective = "Прилагательное"
    adverb = "Наречие"
    preposition = "Предлог"
    determiner = "Определитель"
    numeral = "Числительное"
    conjunction = "Союз"
    other = "Другое"


languages = {"ru": 1, "en": 2}
parts_of_speech = {part.name: part.value for part in AvailablePartOfSpeech}
levels = {level.name: level.value for level in AvailableWordLevel}
