from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator

from models.enums import RentalStatus
from schemas.base import AppBaseModel
from schemas.employee import EmployeeResponse
from schemas.vehicle import VehicleResponse


class RentalCreate(BaseModel):
    vehicle_id: int = Field(gt=0)
    employee_id: int = Field(gt=0)
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    end_time: datetime | None = None

    @model_validator(mode="after")
    def end_must_follow_start(self) -> "RentalCreate":
        if self.end_time is not None and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class RentalUpdate(BaseModel):
    end_time: datetime | None = None
    status: RentalStatus | None = None

    @model_validator(mode="after")
    def completed_requires_end_time(self) -> "RentalUpdate":
        if self.status == RentalStatus.completed and self.end_time is None:
            raise ValueError("end_time is required when status is 'completed'")
        return self


class RentalResponse(AppBaseModel):
    id: int
    vehicle_id: int
    employee_id: int
    start_time: datetime
    end_time: datetime | None
    status: RentalStatus


class RentalDetailResponse(AppBaseModel):
    """Extended response with nested vehicle and employee data."""
    id: int
    start_time: datetime
    end_time: datetime | None
    status: RentalStatus
    vehicle: VehicleResponse
    employee: EmployeeResponse
