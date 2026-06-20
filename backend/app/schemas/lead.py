import uuid

from pydantic import BaseModel, EmailStr


class LeadCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    source: str | None = None
    score: int | None = None


class LeadOut(BaseModel):
    id: uuid.UUID
    status: str
    score: int | None
    source: str | None

    model_config = {"from_attributes": True}
