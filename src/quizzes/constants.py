from enum import Enum


class AvailableWordLevel(str, Enum):
    a1 = 'A1'
    a2 = 'A2'
    b1 = 'B1'
    b2 = 'B2'
    c1 = 'C1'
    c2 = 'C2'


class AvailablePartOfSpeech(str, Enum):
    noun = "noun"
    pronoun = "pronoun"
    verb = "verb"
    adjective = "adjective"
    adverb = "adverb"
    preposition = "preposition"
    determiner = "determiner"
    numeral = "numeral"
    conjunction = "conjunction"
    other = "other"
