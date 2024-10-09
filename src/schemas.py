from pydantic import BaseModel, UUID4, ConfigDict


class WordInfo(BaseModel):
    id: UUID4
    name: str
    model_config = ConfigDict(from_attributes=True)


class SentenceInfo(BaseModel):
    id: UUID4
    name: str
