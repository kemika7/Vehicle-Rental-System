"""
Vehicle CRUD — happy paths, validation failures, auth/authz, search filters.
"""

from tests.conftest import future_rental_payload


# ---------------------------------------------------------------------------
# Auth / access control
# ---------------------------------------------------------------------------


def test_list_vehicles_requires_auth(client):
    assert client.get("/vehicles").status_code == 401


def test_list_vehicles_empty(client, admin_headers):
    resp = client.get("/vehicles", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_vehicle_requires_admin(client, employee_headers, office):
    payload = {
        "plate_number": "ABC-001",
        "vehicle_type": "sedan",
        "capacity": 5,
        "office_id": office.id,
    }
    assert client.post("/vehicles", headers=employee_headers, json=payload).status_code == 403


def test_create_vehicle_requires_auth(client, office):
    payload = {
        "plate_number": "ABC-002",
        "vehicle_type": "sedan",
        "capacity": 5,
        "office_id": office.id,
    }
    assert client.post("/vehicles", json=payload).status_code == 401


def test_update_vehicle_requires_admin(client, employee_headers, vehicle):
    assert (
        client.patch(f"/vehicles/{vehicle.id}", headers=employee_headers, json={"capacity": 9}).status_code
        == 403
    )


def test_delete_vehicle_requires_admin(client, employee_headers, vehicle):
    assert client.delete(f"/vehicles/{vehicle.id}", headers=employee_headers).status_code == 403


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_vehicle_success(client, admin_headers, office):
    resp = client.post(
        "/vehicles",
        headers=admin_headers,
        json={
            "plate_number": "ABC-123",
            "vehicle_type": "suv",
            "capacity": 7,
            "office_id": office.id,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["plate_number"] == "ABC-123"
    assert data["vehicle_type"] == "suv"
    assert data["capacity"] == 7
    assert data["status"] == "available"


def test_create_vehicle_invalid_plate_lowercase(client, admin_headers, office):
    resp = client.post(
        "/vehicles",
        headers=admin_headers,
        json={"plate_number": "abc-123", "vehicle_type": "sedan", "capacity": 5, "office_id": office.id},
    )
    assert resp.status_code == 422


def test_create_vehicle_invalid_plate_special_chars(client, admin_headers, office):
    resp = client.post(
        "/vehicles",
        headers=admin_headers,
        json={"plate_number": "AB!@#", "vehicle_type": "sedan", "capacity": 5, "office_id": office.id},
    )
    assert resp.status_code == 422


def test_create_vehicle_zero_capacity(client, admin_headers, office):
    resp = client.post(
        "/vehicles",
        headers=admin_headers,
        json={"plate_number": "XYZ-001", "vehicle_type": "sedan", "capacity": 0, "office_id": office.id},
    )
    assert resp.status_code == 422


def test_create_vehicle_duplicate_plate(client, admin_headers, vehicle, office):
    resp = client.post(
        "/vehicles",
        headers=admin_headers,
        json={
            "plate_number": vehicle.plate_number,
            "vehicle_type": "van",
            "capacity": 8,
            "office_id": office.id,
        },
    )
    # SQLite raises IntegrityError for the unique constraint — FastAPI returns 500
    # or 409 depending on exception handling; we just assert it is not 2xx.
    assert resp.status_code >= 400


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def test_get_vehicle_success(client, admin_headers, vehicle):
    resp = client.get(f"/vehicles/{vehicle.id}", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == vehicle.id
    assert data["plate_number"] == vehicle.plate_number


def test_get_vehicle_not_found(client, admin_headers):
    assert client.get("/vehicles/99999", headers=admin_headers).status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_vehicle_partial(client, admin_headers, vehicle):
    resp = client.patch(
        f"/vehicles/{vehicle.id}", headers=admin_headers, json={"capacity": 9}
    )
    assert resp.status_code == 200
    assert resp.json()["capacity"] == 9


def test_update_vehicle_status_to_maintenance(client, admin_headers, vehicle):
    resp = client.patch(
        f"/vehicles/{vehicle.id}", headers=admin_headers, json={"status": "maintenance"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "maintenance"


def test_update_vehicle_not_found(client, admin_headers):
    assert (
        client.patch("/vehicles/99999", headers=admin_headers, json={"capacity": 5}).status_code == 404
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_vehicle_success(client, admin_headers, vehicle):
    assert client.delete(f"/vehicles/{vehicle.id}", headers=admin_headers).status_code == 204
    assert client.get(f"/vehicles/{vehicle.id}", headers=admin_headers).status_code == 404


def test_delete_vehicle_not_found(client, admin_headers):
    assert client.delete("/vehicles/99999", headers=admin_headers).status_code == 404


def test_delete_vehicle_with_active_rental_rejected(
    client, admin_headers, employee_headers, vehicle, regular_employee
):
    payload = future_rental_payload(vehicle.id, regular_employee.id)
    client.post("/rentals", headers=employee_headers, json=payload)
    resp = client.delete(f"/vehicles/{vehicle.id}", headers=admin_headers)
    assert resp.status_code == 409
    assert "active rental" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Search / filters
# ---------------------------------------------------------------------------


def test_filter_by_vehicle_type(client, admin_headers, office):
    client.post("/vehicles", headers=admin_headers, json={"plate_number": "S-001", "vehicle_type": "sedan", "capacity": 5, "office_id": office.id})
    client.post("/vehicles", headers=admin_headers, json={"plate_number": "V-001", "vehicle_type": "van", "capacity": 8, "office_id": office.id})

    resp = client.get("/vehicles?vehicle_type=sedan", headers=admin_headers)
    assert resp.status_code == 200
    assert all(v["vehicle_type"] == "sedan" for v in resp.json())
    assert len(resp.json()) == 1


def test_filter_by_min_capacity(client, admin_headers, office):
    client.post("/vehicles", headers=admin_headers, json={"plate_number": "SM-001", "vehicle_type": "sedan", "capacity": 4, "office_id": office.id})
    client.post("/vehicles", headers=admin_headers, json={"plate_number": "LG-001", "vehicle_type": "suv", "capacity": 8, "office_id": office.id})

    resp = client.get("/vehicles?min_capacity=7", headers=admin_headers)
    assert resp.status_code == 200
    assert all(v["capacity"] >= 7 for v in resp.json())


def test_filter_by_capacity_range(client, admin_headers, office):
    for plate, cap in [("R1-001", 3), ("R1-002", 6), ("R1-003", 10)]:
        client.post("/vehicles", headers=admin_headers, json={"plate_number": plate, "vehicle_type": "sedan", "capacity": cap, "office_id": office.id})

    resp = client.get("/vehicles?min_capacity=5&max_capacity=7", headers=admin_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert all(5 <= v["capacity"] <= 7 for v in results)
    assert len(results) == 1


def test_filter_invalid_capacity_range_rejected(client, admin_headers):
    resp = client.get("/vehicles?min_capacity=10&max_capacity=5", headers=admin_headers)
    assert resp.status_code == 422


def test_filter_by_office(client, admin_headers, vehicle, second_office_vehicle):
    resp = client.get(f"/vehicles?office_id={vehicle.office_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert all(v["office_id"] == vehicle.office_id for v in resp.json())


def test_filter_available_excludes_booked_vehicle(
    client, admin_headers, employee_headers, vehicle, regular_employee
):
    window_start_json = "2030-06-01T09:00:00+00:00"
    window_end_json = "2030-06-01T17:00:00+00:00"
    # Use Z (not +00:00) in URLs — + is decoded as space in query strings.
    window_start_url = "2030-06-01T09:00:00Z"
    window_end_url = "2030-06-01T17:00:00Z"

    client.post(
        "/rentals",
        headers=employee_headers,
        json={
            "vehicle_id": vehicle.id,
            "employee_id": regular_employee.id,
            "start_time": window_start_json,
            "end_time": window_end_json,
        },
    )

    # Vehicle is booked — should not appear as available for that window.
    resp = client.get(
        f"/vehicles?available_from={window_start_url}&available_until={window_end_url}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert all(v["id"] != vehicle.id for v in resp.json())


def test_filter_available_includes_unbooked_vehicle(
    client, admin_headers, employee_headers, vehicle, regular_employee
):
    client.post(
        "/rentals",
        headers=employee_headers,
        json={
            "vehicle_id": vehicle.id,
            "employee_id": regular_employee.id,
            "start_time": "2030-06-01T09:00:00+00:00",
            "end_time": "2030-06-01T17:00:00+00:00",
        },
    )

    # Different window — vehicle should appear available. Use Z not +00:00 in URLs.
    resp = client.get(
        "/vehicles?available_from=2030-07-01T09:00:00Z&available_until=2030-07-01T17:00:00Z",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert any(v["id"] == vehicle.id for v in resp.json())


def test_filter_invalid_availability_range_rejected(client, admin_headers):
    resp = client.get(
        "/vehicles?available_from=2030-06-10T00:00:00Z&available_until=2030-06-01T00:00:00Z",
        headers=admin_headers,
    )
    assert resp.status_code == 422
