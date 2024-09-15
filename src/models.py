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

    exam: Mapped["Exam"] = relationship(back_populates="user")
    favorite_words: Mapped["FavoriteWord"] = relationship(back_populates="user")


class Exam(Base):
    __tablename__ = "exam"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    status: Mapped[str] = mapped_column(default="going")

    user: Mapped["User"] = relationship(back_populates="exam")
    exam_question: Mapped["ExamQuestion"] = relationship(back_populates="exam")


class ExamQuestion(Base):
    __tablename__ = "exam_question"

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exam.id'))
    word_id: Mapped[str] = mapped_column(ForeignKey('words.id'))
    status: Mapped[str] = mapped_column(default="awaiting response")

    exam: Mapped["Exam"] = relationship(back_populates="exam_question")
    word: Mapped["Word"] = relationship(back_populates="exam_question")


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
    exam_question: Mapped["ExamQuestion"] = relationship(back_populates="word")


class TranslationWord(Base):
    __tablename__ = 'translation_words'

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str]

    words: Mapped["Word"] = relationship(back_populates="translation")


class FavoriteWord(Base):
    __tablename__ = 'favorite_words'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    word_id: Mapped[UUID] = mapped_column(ForeignKey("words.id"))

    user: Mapped["User"] = relationship(back_populates="favorite_words")
