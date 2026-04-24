from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.security import decode_access_token
from database import get_db
from exceptions import AuthenticationError
from models.employee import Employee
from models.enums import Role

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
_BEARER_HEADERS = {"WWW-Authenticate": "Bearer"}


def get_current_employee(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> Employee:
    try:
        payload = decode_access_token(token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers=_BEARER_HEADERS,
        )

    employee_id_str: str | None = payload.get("sub")
    if not employee_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token: missing subject",
            headers=_BEARER_HEADERS,
        )

    employee = db.get(Employee, int(employee_id_str))
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Employee account not found",
            headers=_BEARER_HEADERS,
        )

    return employee


def require_admin(
    current_employee: Employee = Depends(get_current_employee),
) -> Employee:
    if current_employee.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_employee


# ---------------------------------------------------------------------------
# Annotated shortcuts — use these directly in router signatures or as
# route/router-level dependencies=[...] arguments.
# ---------------------------------------------------------------------------

CurrentEmployee = Annotated[Employee, Depends(get_current_employee)]
AdminEmployee = Annotated[Employee, Depends(require_admin)]
