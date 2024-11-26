from enum import Enum


class AvailableLanguages(Enum):
    russian = 1
    english = 2
    french = 3

    @classmethod
    def __contains__(cls, item):
        return item in (lang.name for lang in cls)
