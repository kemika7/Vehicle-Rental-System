from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_employee, require_admin
from database import get_db
from exceptions import BusinessRuleError, NotFoundError
from schemas.filters import RentalFilters
from schemas.rental import (
    RentalCreate,
    RentalDetailResponse,
    RentalResponse,
    RentalUpdate,
)
from services import rental as rental_svc

router = APIRouter(
    prefix="/rentals",
    tags=["rentals"],
    dependencies=[Depends(get_current_employee)],  # every route requires a valid token
)


@router.get("", response_model=list[RentalResponse])
def list_rentals(
    filters: Annotated[RentalFilters, Query()],
    db: Session = Depends(get_db),
) -> list[RentalResponse]:
    return rental_svc.list_rentals(db, filters)


@router.get("/{rental_id}", response_model=RentalDetailResponse)
def get_rental(rental_id: int, db: Session = Depends(get_db)) -> RentalDetailResponse:
    try:
        return rental_svc.get_rental(db, rental_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("", response_model=RentalResponse, status_code=status.HTTP_201_CREATED)
def create_rental(
    data: RentalCreate, db: Session = Depends(get_db)
) -> RentalResponse:
    try:
        return rental_svc.create_rental(db, data)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BusinessRuleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.patch("/{rental_id}", response_model=RentalResponse)
def update_rental(
    rental_id: int, data: RentalUpdate, db: Session = Depends(get_db)
) -> RentalResponse:
    try:
        return rental_svc.update_rental(db, rental_id, data)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BusinessRuleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.delete(
    "/{rental_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_rental(rental_id: int, db: Session = Depends(get_db)) -> None:
    try:
        rental_svc.delete_rental(db, rental_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BusinessRuleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
