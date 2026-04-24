"""
Rental business logic — happy paths, domain-rule violations, status transitions,
date-range filtering, and authorization checks.
"""

from datetime import datetime, timedelta, timezone

from tests.conftest import future_rental_payload


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_list_rentals_requires_auth(client):
    assert client.get("/rentals").status_code == 401


def test_delete_rental_requires_admin(client, employee_headers, vehicle, regular_employee):
    created = client.post(
        "/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, regular_employee.id)
    ).json()
    # Cancel first so delete would otherwise succeed
    client.patch(f"/rentals/{created['id']}", headers=employee_headers, json={"status": "cancelled"})
    assert client.delete(f"/rentals/{created['id']}", headers=employee_headers).status_code == 403


# ---------------------------------------------------------------------------
# Create — happy path
# ---------------------------------------------------------------------------


def test_create_rental_success(client, employee_headers, vehicle, regular_employee):
    resp = client.post(
        "/rentals",
        headers=employee_headers,
        json=future_rental_payload(vehicle.id, regular_employee.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["vehicle_id"] == vehicle.id
    assert data["employee_id"] == regular_employee.id
    assert data["status"] == "active"


def test_create_rental_sets_vehicle_rented(
    client, admin_headers, employee_headers, vehicle, regular_employee
):
    client.post("/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, regular_employee.id))
    assert client.get(f"/vehicles/{vehicle.id}", headers=admin_headers).json()["status"] == "rented"


# ---------------------------------------------------------------------------
# Create — domain rule violations
# ---------------------------------------------------------------------------


def test_create_rental_vehicle_maintenance(
    client, admin_headers, employee_headers, vehicle, regular_employee
):
    client.patch(f"/vehicles/{vehicle.id}", headers=admin_headers, json={"status": "maintenance"})
    resp = client.post("/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, regular_employee.id))
    assert resp.status_code == 409
    assert "maintenance" in resp.json()["detail"].lower()


def test_create_rental_cross_office_rejected(
    client, employee_headers, second_office_vehicle, regular_employee
):
    """Employee from office A cannot rent a vehicle belonging to office B."""
    resp = client.post(
        "/rentals",
        headers=employee_headers,
        json=future_rental_payload(second_office_vehicle.id, regular_employee.id),
    )
    assert resp.status_code == 409
    assert "office" in resp.json()["detail"].lower()


def test_create_rental_time_overlap_rejected(
    client, employee_headers, vehicle, regular_employee
):
    payload = future_rental_payload(vehicle.id, regular_employee.id)
    client.post("/rentals", headers=employee_headers, json=payload)
    resp = client.post("/rentals", headers=employee_headers, json=payload)
    assert resp.status_code == 409
    assert "booked" in resp.json()["detail"].lower()


def test_create_rental_adjacent_slots_allowed(
    client, employee_headers, vehicle, regular_employee
):
    """Back-to-back bookings (A.end == B.start) must NOT be treated as overlapping."""
    t = datetime(2030, 3, 1, tzinfo=timezone.utc)
    slot1 = {"vehicle_id": vehicle.id, "employee_id": regular_employee.id,
              "start_time": t.isoformat(), "end_time": (t + timedelta(hours=4)).isoformat()}
    slot2 = {"vehicle_id": vehicle.id, "employee_id": regular_employee.id,
              "start_time": (t + timedelta(hours=4)).isoformat(),
              "end_time": (t + timedelta(hours=8)).isoformat()}

    assert client.post("/rentals", headers=employee_headers, json=slot1).status_code == 201
    assert client.post("/rentals", headers=employee_headers, json=slot2).status_code == 201


def test_create_rental_cancelled_slot_is_reusable(
    client, employee_headers, vehicle, regular_employee
):
    """A cancelled rental's time window should be available for rebooking."""
    payload = future_rental_payload(vehicle.id, regular_employee.id)
    r1 = client.post("/rentals", headers=employee_headers, json=payload).json()
    client.patch(f"/rentals/{r1['id']}", headers=employee_headers, json={"status": "cancelled"})
    resp = client.post("/rentals", headers=employee_headers, json=payload)
    assert resp.status_code == 201


def test_create_rental_vehicle_not_found(client, employee_headers, regular_employee):
    resp = client.post(
        "/rentals", headers=employee_headers, json=future_rental_payload(99999, regular_employee.id)
    )
    assert resp.status_code == 404


def test_create_rental_employee_not_found(client, employee_headers, vehicle):
    resp = client.post(
        "/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, 99999)
    )
    assert resp.status_code == 404


def test_create_rental_end_before_start_rejected(client, employee_headers, vehicle, regular_employee):
    now = datetime.now(timezone.utc)
    resp = client.post(
        "/rentals",
        headers=employee_headers,
        json={
            "vehicle_id": vehicle.id,
            "employee_id": regular_employee.id,
            "start_time": (now + timedelta(hours=5)).isoformat(),
            "end_time": (now + timedelta(hours=1)).isoformat(),
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def test_get_rental_detail_response(client, employee_headers, vehicle, regular_employee):
    created = client.post(
        "/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, regular_employee.id)
    ).json()
    resp = client.get(f"/rentals/{created['id']}", headers=employee_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "vehicle" in data and "employee" in data
    assert data["vehicle"]["id"] == vehicle.id
    assert data["employee"]["id"] == regular_employee.id


def test_get_rental_not_found(client, employee_headers):
    assert client.get("/rentals/99999", headers=employee_headers).status_code == 404


# ---------------------------------------------------------------------------
# Update — status transitions
# ---------------------------------------------------------------------------


def test_complete_rental_frees_vehicle(
    client, admin_headers, employee_headers, vehicle, regular_employee
):
    # future_rental_payload default: start_offset_days=10 → 2030-01-11 09:00 UTC
    created = client.post(
        "/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, regular_employee.id)
    ).json()

    resp = client.patch(
        f"/rentals/{created['id']}",
        headers=employee_headers,
        json={"status": "completed", "end_time": "2030-01-11T17:00:00+00:00"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert client.get(f"/vehicles/{vehicle.id}", headers=admin_headers).json()["status"] == "available"


def test_cancel_rental_frees_vehicle(
    client, admin_headers, employee_headers, vehicle, regular_employee
):
    created = client.post(
        "/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, regular_employee.id)
    ).json()

    resp = client.patch(
        f"/rentals/{created['id']}", headers=employee_headers, json={"status": "cancelled"}
    )
    assert resp.status_code == 200
    assert client.get(f"/vehicles/{vehicle.id}", headers=admin_headers).json()["status"] == "available"


def test_update_terminal_rental_rejected(client, employee_headers, vehicle, regular_employee):
    created = client.post(
        "/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, regular_employee.id)
    ).json()
    # Complete the rental with a valid end_time after the 2030-01-11 start.
    complete = client.patch(
        f"/rentals/{created['id']}",
        headers=employee_headers,
        json={"status": "completed", "end_time": "2030-01-11T17:00:00+00:00"},
    )
    assert complete.status_code == 200
    resp = client.patch(
        f"/rentals/{created['id']}", headers=employee_headers, json={"status": "cancelled"}
    )
    assert resp.status_code == 409
    assert "completed" in resp.json()["detail"].lower()


def test_update_end_time_before_start_rejected(client, employee_headers, vehicle, regular_employee):
    payload = future_rental_payload(vehicle.id, regular_employee.id, start_offset_days=5)
    created = client.post("/rentals", headers=employee_headers, json=payload).json()

    past_time = datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat()
    resp = client.patch(
        f"/rentals/{created['id']}", headers=employee_headers, json={"end_time": past_time}
    )
    assert resp.status_code == 409
    assert "start_time" in resp.json()["detail"].lower()


def test_extend_end_time_overlapping_next_rental_rejected(
    client, employee_headers, vehicle, regular_employee
):
    """Extending end_time into a subsequent rental's window must be blocked."""
    base = datetime(2030, 3, 1, 9, 0, tzinfo=timezone.utc)

    # r1: 09:00–13:00
    r1 = client.post("/rentals", headers=employee_headers, json={
        "vehicle_id": vehicle.id, "employee_id": regular_employee.id,
        "start_time": base.isoformat(),
        "end_time": (base + timedelta(hours=4)).isoformat(),
    }).json()
    assert r1.get("status") == "active"

    # r2: 13:00–17:00  (adjacent to r1, not overlapping — must succeed)
    r2_resp = client.post("/rentals", headers=employee_headers, json={
        "vehicle_id": vehicle.id, "employee_id": regular_employee.id,
        "start_time": (base + timedelta(hours=4)).isoformat(),
        "end_time": (base + timedelta(hours=8)).isoformat(),
    })
    assert r2_resp.status_code == 201

    # Extend r1 past 13:00 into r2's window — must be rejected.
    new_end = (base + timedelta(hours=6)).isoformat()
    resp = client.patch(f"/rentals/{r1['id']}", headers=employee_headers, json={"end_time": new_end})
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_active_rental_rejected(
    client, admin_headers, employee_headers, vehicle, regular_employee
):
    created = client.post(
        "/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, regular_employee.id)
    ).json()
    assert client.delete(f"/rentals/{created['id']}", headers=admin_headers).status_code == 409


def test_delete_cancelled_rental_success(
    client, admin_headers, employee_headers, vehicle, regular_employee
):
    created = client.post(
        "/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, regular_employee.id)
    ).json()
    client.patch(f"/rentals/{created['id']}", headers=employee_headers, json={"status": "cancelled"})
    assert client.delete(f"/rentals/{created['id']}", headers=admin_headers).status_code == 204


def test_delete_rental_not_found(client, admin_headers):
    assert client.delete("/rentals/99999", headers=admin_headers).status_code == 404


# ---------------------------------------------------------------------------
# List / filter
# ---------------------------------------------------------------------------


def test_filter_rentals_by_status(client, employee_headers, vehicle, regular_employee):
    payload = future_rental_payload(vehicle.id, regular_employee.id)
    created = client.post("/rentals", headers=employee_headers, json=payload).json()
    client.patch(f"/rentals/{created['id']}", headers=employee_headers, json={"status": "cancelled"})

    active = client.get("/rentals?status=active", headers=employee_headers).json()
    cancelled = client.get("/rentals?status=cancelled", headers=employee_headers).json()

    assert active == []
    assert len(cancelled) == 1


def test_filter_rentals_by_date_range(client, employee_headers, vehicle, regular_employee):
    # Rental in June 2030
    client.post(
        "/rentals",
        headers=employee_headers,
        json={
            "vehicle_id": vehicle.id,
            "employee_id": regular_employee.id,
            "start_time": "2030-06-10T09:00:00+00:00",
            "end_time": "2030-06-10T17:00:00+00:00",
        },
    )

    # Use Z not +00:00 in URLs — + is decoded as space in query strings.
    june = client.get(
        "/rentals?active_from=2030-06-01T00:00:00Z&active_until=2030-06-30T23:59:59Z",
        headers=employee_headers,
    )
    july = client.get(
        "/rentals?active_from=2030-07-01T00:00:00Z&active_until=2030-07-31T23:59:59Z",
        headers=employee_headers,
    )

    assert len(june.json()) == 1
    assert july.json() == []


def test_filter_rentals_by_office(
    client, employee_headers, vehicle, regular_employee,
    second_office_vehicle, other_office_employee, admin_headers
):
    # Regular employee rents a vehicle in their office
    client.post("/rentals", headers=employee_headers, json=future_rental_payload(vehicle.id, regular_employee.id))

    # other_office_employee rents the branch vehicle
    other_token = __import__("core.security", fromlist=["create_access_token"]).create_access_token(
        other_office_employee.id, "employee"
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}
    client.post("/rentals", headers=other_headers, json=future_rental_payload(second_office_vehicle.id, other_office_employee.id))

    resp = client.get(f"/rentals?office_id={vehicle.office_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_filter_invalid_date_range_rejected(client, employee_headers):
    resp = client.get(
        "/rentals?active_from=2030-06-10T00:00:00Z&active_until=2030-06-01T00:00:00Z",
        headers=employee_headers,
    )
    assert resp.status_code == 422
