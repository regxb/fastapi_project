from enum import Enum


class AvailableLanguages(Enum):
    russian = 1
    english = 2
    french = 3


levels = {
    "A1": "A2",
    "A2": "B1",
    "B1": "B2",
    "B2": "C1",
    "C1": "C2",
    "C2": "C2",
}
