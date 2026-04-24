from sqlalchemy import select
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password, verify_password
from exceptions import AuthenticationError, BusinessRuleError
from models.employee import Employee
from models.enums import Role
from schemas.employee import EmployeeCreate


def register_employee(db: Session, data: EmployeeCreate) -> Employee:
    existing = db.execute(
        select(Employee).where(Employee.email == data.email)
    ).scalar_one_or_none()
    if existing is not None:
        raise BusinessRuleError(f"Email '{data.email}' is already registered.")

    employee = Employee(
        name=data.name,
        email=str(data.email),
        hashed_password=hash_password(data.password),
        office_id=data.office_id,
        role=Role.employee,  # self-registration never grants admin
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def login(db: Session, email: str, password: str) -> str:
    employee = db.execute(
        select(Employee).where(Employee.email == email)
    ).scalar_one_or_none()

    # Deliberate: identical error for unknown email and wrong password
    # to prevent user-enumeration attacks.
    if employee is None or not verify_password(password, employee.hashed_password):
        raise AuthenticationError("Invalid email or password")

    return create_access_token(employee.id, employee.role.value)
