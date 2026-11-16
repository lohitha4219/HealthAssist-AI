from sqlalchemy import select

from app.core.rate_limit import auth_rate_limiter
from app.core.security import verify_password
from app.models.user import User
from tests.conftest import register_and_login


def test_register_login_me_refresh_logout(client, test_db_session):
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Morgan",
            "email": "Alice@Example.com",
            "password": "HealthPass123",
            "confirm_password": "HealthPass123",
            "date_of_birth": "1994-05-12",
            "gender": "Female",
            "phone": "+1-555-0100",
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text
    tokens = reg_resp.json()
    assert tokens["message"] == "Registration successful"
    assert tokens["user"]["email"] == "alice@example.com"
    assert tokens["user"]["role"] == "patient"
    assert isinstance(tokens["user"]["id"], int)
    assert tokens["user"]["date_of_birth"] == "1994-05-12"
    assert tokens["user"]["gender"] == "Female"
    assert tokens["user"]["phone"] == "+1-555-0100"

    # Password is stored hashed (never plaintext)
    db_user = test_db_session.scalar(select(User).where(User.email == "alice@example.com"))
    assert db_user is not None
    assert db_user.hashed_password != "HealthPass123"
    assert db_user.hashed_password.startswith("$2")
    assert verify_password("HealthPass123", db_user.hashed_password)

    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    # Protected /me works with bearer token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["full_name"] == "Alice Morgan"

    # Unauthenticated /me rejected
    assert client.get("/api/auth/me").status_code == 401

    # Duplicate email rejected with 409
    dup = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Duplicate",
            "email": "alice@example.com",
            "password": "HealthPass123",
            "confirm_password": "HealthPass123",
        },
    )
    assert dup.status_code == 409

    # Login with valid credentials + remember_me
    login_resp = client.post(
        "/api/auth/login",
        json={
            "email": "alice@example.com",
            "password": "HealthPass123",
            "remember_me": True,
        },
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["user"]["email"] == "alice@example.com"

    # Refresh rotates token
    ref_resp = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert ref_resp.status_code == 200
    new_refresh = ref_resp.json()["refresh_token"]
    assert new_refresh != refresh

    # Old refresh token cannot be reused
    assert client.post("/api/auth/refresh", json={"refresh_token": refresh}).status_code == 401

    # Logout revokes current refresh token
    logout_resp = client.post(
        "/api/auth/logout",
        json={"refresh_token": new_refresh},
        headers={"Authorization": f"Bearer {ref_resp.json()['access_token']}"},
    )
    assert logout_resp.status_code == 200
    assert client.post("/api/auth/refresh", json={"refresh_token": new_refresh}).status_code == 401


def test_registration_validation_errors(client):
    # Invalid email
    assert (
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Valid User",
                "email": "not-an-email",
                "password": "HealthPass123",
                "confirm_password": "HealthPass123",
            },
        ).status_code
        == 422
    )

    # Missing required fields
    assert (
        client.post(
            "/api/auth/register",
            json={"email": "missing@example.com"},
        ).status_code
        == 422
    )

    # Invalid full name characters
    assert (
        client.post(
            "/api/auth/register",
            json={
                "full_name": "12345!!!",
                "email": "numname@example.com",
                "password": "HealthPass123",
                "confirm_password": "HealthPass123",
            },
        ).status_code
        == 422
    )

    # Weak password (no digit)
    assert (
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Weak Pass",
                "email": "weakpw@example.com",
                "password": "onlyletters",
                "confirm_password": "onlyletters",
            },
        ).status_code
        == 422
    )

    # Mismatched confirm_password
    assert (
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Mismatch User",
                "email": "mismatch@example.com",
                "password": "HealthPass123",
                "confirm_password": "HealthPass999",
            },
        ).status_code
        == 422
    )


def test_login_failures_and_inactive_account(client, test_db_session):
    register_and_login(client, email="statuscheck@example.com", password="HealthPass123")

    # Wrong password -> 401
    wrong_pw = client.post(
        "/api/auth/login",
        json={"email": "statuscheck@example.com", "password": "WrongPassword1"},
    )
    assert wrong_pw.status_code == 401

    # Unknown email -> 401
    unknown = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "HealthPass123"},
    )
    assert unknown.status_code == 401

    # Inactive account -> 403
    user = test_db_session.scalar(
        select(User).where(User.email == "statuscheck@example.com")
    )
    user.is_active = False
    test_db_session.commit()

    inactive_login = client.post(
        "/api/auth/login",
        json={"email": "statuscheck@example.com", "password": "HealthPass123"},
    )
    assert inactive_login.status_code == 403


def test_auth_rate_limiting(client):
    auth_rate_limiter.reset()
    for _ in range(20):
        resp = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "BadPassword1"},
        )
        assert resp.status_code == 401

    blocked = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "BadPassword1"},
    )
    assert blocked.status_code == 429
    auth_rate_limiter.reset()


def test_forgot_and_reset_password(client):
    register_and_login(client, email="reset@example.com", password="OldPassword1")
    forgot = client.post("/api/auth/forgot-password", json={"email": "reset@example.com"})
    assert forgot.status_code == 200
    token = forgot.json()["dev_reset_token"]
    assert token

    reset = client.post(
        "/api/auth/reset-password",
        json={
            "token": token,
            "new_password": "NewPassword2",
            "confirm_password": "NewPassword2",
        },
    )
    assert reset.status_code == 200

    old_login = client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "OldPassword1"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "NewPassword2"},
    )
    assert new_login.status_code == 200
