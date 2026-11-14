"""ORM 模型。

数据库设计说明见 README「数据库设计」一节。要点：
- 枚举以字符串存储（SQLite 友好，迁移时改字面量即可，无需 ALTER TYPE）。
- tickets.owner_id 建索引，列表查询永远带 owner 过滤。
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="owner")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    # open | in_progress | done
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    # low | medium | high
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True)

    # AI 结果：失败时 summary 退化为截断原文，category 固定 other
    summary: Mapped[str] = mapped_column(String(200), default="")
    category: Mapped[str] = mapped_column(String(20), default="other")
    # ok | failed —— 记录本次 AI 处理是否成功，便于排查
    ai_status: Mapped[str] = mapped_column(String(20), default="ok")

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    owner: Mapped[User] = relationship(back_populates="tickets")

    __table_args__ = (Index("ix_tickets_owner_status", "owner_id", "status"),)
