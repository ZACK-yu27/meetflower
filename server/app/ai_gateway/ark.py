"""火山方舟（Volcengine Ark）真实模型客户端：对话(chat completions) 与 图片生成(images/generations)。

契约文档：docs/model_api/seed-2.1-turbo.md（对话）、docs/model_api/seed-2.1-turbo.md
仅在本模块内持有 HTTP 细节；上层（vlm/llm/imagegen）失败时自行降级 mock。
"""

import base64
import json
import re

import httpx

from . import settings


class ArkError(Exception):
    """Ark 调用失败（网络 / 非 200 / 响应结构不符）。"""


def _post(path: str, payload: dict, timeout: float) -> dict:
    if not settings.ARK_API_KEY:
        raise ArkError("ARK_API_KEY 未配置")
    try:
        resp = httpx.post(
            f"{settings.ARK_BASE_URL}{path}",
            headers={
                "Authorization": f"Bearer {settings.ARK_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
    except httpx.HTTPError as e:
        raise ArkError(f"网络错误: {e}") from e
    if resp.status_code != 200:
        raise ArkError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    try:
        return resp.json()
    except ValueError as e:
        raise ArkError("响应非 JSON") from e


def chat_text(messages: list[dict], max_tokens: int = 512, model: str | None = None) -> str:
    """纯文本对话，返回 content 字符串。model 缺省为 settings.ARK_CHAT_MODEL。"""
    data = _post(
        "/chat/completions",
        {
            "model": model or settings.ARK_CHAT_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.8,
            "reasoning_effort": "low",
        },
        settings.ARK_CHAT_TIMEOUT,
    )
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as e:
        raise ArkError(f"响应结构异常: {str(data)[:300]}") from e


def chat_json(messages: list[dict], max_tokens: int = 1024, model: str | None = None) -> dict:
    """JSON 模式对话，返回解析后的 dict（解析失败抛 ArkError）。model 缺省为 settings.ARK_CHAT_MODEL。"""
    data = _post(
        "/chat/completions",
        {
            "model": model or settings.ARK_CHAT_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.6,
            "reasoning_effort": "low",
            "response_format": {"type": "json_object"},
        },
        settings.ARK_CHAT_TIMEOUT,
    )
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ArkError(f"响应结构异常: {str(data)[:300]}") from e
    return _parse_json(text)


def _parse_json(text: str) -> dict:
    """宽松解析：先去代码围栏，再截取第一个 {...} 块。"""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.M)
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except ValueError:
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            result = json.loads(m.group(0))
            if isinstance(result, dict):
                return result
        except ValueError:
            pass
    raise ArkError(f"无法从响应解析 JSON: {text[:200]}")


def image_b64(prompt: str, size: str = "1K") -> bytes:
    """文生图，返回 PNG/JPEG 字节流。"""
    data = _post(
        "/images/generations",
        {
            "model": settings.ARK_IMAGE_MODEL,
            "prompt": prompt,
            "size": size,
            "response_format": "b64_json",
            "watermark": False,
        },
        settings.ARK_IMAGE_TIMEOUT,
    )
    try:
        raw = base64.b64decode(data["data"][0]["b64_json"])
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise ArkError(f"生图响应结构异常: {str(data)[:300]}") from e
    if not raw:
        raise ArkError("生图响应内容为空")
    return raw
