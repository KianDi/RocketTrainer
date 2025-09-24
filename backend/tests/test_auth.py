"""
Test authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


def test_steam_login_new_user(client: TestClient, db: Session):
    """Test Steam login with new user."""
    response = client.post("/auth/steam-login", json={
        "steam_id": "76561198000000001",
        "username": "newuser"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "newuser"
    assert data["user"]["steam_id"] == "76561198000000001"
    
    # Verify user was created in database
    user = db.query(User).filter(User.steam_id == "76561198000000001").first()
    assert user is not None
    assert user.username == "newuser"


def test_steam_login_existing_user(client: TestClient, test_user: User):
    """Test Steam login with existing user."""
    response = client.post("/auth/steam-login", json={
        "steam_id": test_user.steam_id,
        "username": "updatedname"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["steam_id"] == test_user.steam_id


def test_steam_login_missing_steam_id(client: TestClient):
    """Test Steam login without Steam ID."""
    response = client.post("/auth/steam-login", json={
        "username": "testuser"
    })
    
    assert response.status_code == 400


def test_get_current_user_without_token(client: TestClient):
    """Test getting current user without authentication."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout(client: TestClient, test_user: User):
    """Test user logout."""
    # First login to get token
    login_response = client.post("/auth/steam-login", json={
        "steam_id": test_user.steam_id,
        "username": test_user.username
    })
    token = login_response.json()["access_token"]
    
    # Then logout
    response = client.post("/auth/logout", headers={
        "Authorization": f"Bearer {token}"
    })
    
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"
