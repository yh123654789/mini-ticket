"""应用入口：装配路由、跨域、启动时建表与播种。"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db
from .routers import auth, tickets
from .seed import seed_demo_users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    if settings.seed_demo_users:
        seed_demo_users()
    logger.info("Mini Ticket 已启动 | AI_PROVIDER=%s | DB=%s", settings.ai_provider, settings.database_url)
    yield


app = FastAPI(
    title="Mini Ticket API",
    description="带 AI 摘要与分类的内部工单系统",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

# Demo 场景前端与后端可能不同端口，直接放开；生产应收敛为具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """把 pydantic 的原始报错整理成人能看懂的结构。"""
    details = [
        {
            "field": ".".join(str(part) for part in err.get("loc", ())[1:]) or "(body)",
            "message": err.get("msg", "invalid value"),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": "参数校验失败", "errors": details},
    )


app.include_router(auth.router)
app.include_router(tickets.router)


@app.get("/api/health", tags=["meta"], summary="健康检查")
def health() -> dict[str, str]:
    return {"status": "ok", "ai_provider": get_settings().ai_provider}
