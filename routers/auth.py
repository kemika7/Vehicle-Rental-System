from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from exceptions import AuthenticationError, BusinessRuleError
from schemas.auth import TokenResponse
from schemas.employee import EmployeeCreate, EmployeeResponse
from services import auth as auth_svc

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def register(data: EmployeeCreate, db: Session = Depends(get_db)) -> EmployeeResponse:
    """
    Open endpoint — creates an employee account with role=employee.
    Admin accounts must be seeded directly in the database.
    """
    try:
        return auth_svc.register_employee(db, data)
    except BusinessRuleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Standard OAuth2 password flow.  Use `username` field for the email address.
    Returns a Bearer token valid for the configured expiry window.
    """
    try:
        token = auth_svc.login(db, form_data.username, form_data.password)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=token)
