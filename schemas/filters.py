from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from models.enums import RentalStatus, VehicleStatus, VehicleType


class VehicleFilters(BaseModel):
    """Query parameters for GET /vehicles.

    All fields are optional and stack as AND conditions.
    Availability filtering uses a NOT EXISTS subquery — it is independent
    of the `status` column filter so both can be combined freely.
    """

    office_id: int | None = Field(default=None, gt=0)
    vehicle_type: VehicleType | None = None
    min_capacity: int | None = Field(default=None, gt=0)
    max_capacity: int | None = Field(default=None, gt=0)
    available_from: datetime | None = None
    available_until: datetime | None = None
    status: VehicleStatus | None = None

    @model_validator(mode="after")
    def validate_ranges(self) -> "VehicleFilters":
        if (
            self.min_capacity is not None
            and self.max_capacity is not None
            and self.min_capacity > self.max_capacity
        ):
            raise ValueError("min_capacity cannot be greater than max_capacity")
        if (
            self.available_from is not None
            and self.available_until is not None
            and self.available_from >= self.available_until
        ):
            raise ValueError("available_from must be before available_until")
        return self


class RentalFilters(BaseModel):
    """Query parameters for GET /rentals.

    `active_from` / `active_until` match rentals whose window overlaps
    with the requested period, not just rentals that start within it.
    `office_id` filters by the office of the rented vehicle (requires a JOIN).
    """

    vehicle_id: int | None = Field(default=None, gt=0)
    employee_id: int | None = Field(default=None, gt=0)
    office_id: int | None = Field(default=None, gt=0)
    status: RentalStatus | None = None
    active_from: datetime | None = None
    active_until: datetime | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "RentalFilters":
        if (
            self.active_from is not None
            and self.active_until is not None
            and self.active_from >= self.active_until
        ):
            raise ValueError("active_from must be before active_until")
        return self
