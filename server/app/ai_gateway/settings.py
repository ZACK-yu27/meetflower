"""AI 提供方配置：火山方舟（真实模型）/ mock 切换与 Ark 连接参数。

独立于 app.config（避免 app.config → ai_gateway.catalog → ai_gateway → app.config 循环导入）。
优先级：环境变量 > server/.env 文件 > 默认值。未配置 ARK_API_KEY 时自动回落 mock。
"""

import os
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def _load_dotenv() -> None:
    if not _ENV_PATH.exists():
        return
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

ARK_API_KEY = os.environ.get("ARK_API_KEY", "")
ARK_BASE_URL = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
ARK_CHAT_MODEL = os.environ.get("ARK_CHAT_MODEL", "doubao-seed-2-0-lite-260215")
# VLM 识花专用模型（缺省跟随 chat；如需与科普文案分开可单独设 ARK_VLM_MODEL）
ARK_VLM_MODEL = os.environ.get("ARK_VLM_MODEL") or ARK_CHAT_MODEL
ARK_IMAGE_MODEL = os.environ.get("ARK_IMAGE_MODEL", "doubao-seedream-5-0-260128")
ARK_CHAT_TIMEOUT = float(os.environ.get("ARK_CHAT_TIMEOUT", "90"))
ARK_IMAGE_TIMEOUT = float(os.environ.get("ARK_IMAGE_TIMEOUT", "120"))

# ark = 真实模型（每次调用失败自动降级 mock）；mock = 全部本地 mock（测试/离线）
AI_PROVIDER = os.environ.get("AI_PROVIDER") or ("ark" if ARK_API_KEY else "mock")

# 静态资源公网前缀：本地开发为空（/static/... 相对路径，走 vite 代理）；
# 生产部署（前端与 API 不同域，如 Pages + Render）时设为后端公网地址，
# 例如 https://flowers-api-xxxx.onrender.com —— 否则前端会把图片 URL 解析到前端域名下 404
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")


def public_url(path: str) -> str:
    """把 /static/... 相对路径转为可跨域访问的 URL（未配置 PUBLIC_BASE_URL 时原样返回）。"""
    return f"{PUBLIC_BASE_URL}{path}" if PUBLIC_BASE_URL else path
