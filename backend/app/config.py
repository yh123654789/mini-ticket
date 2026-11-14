"""集中读取环境变量，避免散落在各处的 os.getenv。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


@dataclass(frozen=True)
class Settings:
    """运行期配置。全部来自环境变量，方便 docker-compose 注入。"""

    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    ai_provider: str
    ai_base_url: str
    ai_api_key: str
    ai_model: str
    ai_timeout_seconds: float
    seed_demo_users: bool

    @property
    def ai_configured(self) -> bool:
        """openai-compatible 模式至少要有 base_url 和 model 才算配置完整。"""
        return bool(self.ai_base_url and self.ai_model)


@lru_cache
def get_settings() -> Settings:
    backend_dir = Path(__file__).resolve().parent.parent
    default_db = f"sqlite:///{(backend_dir / 'tickets.db').as_posix()}"
    return Settings(
        database_url=_env("DATABASE_URL", default_db),
        jwt_secret=_env("JWT_SECRET", "dev-only-secret-change-me-32bytes-minimum!"),
        jwt_algorithm=_env("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(_env("ACCESS_TOKEN_EXPIRE_MINUTES", "720")),
        ai_provider=_env("AI_PROVIDER", "mock").lower() or "mock",
        ai_base_url=_env("AI_BASE_URL", "https://api.openai.com/v1"),
        ai_api_key=_env("AI_API_KEY", ""),
        ai_model=_env("AI_MODEL", ""),
        ai_timeout_seconds=float(_env("AI_TIMEOUT_SECONDS", "10")),
        seed_demo_users=_env("SEED_DEMO_USERS", "true").lower() in {"1", "true", "yes"},
    )


def reset_settings_cache() -> None:
    """测试里改了环境变量后调用。"""
    get_settings.cache_clear()
