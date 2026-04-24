"""
Shared fixtures for all tests.

Database strategy
─────────────────
A single in-memory SQLite engine with StaticPool is created once for the
test session.  Before every test the schema is dropped and recreated so
each test starts with a clean, empty database.

Auth strategy
─────────────
Real JWT tokens are generated via create_access_token so the full
authentication stack is exercised (no mocking of dependencies).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.security import create_access_token, hash_password
from database import get_db
from main import app
from models.base import Base
from models.employee import Employee
from models.enums import Role, VehicleStatus, VehicleType
from models.office import Office
from models.vehicle import Vehicle

# ---------------------------------------------------------------------------
# Test database
# ---------------------------------------------------------------------------

_TEST_DB_URL = "sqlite:///:memory:"

_test_engine = create_engine(
    _TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # every connection reuses the same in-memory DB
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


# Wire the override once at import time — applies for the whole test run.
app.dependency_overrides[get_db] = _override_get_db


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Per-test isolation — drop & recreate schema before every test
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_db() -> None:
    Base.metadata.drop_all(_test_engine)
    Base.metadata.create_all(_test_engine)
    yield


# ---------------------------------------------------------------------------
# Short-lived DB session (used by fixtures that insert seed rows)
# ---------------------------------------------------------------------------


@pytest.fixture
def db():
    session = _TestingSession()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# Domain fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def office(db) -> Office:
    obj = Office(name="HQ", location="New York")
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@pytest.fixture
def second_office(db) -> Office:
    obj = Office(name="Branch", location="Chicago")
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@pytest.fixture
def admin_employee(db, office) -> Employee:
    obj = Employee(
        name="Admin User",
        email="admin@test.com",
        hashed_password=hash_password("adminpass1"),
        role=Role.admin,
        office_id=office.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@pytest.fixture
def regular_employee(db, office) -> Employee:
    obj = Employee(
        name="Jane Employee",
        email="jane@test.com",
        hashed_password=hash_password("emppass123"),
        role=Role.employee,
        office_id=office.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@pytest.fixture
def other_office_employee(db, second_office) -> Employee:
    obj = Employee(
        name="Branch User",
        email="branch@test.com",
        hashed_password=hash_password("branchpass1"),
        role=Role.employee,
        office_id=second_office.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@pytest.fixture
def vehicle(db, office) -> Vehicle:
    obj = Vehicle(
        plate_number="TEST-001",
        vehicle_type=VehicleType.sedan,
        capacity=5,
        status=VehicleStatus.available,
        office_id=office.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@pytest.fixture
def second_office_vehicle(db, second_office) -> Vehicle:
    obj = Vehicle(
        plate_number="BRANCH-001",
        vehicle_type=VehicleType.suv,
        capacity=7,
        status=VehicleStatus.available,
        office_id=second_office.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ---------------------------------------------------------------------------
# Auth header fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_headers(admin_employee) -> dict:
    token = create_access_token(admin_employee.id, Role.admin.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def employee_headers(regular_employee) -> dict:
    token = create_access_token(regular_employee.id, Role.employee.value)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Rental payload helper
# ---------------------------------------------------------------------------


def future_rental_payload(
    vehicle_id: int,
    employee_id: int,
    start_offset_days: int = 10,
    duration_hours: int = 8,
) -> dict:
    from datetime import datetime, timedelta, timezone

    start = datetime(2030, 1, 1, 9, 0, tzinfo=timezone.utc) + timedelta(
        days=start_offset_days
    )
    end = start + timedelta(hours=duration_hours)
    return {
        "vehicle_id": vehicle_id,
        "employee_id": employee_id,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
    }
