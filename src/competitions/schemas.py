from pydantic import BaseModel


class CompetitionRoomSchema(BaseModel):
    telegram_id: int
    room_id: int
