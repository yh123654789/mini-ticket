"""OpenAI 兼容 Provider：只要服务端实现 /chat/completions 就能接。

覆盖 OpenAI / DeepSeek / 通义 / Ollama（/v1）/ vLLM 等。
"""

from __future__ import annotations

import json
import re

import httpx

from .base import AIProviderError, AIResult, truncate, normalize_category

_PROMPT = """你是工单助手。阅读工单后只输出一个 JSON 对象，不要输出任何解释或 Markdown 代码块。

JSON 格式：
{{"summary": "一句话摘要，不超过 {limit} 个汉字", "category": "bug 或 feature 或 consult 或 other"}}

分类含义：
- bug：报错、崩溃、功能异常、数据错误
- feature：希望新增或改进功能
- consult：使用咨询、操作求助、信息询问
- other：以上都不是

标题：{title}
描述：{description}"""

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 10.0) -> None:
        if not base_url or not model:
            raise AIProviderError("AI_BASE_URL 与 AI_MODEL 必须配置")
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def analyze(self, title: str, description: str) -> AIResult:
        payload = {
            "model": self._model,
            "temperature": 0,
            "max_tokens": 200,
            "messages": [
                {
                    "role": "system",
                    "content": "你是严谨的工单分类助手，只输出 JSON。",
                },
                {
                    "role": "user",
                    "content": _PROMPT.format(limit=80, title=title, description=description),
                },
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(self._url, json=payload, headers=headers)
        except httpx.HTTPError as exc:  # 超时 / 连不上 / DNS 失败
            raise AIProviderError(f"请求模型失败: {exc}") from exc

        if resp.status_code >= 400:
            raise AIProviderError(f"模型返回 {resp.status_code}: {resp.text[:200]}")

        try:
            content = resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise AIProviderError(f"响应结构不符合 OpenAI 规范: {exc}") from exc

        data = self._parse_json(content)
        summary = truncate(str(data.get("summary") or ""))
        if not summary:
            raise AIProviderError("模型没有返回摘要")

        return AIResult(
            summary=summary,
            category=normalize_category(data.get("category")),
            status="ok",
            provider=self.name,
        )

    @staticmethod
    def _parse_json(content: str) -> dict:
        """模型常见会包 ```json 或加前后废话，这里做一次宽容解析。"""
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            match = _JSON_BLOCK.search(text)
            if not match:
                raise AIProviderError("模型输出不是合法 JSON") from None
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise AIProviderError("模型输出不是合法 JSON") from exc
        if not isinstance(parsed, dict):
            raise AIProviderError("模型输出不是 JSON 对象")
        return parsed
