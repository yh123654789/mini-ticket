"""登录与鉴权。"""

from __future__ import annotations

from .conftest import ALICE, auth_headers, login


def test_login_success_returns_token_and_user(client):
    resp = client.post("/api/auth/login", json=ALICE)
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].count(".") == 2  # JWT 三段
    assert body["user"]["email"] == ALICE["email"]


def test_login_wrong_password_rejected(client):
    resp = client.post("/api/auth/login", json={"email": ALICE["email"], "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "邮箱或密码错误"


def test_login_unknown_account_rejected_with_same_message(client):
    resp = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "x"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "邮箱或密码错误"


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_valid_token(client):
    token = login(client, ALICE)
    resp = client.get("/api/auth/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice Chen"


def test_me_with_garbage_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_ticket_endpoints_require_login(client):
    assert client.get("/api/tickets").status_code == 401
    assert client.post("/api/tickets", json={"title": "x", "description": "y"}).status_code == 401
