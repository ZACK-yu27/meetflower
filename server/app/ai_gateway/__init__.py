"""ai_gateway：mock AI 能力包（VLM 识花 / LLM 科普 / Pillow 绘图 / 生图合成）。

backend-core 只按 API.md §4 契约 import 本包，不修改实现。
"""

from .vlm import identify_flower, identify_resemble, VlmResult
from .llm import flower_profile, FlowerProfile, StageSpec
from .imagegen import generate_bouquet, BouquetItem
from .art import ensure_stage_images, stage_image_url, flower_image_url

__all__ = [
    "identify_flower",
    "identify_resemble",
    "VlmResult",
    "flower_profile",
    "FlowerProfile",
    "StageSpec",
    "generate_bouquet",
    "BouquetItem",
    "ensure_stage_images",
    "stage_image_url",
    "flower_image_url",
]
