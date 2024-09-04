from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

engine = create_async_engine('postgresql+asyncpg://qwe:qwe@127.0.0.1:5432/fastapi', echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Word(Base):
    __tablename__ = 'words'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    translation_id: Mapped[int] = mapped_column(ForeignKey('translation_words.id'))

    translation: Mapped["TranslationWord"] = relationship(back_populates="words")


class TranslationWord(Base):
    __tablename__ = 'translation_words'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    words: Mapped["Word"] = relationship(back_populates="translation")
