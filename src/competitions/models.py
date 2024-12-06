from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base


class CompetitionRoom(Base):
    __tablename__ = "competitions_rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    language_from_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    language_to_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))

    competition_room_data: Mapped["CompetitionRoomData"] = relationship(back_populates="competition")


class CompetitionRoomData(Base):
    __tablename__ = "competition_room_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions_rooms.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_points: Mapped[int] = mapped_column(default=0)
    user_status: Mapped[str] = mapped_column(default="offline")

    competition: Mapped["CompetitionRoom"] = relationship(back_populates="competition_room_data")
    user: Mapped["User"] = relationship(back_populates="competition_room_data")
