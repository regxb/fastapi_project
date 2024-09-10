from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
import uuid
from sqlalchemy.dialects.postgresql import UUID

engine = create_async_engine("postgresql+asyncpg://qwe:qwe@localhost/fastapi", echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


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
