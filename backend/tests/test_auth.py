from jose import jwt

from app.core.config import settings
from app.models.user import User
from tests.conftest import auth_header, login_user, register_user


def test_registration_succeeds_without_exposing_password(client):
    response = register_user(client, "alice")

    assert response.status_code == 201
    assert response.json()["username"] == "alice"
    assert "hashed_password" not in response.json()
    assert "password" not in response.json()


def test_login_succeeds(client):
    register_user(client, "alice")

    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "strongpass123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_me_returns_authenticated_user(client):
    register_user(client, "alice")
    token = login_user(client, "alice")

    response = client.get("/auth/me", headers=auth_header(token))

    assert response.status_code == 200
    assert response.json()["username"] == "alice"
    assert "hashed_password" not in response.json()


def test_duplicate_username_is_rejected(client):
    register_user(client, "alice", "first@example.com")

    response = register_user(client, "alice", "second@example.com")

    assert response.status_code == 409
    assert response.json()["detail"] == "Username already in use"


def test_duplicate_email_is_rejected(client):
    register_user(client, "alice", "same@example.com")

    response = register_user(client, "bob", "same@example.com")

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already in use"


def test_invalid_password_is_rejected(client):
    register_user(client, "alice")

    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_non_numeric_jwt_subject_is_rejected(client):
    token = jwt.encode(
        {"sub": "not-a-number"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get("/auth/me", headers=auth_header(token))

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token"


def test_inactive_user_cannot_login(client, db_session):
    register_user(client, "alice")
    user = db_session.query(User).filter(User.username == "alice").one()
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "strongpass123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Inactive user"
