from datetime import datetime, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload

from exceptions import BusinessRuleError, NotFoundError
from models.employee import Employee
from models.enums import RentalStatus, VehicleStatus
from models.rental import Rental
from models.vehicle import Vehicle
from schemas.filters import RentalFilters
from schemas.rental import RentalCreate, RentalUpdate

_TERMINAL_STATUSES = {RentalStatus.completed, RentalStatus.cancelled}


def _to_naive_utc(dt: datetime) -> datetime:
    """Convert to UTC and strip tzinfo — SQLite stores datetimes without timezone."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


# ---------------------------------------------------------------------------
# Internal guards — pure, no DB writes; called before any state mutation.
# ---------------------------------------------------------------------------

def _guard_not_under_maintenance(vehicle: Vehicle) -> None:
    if vehicle.status == VehicleStatus.maintenance:
        raise BusinessRuleError(
            f"Vehicle {vehicle.id} is under maintenance and cannot be rented."
        )


def _guard_same_office(vehicle: Vehicle, employee: Employee) -> None:
    if vehicle.office_id != employee.office_id:
        raise BusinessRuleError(
            f"Vehicle belongs to office {vehicle.office_id} but employee belongs to "
            f"office {employee.office_id}. Cross-office rentals are not permitted."
        )


def _guard_no_time_overlap(
    db: Session,
    vehicle_id: int,
    start_time: datetime,
    end_time: datetime | None,
    *,
    exclude_rental_id: int | None = None,
) -> None:
    """
    Two intervals [A_start, A_end) and [B_start, B_end) overlap when:
        A_start < B_end  AND  B_start < A_end
    NULL end_time means open-ended (treated as +infinity).

    Only non-cancelled rentals block a slot.
    """
    # Normalize to naive UTC so SQLite string comparison works correctly.
    start_time = _to_naive_utc(start_time)
    end_time = _to_naive_utc(end_time) if end_time is not None else None

    ex_ends_after_new_start = or_(
        Rental.end_time.is_(None),
        Rental.end_time > start_time,
    )

    if end_time is None:
        time_overlap = ex_ends_after_new_start
    else:
        time_overlap = and_(ex_ends_after_new_start, Rental.start_time < end_time)

    stmt = select(Rental.id).where(
        Rental.vehicle_id == vehicle_id,
        Rental.status != RentalStatus.cancelled,
        time_overlap,
    )
    if exclude_rental_id is not None:
        stmt = stmt.where(Rental.id != exclude_rental_id)

    conflicting_id = db.execute(stmt).scalar_one_or_none()
    if conflicting_id is not None:
        raise BusinessRuleError(
            f"Vehicle {vehicle_id} is already booked during the requested time window "
            f"(conflicts with rental #{conflicting_id})."
        )


def _guard_end_after_start(end_time: datetime, rental_start: datetime) -> None:
    if _to_naive_utc(end_time) <= _to_naive_utc(rental_start):
        raise BusinessRuleError(
            f"end_time must be after the rental's start_time "
            f"({rental_start.isoformat()})."
        )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def list_rentals(db: Session, filters: RentalFilters) -> list[Rental]:
    stmt = select(Rental)

    # --- JOIN required only when filtering by office ---
    if filters.office_id is not None:
        stmt = stmt.join(Vehicle, Rental.vehicle_id == Vehicle.id).where(
            Vehicle.office_id == filters.office_id
        )

    # --- scalar filters ---
    if filters.vehicle_id is not None:
        stmt = stmt.where(Rental.vehicle_id == filters.vehicle_id)

    if filters.employee_id is not None:
        stmt = stmt.where(Rental.employee_id == filters.employee_id)

    if filters.status is not None:
        stmt = stmt.where(Rental.status == filters.status)

    # --- date-range overlap filters ---
    # Returns rentals whose window overlaps [active_from, active_until].
    # Overlap: rental.start < window.end  AND  rental.end > window.start
    # NULL rental.end_time = open-ended (+infinity).
    if filters.active_from is not None:
        stmt = stmt.where(
            or_(Rental.end_time.is_(None), Rental.end_time > _to_naive_utc(filters.active_from))
        )

    if filters.active_until is not None:
        stmt = stmt.where(Rental.start_time < _to_naive_utc(filters.active_until))

    return list(db.execute(stmt).scalars().all())


def get_rental(db: Session, rental_id: int) -> Rental:
    stmt = (
        select(Rental)
        .options(joinedload(Rental.vehicle), joinedload(Rental.employee))
        .where(Rental.id == rental_id)
    )
    rental = db.execute(stmt).scalar_one_or_none()
    if rental is None:
        raise NotFoundError("Rental", rental_id)
    return rental


def create_rental(db: Session, data: RentalCreate) -> Rental:
    vehicle = db.get(Vehicle, data.vehicle_id)
    if vehicle is None:
        raise NotFoundError("Vehicle", data.vehicle_id)

    employee = db.get(Employee, data.employee_id)
    if employee is None:
        raise NotFoundError("Employee", data.employee_id)

    # All guards before any write.
    _guard_not_under_maintenance(vehicle)
    _guard_same_office(vehicle, employee)
    _guard_no_time_overlap(db, data.vehicle_id, data.start_time, data.end_time)

    rental = Rental(
        vehicle_id=data.vehicle_id,
        employee_id=data.employee_id,
        start_time=data.start_time,
        end_time=data.end_time,
        status=RentalStatus.active,
    )
    vehicle.status = VehicleStatus.rented
    db.add(rental)
    db.commit()
    db.refresh(rental)
    return rental


def update_rental(db: Session, rental_id: int, data: RentalUpdate) -> Rental:
    rental = db.get(Rental, rental_id)
    if rental is None:
        raise NotFoundError("Rental", rental_id)
    if rental.status in _TERMINAL_STATUSES:
        raise BusinessRuleError(
            f"Rental {rental_id} is already {rental.status} and cannot be modified."
        )

    if data.end_time is not None:
        _guard_end_after_start(data.end_time, rental.start_time)
        _guard_no_time_overlap(
            db,
            rental.vehicle_id,
            rental.start_time,
            data.end_time,
            exclude_rental_id=rental_id,
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rental, field, value)

    if data.status in _TERMINAL_STATUSES:
        vehicle = db.get(Vehicle, rental.vehicle_id)
        if vehicle is not None:
            vehicle.status = VehicleStatus.available

    db.commit()
    db.refresh(rental)
    return rental


def delete_rental(db: Session, rental_id: int) -> None:
    rental = db.get(Rental, rental_id)
    if rental is None:
        raise NotFoundError("Rental", rental_id)
    if rental.status == RentalStatus.active:
        raise BusinessRuleError(
            f"Rental {rental_id} is active and cannot be deleted. Cancel it first."
        )
    db.delete(rental)
    db.commit()
