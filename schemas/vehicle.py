from pydantic import BaseModel, Field

from models.enums import VehicleStatus, VehicleType
from schemas.base import AppBaseModel

_PLATE_PATTERN = r"^[A-Z0-9\-]+$"


class VehicleCreate(BaseModel):
    plate_number: str = Field(
        min_length=2,
        max_length=20,
        pattern=_PLATE_PATTERN,
        description="Uppercase letters, digits, and hyphens only",
    )
    vehicle_type: VehicleType
    capacity: int = Field(gt=0, le=100)
    office_id: int = Field(gt=0)


class VehicleUpdate(BaseModel):
    plate_number: str | None = Field(
        default=None, min_length=2, max_length=20, pattern=_PLATE_PATTERN
    )
    vehicle_type: VehicleType | None = None
    capacity: int | None = Field(default=None, gt=0, le=100)
    status: VehicleStatus | None = None
    office_id: int | None = Field(default=None, gt=0)


class VehicleResponse(AppBaseModel):
    id: int
    plate_number: str
    vehicle_type: VehicleType
    capacity: int
    status: VehicleStatus
    office_id: int
