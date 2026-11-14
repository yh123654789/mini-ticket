"""演示账号种子数据。

密码以 bcrypt 哈希入库，源码里没有任何明文密码落库。
账号在 README「预置账号」里公开，仅用于 Demo。
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select

from .database import SessionLocal
from .models import User
from .security import hash_password

logger = logging.getLogger("app.seed")

DEMO_ACCOUNTS: tuple[tuple[str, str, str], ...] = (
    ("alice@example.com", "Alice Chen", "alice123"),
    ("bob@example.com", "Bob Li", "bob123"),
)


def seed_demo_users() -> int:
    """幂等：已有账号就跳过，返回新建数量。"""
    created = 0
    with SessionLocal() as db:
        existing = db.scalar(select(func.count()).select_from(User)) or 0
        if existing > 0:
            return 0
        for email, name, password in DEMO_ACCOUNTS:
            db.add(User(email=email, name=name, password_hash=hash_password(password)))
            created += 1
        db.commit()
    if created:
        logger.info("已创建 %d 个演示账号", created)
    return created
