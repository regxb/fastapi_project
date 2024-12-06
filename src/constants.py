from enum import Enum


class AvailableLanguages(Enum):
    russian = "russian"
    english = "english"
    french = "french"

    @classmethod
    def __contains__(cls, item):
        return item in [idx + 1 for idx, _ in enumerate(cls)]


levels = {
    "A1": "A2",
    "A2": "B1",
    "B1": "B2",
    "B2": "C1",
    "C1": "C2",
    "C2": "C2",
}
