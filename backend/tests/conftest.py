"""测试夹具：独立 SQLite 文件 + 每个用例重建数据。

注意环境变量必须在 import app.* 之前设置，因为 database.py 在导入时就创建了 engine。
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

_TMP_DB_DIR = Path(tempfile.mkdtemp(prefix="mini-ticket-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP_DB_DIR / 'test.db').as_posix()}"
os.environ["JWT_SECRET"] = "test-secret-only-but-long-enough-for-hs256"
os.environ["AI_PROVIDER"] = "mock"
os.environ["SEED_DEMO_USERS"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

from app.config import reset_settings_cache  # noqa: E402
from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.seed import seed_demo_users  # noqa: E402

ALICE = {"email": "alice@example.com", "password": "alice123"}
BOB = {"email": "bob@example.com", "password": "bob123"}


@pytest.fixture(autouse=True)
def fresh_database():
    """每个用例一套干净的表和演示账号。"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_demo_users()
    yield


@pytest.fixture
def client() -> TestClient:
    reset_settings_cache()
    with TestClient(app) as c:
        yield c


def login(client: TestClient, account: dict[str, str]) -> str:
    resp = client.post("/api/auth/login", json=account)
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice_token(client: TestClient) -> str:
    return login(client, ALICE)


@pytest.fixture
def bob_token(client: TestClient) -> str:
    return login(client, BOB)
