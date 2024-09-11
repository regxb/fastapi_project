from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func, DateTime
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int]
    rating: Mapped[str] = mapped_column(default="A1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class Exam(Base):
    __tablename__ = "exam"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(default="going")
    created_at: Mapped[datetime] = mapped_column(default=func.now)
    word: Mapped[str] = mapped_column(ForeignKey('words.id'))
    answer_status: Mapped[str]


class Word(Base):
    __tablename__ = 'words'

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str]
    part_of_speech: Mapped[str]
    rating: Mapped[str]
    translation_id: Mapped[int] = mapped_column(ForeignKey('translation_words.id'))

    translation: Mapped["TranslationWord"] = relationship(back_populates="words")


class TranslationWord(Base):
    __tablename__ = 'translation_words'

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str]

    words: Mapped["Word"] = relationship(back_populates="translation")
