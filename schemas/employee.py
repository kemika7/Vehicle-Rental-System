from pydantic import BaseModel, EmailStr, Field

from models.enums import Role
from schemas.base import AppBaseModel


class EmployeeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # 72-byte bcrypt limit
    office_id: int = Field(gt=0)


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    office_id: int | None = Field(default=None, gt=0)


class EmployeeResponse(AppBaseModel):
    id: int
    name: str
    email: str
    role: Role
    office_id: int
