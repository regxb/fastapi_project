from pydantic import BaseModel


class CompetitionStatisticsSchema(BaseModel):
    telegram_id: int
    room_id: int
