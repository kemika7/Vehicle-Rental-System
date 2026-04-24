from datetime import datetime, timezone

from sqlalchemy import exists, not_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from exceptions import BusinessRuleError, NotFoundError
from models.enums import RentalStatus, VehicleStatus, VehicleType
from models.rental import Rental
from models.vehicle import Vehicle
from schemas.filters import VehicleFilters
from schemas.vehicle import VehicleCreate, VehicleUpdate


def _to_naive_utc(dt: datetime) -> datetime:
    """Convert to UTC and strip tzinfo — SQLite stores datetimes without timezone."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def list_vehicles(db: Session, filters: VehicleFilters) -> list[Vehicle]:
    stmt = select(Vehicle)

    # --- scalar column filters (cheap, no join required) ---
    if filters.office_id is not None:
        stmt = stmt.where(Vehicle.office_id == filters.office_id)

    if filters.vehicle_type is not None:
        stmt = stmt.where(Vehicle.vehicle_type == filters.vehicle_type)

    if filters.status is not None:
        stmt = stmt.where(Vehicle.status == filters.status)

    if filters.min_capacity is not None:
        stmt = stmt.where(Vehicle.capacity >= filters.min_capacity)

    if filters.max_capacity is not None:
        stmt = stmt.where(Vehicle.capacity <= filters.max_capacity)

    # --- availability filter via correlated NOT EXISTS subquery ---
    # A vehicle is available for [from, until] when no non-cancelled rental
    # overlaps that window.  Overlap condition:
    #   rental.start < window.end  AND  rental.end > window.start
    # NULL rental.end_time = open-ended (+infinity).
    if filters.available_from is not None or filters.available_until is not None:
        stmt = stmt.where(
            not_(
                exists(
                    _build_overlap_subquery(
                        filters.available_from, filters.available_until
                    )
                )
            )
        )

    return list(db.execute(stmt).scalars().all())


def _build_overlap_subquery(
    available_from: datetime | None,
    available_until: datetime | None,
):
    """
    Returns a correlated subquery that selects rental IDs which overlap
    with the requested availability window.  Used inside NOT EXISTS so
    that vehicles with zero matching rows are considered available.
    """
    conditions = [
        Rental.vehicle_id == Vehicle.id,  # correlation to outer Vehicle
        Rental.status != RentalStatus.cancelled,
    ]

    # Existing rental ends after the requested window starts.
    if available_from is not None:
        conditions.append(
            or_(Rental.end_time.is_(None), Rental.end_time > _to_naive_utc(available_from))
        )

    # Existing rental starts before the requested window ends.
    if available_until is not None:
        conditions.append(Rental.start_time < _to_naive_utc(available_until))

    return select(Rental.id).where(*conditions).correlate(Vehicle)


def get_vehicle(db: Session, vehicle_id: int) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise NotFoundError("Vehicle", vehicle_id)
    return vehicle


def create_vehicle(db: Session, data: VehicleCreate) -> Vehicle:
    vehicle = Vehicle(
        plate_number=data.plate_number,
        vehicle_type=data.vehicle_type,
        capacity=data.capacity,
        status=VehicleStatus.available,
        office_id=data.office_id,
    )
    db.add(vehicle)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BusinessRuleError(
            f"A vehicle with plate number '{data.plate_number}' already exists."
        )
    db.refresh(vehicle)
    return vehicle


def update_vehicle(db: Session, vehicle_id: int, data: VehicleUpdate) -> Vehicle:
    vehicle = get_vehicle(db, vehicle_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def delete_vehicle(db: Session, vehicle_id: int) -> None:
    vehicle = get_vehicle(db, vehicle_id)

    # Query the rentals table directly — more reliable than trusting vehicle.status,
    # which could be stale if a previous operation failed mid-transaction.
    active_rental_id = db.execute(
        select(Rental.id).where(
            Rental.vehicle_id == vehicle_id,
            Rental.status == RentalStatus.active,
        )
    ).scalar_one_or_none()

    if active_rental_id is not None:
        raise BusinessRuleError(
            f"Vehicle {vehicle_id} has an active rental (#{active_rental_id}) "
            "and cannot be deleted."
        )

    db.delete(vehicle)
    db.commit()
