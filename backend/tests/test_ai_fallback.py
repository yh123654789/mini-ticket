"""AI 降级：模型不可用时，工单照常创建。"""

from __future__ import annotations

import pytest

from app.ai import AIProviderError, service as ai_service
from app.config import reset_settings_cache

from .conftest import auth_headers

PAYLOAD = {
    "title": "导出功能页面空白",
    "description": "点击导出按钮之后页面一片空白，重新刷新也没用。",
    "priority": "medium",
}


@pytest.fixture
def broken_openai_provider(monkeypatch):
    """把 Provider 指到一个必然连不上的地址，走真实的失败路径。"""
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_BASE_URL", "http://127.0.0.1:9/v1")
    monkeypatch.setenv("AI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("AI_TIMEOUT_SECONDS", "2")
    reset_settings_cache()
    yield


@pytest.fixture
def provider_that_raises(monkeypatch):
    def boom(*args, **kwargs):
        raise AIProviderError("模拟模型服务 500")

    monkeypatch.setattr(ai_service, "build_provider", boom)
    yield


def test_ticket_still_created_when_endpoint_unreachable(client, alice_token, broken_openai_provider):
    resp = client.post("/api/tickets", json=PAYLOAD, headers=auth_headers(alice_token))
    assert resp.status_code == 201

    body = resp.json()
    assert body["ai_status"] == "failed"
    assert body["category"] == "other"
    assert body["summary"]  # 退化成截断原文，而不是空字符串
    assert len(body["summary"]) <= 80


def test_ticket_still_created_when_provider_raises(client, alice_token, provider_that_raises):
    resp = client.post("/api/tickets", json=PAYLOAD, headers=auth_headers(alice_token))
    assert resp.status_code == 201
    assert resp.json()["ai_status"] == "failed"


def test_openai_provider_without_model_config_degrades(monkeypatch, client, alice_token):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_BASE_URL", "http://127.0.0.1:9/v1")
    monkeypatch.setenv("AI_MODEL", "")
    reset_settings_cache()

    resp = client.post("/api/tickets", json=PAYLOAD, headers=auth_headers(alice_token))
    assert resp.status_code == 201
    assert resp.json()["ai_status"] == "failed"


def test_health_reports_provider(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
