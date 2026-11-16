"""应用入口：装配路由、跨域、启动时建表与播种。"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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


# ---------------- 单机部署：把前端静态文件也交给 FastAPI 发 ----------------
# 本地 / Docker Compose 用 nginx 代理时，这个目录不存在，下面整段自动跳过。
STATIC_DIR = Path(__file__).resolve().parent / "static"

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        """找不到的路径一律回 index.html，交给前端路由处理。"""
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
