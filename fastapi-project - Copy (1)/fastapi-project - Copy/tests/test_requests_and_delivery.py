import pytest


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def _approved_donation(client, donor_token, admin_token) -> int:
    resp = client.post(
        "/api/v1/donations",
        json={"title": "Test Food", "food_type": "Mixed", "quantity": 30},
        headers=auth(donor_token),
    )
    did = resp.json()["id"]
    client.patch(f"/api/v1/donations/{did}/approve", headers=auth(admin_token))
    return did


# ── Charity Requests ───────────────────────────────────────────────────────────

def test_charity_can_request_approved_donation(
    client, donor_token, admin_token, charity_token
):
    did = _approved_donation(client, donor_token, admin_token)
    resp = client.post(
        "/api/v1/requests",
        json={"donation_id": did, "food_type": "Mixed", "quantity": 30},
        headers=auth(charity_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "Pending"
    assert data["donation_id"] == did


def test_charity_cannot_request_pending_donation(client, donor_token, charity_token):
    resp = client.post(
        "/api/v1/donations",
        json={"title": "Pending Food", "food_type": "Rice", "quantity": 10},
        headers=auth(donor_token),
    )
    did = resp.json()["id"]
    resp2 = client.post(
        "/api/v1/requests",
        json={"donation_id": did, "food_type": "Rice", "quantity": 10},
        headers=auth(charity_token),
    )
    assert resp2.status_code == 400


def test_duplicate_request_rejected(client, donor_token, admin_token, charity_token):
    did = _approved_donation(client, donor_token, admin_token)
    payload = {"donation_id": did, "food_type": "Mixed", "quantity": 10}
    client.post("/api/v1/requests", json=payload, headers=auth(charity_token))
    resp2 = client.post("/api/v1/requests", json=payload, headers=auth(charity_token))
    assert resp2.status_code == 409


def test_donor_cannot_create_request(client, donor_token, admin_token):
    did = _approved_donation(client, donor_token, admin_token)
    resp = client.post(
        "/api/v1/requests",
        json={"donation_id": did, "food_type": "Mixed", "quantity": 10},
        headers=auth(donor_token),
    )
    assert resp.status_code == 403


def test_charity_can_view_own_requests(client, donor_token, admin_token, charity_token):
    did = _approved_donation(client, donor_token, admin_token)
    client.post(
        "/api/v1/requests",
        json={"donation_id": did, "food_type": "Mixed", "quantity": 10},
        headers=auth(charity_token),
    )
    resp = client.get("/api/v1/requests/my", headers=auth(charity_token))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_admin_can_update_request_status(
    client, donor_token, admin_token, charity_token
):
    did = _approved_donation(client, donor_token, admin_token)
    req_resp = client.post(
        "/api/v1/requests",
        json={"donation_id": did, "food_type": "Mixed", "quantity": 10},
        headers=auth(charity_token),
    )
    rid = req_resp.json()["id"]
    resp = client.patch(
        f"/api/v1/requests/{rid}/status",
        json={"status": "Accepted"},
        headers=auth(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "Accepted"


# ── Volunteer Delivery ─────────────────────────────────────────────────────────

def test_admin_can_assign_volunteer(
    client, donor_token, admin_token, volunteer_user, volunteer_token
):
    did = _approved_donation(client, donor_token, admin_token)
    resp = client.post(
        "/api/v1/volunteers/assign",
        json={"donation_id": did, "volunteer_id": volunteer_user.id},
        headers=auth(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "Assigned"


def test_volunteer_can_update_delivery_status(
    client, donor_token, admin_token, volunteer_user, volunteer_token
):
    did = _approved_donation(client, donor_token, admin_token)
    assign = client.post(
        "/api/v1/volunteers/assign",
        json={"donation_id": did, "volunteer_id": volunteer_user.id},
        headers=auth(admin_token),
    )
    assignment_id = assign.json()["id"]
    resp = client.patch(
        f"/api/v1/volunteers/delivery-status/{assignment_id}",
        json={"status": "In_Transit"},
        headers=auth(volunteer_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "In_Transit"


def test_volunteer_deliver_updates_donation_status(
    client, donor_token, admin_token, volunteer_user, volunteer_token, db
):
    did = _approved_donation(client, donor_token, admin_token)
    assign = client.post(
        "/api/v1/volunteers/assign",
        json={"donation_id": did, "volunteer_id": volunteer_user.id},
        headers=auth(admin_token),
    )
    assignment_id = assign.json()["id"]
    resp = client.post(
        f"/api/v1/volunteers/deliver/{assignment_id}",
        headers=auth(volunteer_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "Delivered"

    # Donation should now be Delivered
    donation_resp = client.get(f"/api/v1/donations/{did}", headers=auth(admin_token))
    assert donation_resp.json()["status"] == "Delivered"


def test_volunteer_cannot_update_others_delivery(
    client, donor_token, admin_token, volunteer_user, db
):
    from core.security import hash_password
    from models.user import User, UserRole

    other_vol = User(
        name="Other Vol",
        email="othervol@test.com",
        hashed_password=hash_password("Volunteer1234"),
        role=UserRole.VOLUNTEER,
        is_active=True,
    )
    db.add(other_vol)
    db.commit()

    # Login as other volunteer
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "othervol@test.com", "password": "Volunteer1234"},
    )
    other_token = login_resp.json()["access_token"]

    did = _approved_donation(client, donor_token, admin_token)
    assign = client.post(
        "/api/v1/volunteers/assign",
        json={"donation_id": did, "volunteer_id": volunteer_user.id},
        headers=auth(admin_token),
    )
    assignment_id = assign.json()["id"]

    resp = client.patch(
        f"/api/v1/volunteers/delivery-status/{assignment_id}",
        json={"status": "In_Transit"},
        headers=auth(other_token),
    )
    assert resp.status_code == 403


# ── Admin Reports ──────────────────────────────────────────────────────────────

def test_admin_report(client, admin_token):
    resp = client.get("/api/v1/admin/reports", headers=auth(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    required_keys = [
        "total_users", "total_donors", "total_charities", "total_volunteers",
        "total_donations", "pending_donations", "approved_donations",
        "delivered_donations", "rejected_donations", "total_requests",
    ]
    for key in required_keys:
        assert key in data, f"Missing key: {key}"


def test_non_admin_cannot_access_reports(client, donor_token):
    resp = client.get("/api/v1/admin/reports", headers=auth(donor_token))
    assert resp.status_code == 403
