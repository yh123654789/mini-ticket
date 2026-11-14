"""AI 分析服务：选择 Provider + 失败降级。

降级策略（验收清单第 4 条）：
- 任何异常（超时、连不上、返回格式不对、未配置）都不向上抛；
- 工单照常保存，summary 退化为「截断后的原文」，category 固定 other；
- ai_status 记为 failed，并在服务端日志留下原因。
"""

from __future__ import annotations

import logging

from ..config import get_settings
from .base import AIProvider, AIResult, truncate
from .mock import MockProvider
from .openai_compat import OpenAICompatibleProvider

logger = logging.getLogger("app.ai")


def build_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider == "openai":
        return OpenAICompatibleProvider(
            base_url=settings.ai_base_url,
            api_key=settings.ai_api_key,
            model=settings.ai_model,
            timeout=settings.ai_timeout_seconds,
        )
    if settings.ai_provider != "mock":
        logger.warning("未知 AI_PROVIDER=%s，回退到 mock", settings.ai_provider)
    return MockProvider()


def analyze_ticket(title: str, description: str) -> AIResult:
    settings = get_settings()
    try:
        provider = build_provider()
        return provider.analyze(title, description)
    except Exception as exc:  # noqa: BLE001 —— 故意兜住所有异常，绝不让工单创建失败
        logger.warning("AI 分析失败，已降级：%s", exc)
        fallback = truncate(description or title)
        return AIResult(
            summary=fallback,
            category="other",
            status="failed",
            provider=settings.ai_provider,
            error=str(exc)[:300],
        )
