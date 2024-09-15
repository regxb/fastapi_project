from pydantic import BaseModel, UUID4


class WordInfo(BaseModel):
    id: UUID4
    name: str
