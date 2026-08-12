import pytest


def test_register_success(client):
    resp = client.post("/api/v1/auth/register", json={
        "name": "New User",
        "email": "newuser@test.com",
        "password": "NewUser1234",
        "role": "Donor",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "Donor"
    assert "id" in data


def test_register_duplicate_email(client, donor_user):
    resp = client.post("/api/v1/auth/register", json={
        "name": "Dup",
        "email": "donor@test.com",
        "password": "Donor1234",
        "role": "Donor",
    })
    assert resp.status_code == 409


def test_register_weak_password(client):
    resp = client.post("/api/v1/auth/register", json={
        "name": "Weak",
        "email": "weak@test.com",
        "password": "abc",
        "role": "Donor",
    })
    assert resp.status_code == 422


def test_login_success(client, donor_user):
    resp = client.post("/api/v1/auth/login", json={
        "email": "donor@test.com",
        "password": "Donor1234",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, donor_user):
    resp = client.post("/api/v1/auth/login", json={
        "email": "donor@test.com",
        "password": "WrongPass99",
    })
    assert resp.status_code == 401


def test_refresh_token(client, donor_user):
    login = client.post("/api/v1/auth/login", json={
        "email": "donor@test.com",
        "password": "Donor1234",
    })
    refresh = login.json()["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_get_me(client, donor_token):
    resp = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {donor_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "Donor"


def test_get_me_unauthenticated(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 403
