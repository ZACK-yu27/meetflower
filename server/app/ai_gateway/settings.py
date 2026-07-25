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
ARK_CHAT_MODEL = os.environ.get("ARK_CHAT_MODEL", "doubao-seed-2-1-turbo-260628")
# VLM 识花专用模型（可用更快的端点，如开通 lite 后设 ARK_VLM_MODEL=doubao-seed-2-0-lite-xxx）
ARK_VLM_MODEL = os.environ.get("ARK_VLM_MODEL") or ARK_CHAT_MODEL
ARK_IMAGE_MODEL = os.environ.get("ARK_IMAGE_MODEL", "doubao-seedream-5-0-pro-260628")
ARK_CHAT_TIMEOUT = float(os.environ.get("ARK_CHAT_TIMEOUT", "90"))
ARK_IMAGE_TIMEOUT = float(os.environ.get("ARK_IMAGE_TIMEOUT", "120"))

# ark = 真实模型（每次调用失败自动降级 mock）；mock = 全部本地 mock（测试/离线）
AI_PROVIDER = os.environ.get("AI_PROVIDER") or ("ark" if ARK_API_KEY else "mock")
