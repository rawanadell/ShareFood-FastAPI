import pytest


DONATION_PAYLOAD = {
    "title": "Fresh Sandwiches",
    "description": "50 sandwiches from morning event",
    "food_type": "Sandwiches",
    "quantity": 50,
}


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── Create ─────────────────────────────────────────────────────────────────────

def test_donor_can_create_donation(client, donor_token):
    resp = client.post("/api/v1/donations", json=DONATION_PAYLOAD, headers=auth(donor_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Fresh Sandwiches"
    assert data["status"] == "Pending"


def test_charity_cannot_create_donation(client, charity_token):
    resp = client.post("/api/v1/donations", json=DONATION_PAYLOAD, headers=auth(charity_token))
    assert resp.status_code == 403


def test_create_donation_zero_quantity(client, donor_token):
    bad = {**DONATION_PAYLOAD, "quantity": 0}
    resp = client.post("/api/v1/donations", json=bad, headers=auth(donor_token))
    assert resp.status_code == 422


# ── Approve / Reject ───────────────────────────────────────────────────────────

def _create_donation(client, donor_token):
    resp = client.post("/api/v1/donations", json=DONATION_PAYLOAD, headers=auth(donor_token))
    assert resp.status_code == 201
    return resp.json()["id"]


def test_admin_can_approve(client, donor_token, admin_token):
    did = _create_donation(client, donor_token)
    resp = client.patch(f"/api/v1/donations/{did}/approve", headers=auth(admin_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "Approved"


def test_donor_cannot_approve(client, donor_token):
    did = _create_donation(client, donor_token)
    resp = client.patch(f"/api/v1/donations/{did}/approve", headers=auth(donor_token))
    assert resp.status_code == 403


def test_admin_can_reject_with_reason(client, donor_token, admin_token):
    did = _create_donation(client, donor_token)
    resp = client.patch(
        f"/api/v1/donations/{did}/reject",
        json={"reason": "Quality not up to standard"},
        headers=auth(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Rejected"
    assert data["rejection_reason"] == "Quality not up to standard"


def test_cannot_approve_already_approved(client, donor_token, admin_token):
    did = _create_donation(client, donor_token)
    client.patch(f"/api/v1/donations/{did}/approve", headers=auth(admin_token))
    resp = client.patch(f"/api/v1/donations/{did}/approve", headers=auth(admin_token))
    assert resp.status_code == 400


# ── Edit / Delete ──────────────────────────────────────────────────────────────

def test_donor_can_edit_pending_donation(client, donor_token):
    did = _create_donation(client, donor_token)
    resp = client.put(
        f"/api/v1/donations/{did}",
        json={"title": "Updated Title", "quantity": 75},
        headers=auth(donor_token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"


def test_donor_cannot_edit_approved_donation(client, donor_token, admin_token):
    did = _create_donation(client, donor_token)
    client.patch(f"/api/v1/donations/{did}/approve", headers=auth(admin_token))
    resp = client.put(
        f"/api/v1/donations/{did}",
        json={"title": "Try Edit"},
        headers=auth(donor_token),
    )
    assert resp.status_code == 400


def test_donor_can_delete_pending_donation(client, donor_token):
    did = _create_donation(client, donor_token)
    resp = client.delete(f"/api/v1/donations/{did}", headers=auth(donor_token))
    assert resp.status_code == 204


def test_donor_cannot_delete_approved_donation(client, donor_token, admin_token):
    did = _create_donation(client, donor_token)
    client.patch(f"/api/v1/donations/{did}/approve", headers=auth(admin_token))
    resp = client.delete(f"/api/v1/donations/{did}", headers=auth(donor_token))
    assert resp.status_code == 400


# ── Track / Audit ──────────────────────────────────────────────────────────────

def test_track_donation_shows_history(client, donor_token, admin_token):
    did = _create_donation(client, donor_token)
    client.patch(f"/api/v1/donations/{did}/approve", headers=auth(admin_token))
    resp = client.get(f"/api/v1/donations/track/{did}", headers=auth(donor_token))
    assert resp.status_code == 200
    body = resp.json()
    assert "history" in body
    actions = [h["action"] for h in body["history"]]
    assert "CREATED" in actions
    assert "APPROVED" in actions


# ── Available donations ────────────────────────────────────────────────────────

def test_available_donations_only_approved(client, donor_token, admin_token, charity_token):
    did = _create_donation(client, donor_token)
    client.patch(f"/api/v1/donations/{did}/approve", headers=auth(admin_token))

    resp = client.get("/api/v1/donations/available", headers=auth(charity_token))
    assert resp.status_code == 200
    statuses = [d["status"] for d in resp.json()["items"]]
    assert all(s == "Approved" for s in statuses)
