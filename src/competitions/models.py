from datetime import datetime

from sqlalchemy import DateTime, func, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.models import Base


class Competitions(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(default="awaiting")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    competition_room_data: Mapped["CompetitionRoomData"] = relationship(back_populates="competition")


class CompetitionRoomData(Base):
    __tablename__ = "competition_room_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_points: Mapped[int] = mapped_column(default=0)
    user_status: Mapped[str] = mapped_column(default="offline")

    competition: Mapped["Competitions"] = relationship(back_populates="competition_room_data")
    user: Mapped["User"] = relationship(back_populates="competition_room_data")
