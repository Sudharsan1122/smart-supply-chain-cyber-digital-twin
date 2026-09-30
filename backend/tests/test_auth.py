"""Authentication, JWT rotation, bcrypt hashing, and AES-256 encryption integration tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.security import decrypt_sensitive, encrypt_sensitive


def test_health_and_security_headers(client: TestClient) -> None:
    """Verify /health returns 200 and includes HSTS and anti-framing headers."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert "Strict-Transport-Security" in res.headers
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"


def test_register_login_and_refresh_rotation(client: TestClient) -> None:
    """Test user registration, duplicate rejection, login, and one-time refresh token rotation."""
    reg_payload = {
        "username": "sec_analyst",
        "password": "StrongPassword!2026",
        "role": "PLANNER",
        "org_id": None,
    }
    reg_res = client.post("/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    tokens = reg_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    dup_res = client.post("/auth/register", json=reg_payload)
    assert dup_res.status_code == 409

    login_res = client.post(
        "/auth/login",
        json={"username": "sec_analyst", "password": "StrongPassword!2026"},
    )
    assert login_res.status_code == 200
    old_refresh = login_res.json()["refresh_token"]

    rot_res = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert rot_res.status_code == 200
    new_refresh = rot_res.json()["refresh_token"]
    assert new_refresh != old_refresh

    # Reusing a rotated refresh token must fail with 401
    reuse_res = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse_res.status_code == 401


def test_invalid_login_and_unauthenticated_access(client: TestClient) -> None:
    """Verify invalid password and missing bearer token both return 401 Unauthorized."""
    bad_login = client.post("/auth/login", json={"username": "admin_user", "password": "WrongPassword99!"})
    assert bad_login.status_code == 401

    unauth = client.get("/twin/state")
    assert unauth.status_code == 401


def test_aes256_fernet_encryption_roundtrip() -> None:
    """Verify sensitive field encryption at rest produces non-plaintext ciphertext and roundtrips."""
    secret_text = "CONFIDENTIAL-SUPPLIER-SLA-9900"
    ciphertext = encrypt_sensitive(secret_text)
    assert ciphertext != secret_text
    assert decrypt_sensitive(ciphertext) == secret_text
