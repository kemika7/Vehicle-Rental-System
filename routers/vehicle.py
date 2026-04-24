from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_employee, require_admin
from database import get_db
from exceptions import BusinessRuleError, NotFoundError
from schemas.filters import VehicleFilters
from schemas.vehicle import VehicleCreate, VehicleResponse, VehicleUpdate
from services import vehicle as vehicle_svc

router = APIRouter(
    prefix="/vehicles",
    tags=["vehicles"],
    dependencies=[Depends(get_current_employee)],  # every route requires a valid token
)


@router.get("", response_model=list[VehicleResponse])
def list_vehicles(
    filters: Annotated[VehicleFilters, Query()],
    db: Session = Depends(get_db),
) -> list[VehicleResponse]:
    return vehicle_svc.list_vehicles(db, filters)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)) -> VehicleResponse:
    try:
        return vehicle_svc.get_vehicle(db, vehicle_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_vehicle(
    data: VehicleCreate, db: Session = Depends(get_db)
) -> VehicleResponse:
    try:
        return vehicle_svc.create_vehicle(db, data)
    except BusinessRuleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.patch(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    dependencies=[Depends(require_admin)],
)
def update_vehicle(
    vehicle_id: int, data: VehicleUpdate, db: Session = Depends(get_db)
) -> VehicleResponse:
    try:
        return vehicle_svc.update_vehicle(db, vehicle_id, data)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)) -> None:
    try:
        vehicle_svc.delete_vehicle(db, vehicle_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BusinessRuleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
