"""工单接口：创建、分页、筛选、归属隔离、状态流转。"""

from __future__ import annotations

from .conftest import ALICE, BOB, auth_headers, login

BASE_PAYLOAD = {
    "title": "登录后报 500 错误",
    "description": "点击登录按钮后页面直接报 500，控制台没有任何有效信息。",
    "priority": "high",
}


def create(client, token, **overrides):
    payload = {**BASE_PAYLOAD, **overrides}
    return client.post("/api/tickets", json=payload, headers=auth_headers(token))


def test_create_ticket_with_mock_ai(client, alice_token):
    resp = create(client, alice_token)
    assert resp.status_code == 201, resp.text

    body = resp.json()
    assert body["status"] == "open"
    assert body["ai_status"] == "ok"
    assert body["category"] == "bug"  # 描述里有「报 500」
    assert 0 < len(body["summary"]) <= 80
    assert body["summary"].startswith("点击登录按钮后页面直接报 500")


def test_create_ticket_blank_title_rejected(client, alice_token):
    resp = create(client, alice_token, title="   ")
    assert resp.status_code == 422
    body = resp.json()
    assert body["detail"] == "参数校验失败"
    assert body["errors"][0]["field"] == "title"


def test_create_ticket_invalid_priority_rejected(client, alice_token):
    resp = create(client, alice_token, priority="urgent")
    assert resp.status_code == 422
    assert resp.json()["detail"] == "参数校验失败"


def test_list_pagination(client, alice_token):
    for i in range(5):
        assert create(client, alice_token, title=f"工单 {i}").status_code == 201

    resp = client.get(
        "/api/tickets", params={"page": 1, "page_size": 2}, headers=auth_headers(alice_token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2

    last = client.get(
        "/api/tickets", params={"page": 3, "page_size": 2}, headers=auth_headers(alice_token)
    ).json()
    assert len(last["items"]) == 1


def test_filter_by_status_and_priority(client, alice_token):
    h = auth_headers(alice_token)
    first = create(client, alice_token, priority="low").json()["id"]
    second = create(client, alice_token, priority="high").json()["id"]
    create(client, alice_token, priority="high")

    assert client.patch(f"/api/tickets/{first}/status", json={"status": "in_progress"}, headers=h).status_code == 200
    assert client.patch(f"/api/tickets/{second}/status", json={"status": "done"}, headers=h).status_code == 200

    only_open = client.get("/api/tickets", params={"status": "open"}, headers=h).json()
    assert only_open["total"] == 1

    only_high = client.get("/api/tickets", params={"priority": "high"}, headers=h).json()
    assert only_high["total"] == 2

    combo = client.get("/api/tickets", params={"status": "done", "priority": "high"}, headers=h).json()
    assert combo["total"] == 1
    assert combo["items"][0]["id"] == second


def test_users_cannot_see_or_touch_others_tickets(client, alice_token, bob_token):
    ticket_id = create(client, alice_token).json()["id"]
    bob_headers = auth_headers(bob_token)

    assert client.get("/api/tickets", headers=bob_headers).json()["total"] == 0
    assert client.get(f"/api/tickets/{ticket_id}", headers=bob_headers).status_code == 404
    assert (
        client.patch(
            f"/api/tickets/{ticket_id}/status", json={"status": "done"}, headers=bob_headers
        ).status_code
        == 404
    )

    # 原主人一切正常
    assert client.get(f"/api/tickets/{ticket_id}", headers=auth_headers(alice_token)).status_code == 200


def test_update_status(client, alice_token):
    ticket_id = create(client, alice_token).json()["id"]
    resp = client.patch(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "in_progress"},
        headers=auth_headers(alice_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_update_status_invalid_value(client, alice_token):
    ticket_id = create(client, alice_token).json()["id"]
    resp = client.patch(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "closed"},
        headers=auth_headers(alice_token),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "参数校验失败"


def test_get_missing_ticket_returns_404(client, alice_token):
    assert client.get("/api/tickets/9999", headers=auth_headers(alice_token)).status_code == 404


def test_login_then_list_is_empty_for_new_user(client):
    token = login(client, BOB)
    body = client.get("/api/tickets", headers=auth_headers(token)).json()
    assert body["total"] == 0
    assert body["items"] == []
