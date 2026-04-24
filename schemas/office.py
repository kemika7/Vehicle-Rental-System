from pydantic import BaseModel, Field

from schemas.base import AppBaseModel


class OfficeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=255)


class OfficeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    location: str | None = Field(default=None, min_length=1, max_length=255)


class OfficeResponse(AppBaseModel):
    id: int
    name: str
    location: str
