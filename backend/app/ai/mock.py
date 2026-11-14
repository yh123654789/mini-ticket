"""Mock Provider：没有 API Key 也能跑，且结果可预期（测试依赖这一点）。"""

from __future__ import annotations

import re

from .base import AIProviderError, AIResult, truncate

# 关键词 → 分类。命中顺序：bug > feature > consult，都没命中就是 other。
_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "bug",
        ("报错", "崩溃", "错误", "异常", "失败", "无法", "打不开", "bug", "error", "crash", "500", "404"),
    ),
    (
        "feature",
        ("希望", "建议", "增加", "支持", "新功能", "需求", "能不能", "feature", "request", "add"),
    ),
    (
        "consult",
        ("怎么", "如何", "为什么", "咨询", "请问", "是不是", "how", "why", "what"),
    ),
)

_SENTENCE_END = re.compile(r"[。！？!?\n]")


class MockProvider:
    """确定性实现：同样的输入永远得到同样的输出。"""

    name = "mock"

    def analyze(self, title: str, description: str) -> AIResult:
        if not title.strip() and not description.strip():
            raise AIProviderError("标题与描述都为空，mock 无法分析")

        text = f"{title} {description}".lower()
        category = "other"
        for name, words in _KEYWORDS:
            if any(word in text for word in words):
                category = name
                break

        first_sentence = _SENTENCE_END.split(description.strip(), maxsplit=1)[0].strip()
        summary = truncate(first_sentence or title.strip())

        return AIResult(summary=summary, category=category, status="ok", provider=self.name)
