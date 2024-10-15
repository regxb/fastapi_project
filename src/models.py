from datetime import datetime
from enum import Enum

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func, DateTime, text, String
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int]
    learning_language_from_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    learning_language_to_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    rating: Mapped[str] = mapped_column(default="A1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # exam: Mapped["Exam"] = relationship(back_populates="user")
    favorite_word: Mapped["FavoriteWord"] = relationship(back_populates="user")


# class Exam(Base):
#     __tablename__ = "exam"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
#     status: Mapped[str] = mapped_column(default="going")
#
#     user: Mapped["User"] = relationship(back_populates="exam")
#     exam_question: Mapped["ExamQuestion"] = relationship(back_populates="exam")
#
#
# class ExamQuestion(Base):
#     __tablename__ = "exam_question"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     exam_id: Mapped[int] = mapped_column(ForeignKey('exam.id'))
#     word_id: Mapped[str] = mapped_column(ForeignKey('words.id'))
#     status: Mapped[str] = mapped_column(default="awaiting response")
#
#     exam: Mapped["Exam"] = relationship(back_populates="exam_question")
#     word: Mapped["Word"] = relationship(back_populates="exam_question")


class Sentence(Base):
    __tablename__ = 'sentences'

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str]
    level: Mapped[str] = mapped_column(nullable=True)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))

    translation: Mapped["TranslationSentence"] = relationship(back_populates="sentence")


class TranslationSentence(Base):
    __tablename__ = 'translation_sentences'

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str]
    sentence_id: Mapped[UUID] = mapped_column(ForeignKey("sentences.id"))
    from_language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    to_language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))

    sentence: Mapped["Sentence"] = relationship(back_populates="translation")


class Word(Base):
    __tablename__ = 'words'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    name: Mapped[str]
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    part_of_speech: Mapped[str]
    level: Mapped[str]

    translation: Mapped["TranslationWord"] = relationship(back_populates="word")
    favorite_word: Mapped["FavoriteWord"] = relationship(back_populates="word")
    # exam_question: Mapped["ExamQuestion"] = relationship(back_populates="word")


class TranslationWord(Base):
    __tablename__ = 'translation_words'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    word_id: Mapped[UUID] = mapped_column(ForeignKey("words.id"))
    from_language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    to_language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str]

    word: Mapped["Word"] = relationship(back_populates="translation")


class Language(Base):
    __tablename__ = 'languages'

    id: Mapped[int] = mapped_column(primary_key=True)
    language: Mapped[str]


class FavoriteWord(Base):
    __tablename__ = 'favorite_words'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    word_id: Mapped[UUID] = mapped_column(ForeignKey("words.id"))

    user: Mapped["User"] = relationship(back_populates="favorite_word")
    word: Mapped["Word"] = relationship(back_populates="favorite_word")


class Exam(Base):
    __tablename__ = 'exams'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    attempts: Mapped[int] = mapped_column(default=3)
    total_exercises: Mapped[int] = mapped_column(default=50)
    progress: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="started")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

