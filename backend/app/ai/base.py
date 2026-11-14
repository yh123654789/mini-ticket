"""AI Provider 抽象。

设计目标：工单创建流程只依赖 `AIProvider` 协议，不关心背后是 mock 还是真实模型。
新增一家服务商 = 新增一个实现类 + 工厂里加一个分支，不动业务代码。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

Category = Literal["bug", "feature", "consult", "other"]

CATEGORIES: tuple[str, ...] = ("bug", "feature", "consult", "other")
SUMMARY_MAX_CHARS = 80


class AIProviderError(RuntimeError):
    """Provider 内部任何异常都收敛成这个，方便上层统一降级。"""


@dataclass(frozen=True)
class AIResult:
    summary: str
    category: str
    status: Literal["ok", "failed"]
    provider: str
    error: str | None = None


@runtime_checkable
class AIProvider(Protocol):
    name: str

    def analyze(self, title: str, description: str) -> AIResult:
        """返回一句话摘要 + 分类。失败时应抛 AIProviderError，由上层降级。"""
        ...


def truncate(text: str, limit: int = SUMMARY_MAX_CHARS) -> str:
    """按字符截断（中文按字算，不是按字节）。"""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def normalize_category(raw: object) -> str:
    """模型可能返回大小写混乱或未知值，统一收敛到枚举。"""
    if isinstance(raw, str):
        value = raw.strip().lower()
        if value in CATEGORIES:
            return value
    return "other"
