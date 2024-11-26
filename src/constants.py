from enum import Enum


class AvailableLanguages(Enum):
    russian = "russian"
    english = "english"
    french = "french"

    @classmethod
    def __contains__(cls, item):
        return item in [idx + 1 for idx, _ in enumerate(cls)]
