"""工单接口：创建、列表（分页 + 筛选）、详情、状态更新。

所有接口都要求登录；所有查询都强制带 owner_id 过滤，保证用户之间互相隔离。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ai import analyze_ticket
from ..database import get_db
from ..deps import get_current_user
from ..models import Ticket, User
from ..schemas import (
    TicketCreate,
    TicketOut,
    TicketPage,
    TicketPriority,
    TicketStatus,
    TicketStatusUpdate,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def _get_own_ticket(ticket_id: int, user: User, db: Session) -> Ticket:
    """查不到和不属于你都返回 404，避免泄露「这条工单存在」。"""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.owner_id != user.id:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="工单不存在")
    return ticket


@router.post(
    "",
    response_model=TicketOut,
    status_code=http_status.HTTP_201_CREATED,
    summary="创建工单并同步生成 AI 摘要与分类",
)
def create_ticket(
    payload: TicketCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketOut:
    ai_result = analyze_ticket(payload.title, payload.description)

    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status="open",
        summary=ai_result.summary,
        category=ai_result.category,
        ai_status=ai_result.status,
        owner_id=current.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return TicketOut.model_validate(ticket)


@router.get("", response_model=TicketPage, summary="分页 + 按状态/优先级筛选自己的工单")
def list_tickets(
    status: TicketStatus | None = Query(default=None, description="open / in_progress / done"),
    priority: TicketPriority | None = Query(default=None, description="low / medium / high"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketPage:
    stmt = select(Ticket).where(Ticket.owner_id == current.id)
    if status is not None:
        stmt = stmt.where(Ticket.status == status)
    if priority is not None:
        stmt = stmt.where(Ticket.priority == priority)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Ticket.created_at.desc(), Ticket.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return TicketPage(
        items=[TicketOut.model_validate(t) for t in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{ticket_id}", response_model=TicketOut, summary="工单详情")
def get_ticket(
    ticket_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketOut:
    return TicketOut.model_validate(_get_own_ticket(ticket_id, current, db))


@router.patch("/{ticket_id}/status", response_model=TicketOut, summary="更新工单状态")
def update_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketOut:
    ticket = _get_own_ticket(ticket_id, current, db)
    ticket.status = payload.status
    db.commit()
    db.refresh(ticket)
    return TicketOut.model_validate(ticket)
