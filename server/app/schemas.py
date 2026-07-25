"""Pydantic 模型：请求/响应结构与 API.md v0.2 §1 示例逐字段对齐。"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---- 通用 ----

class ResourceBundle(BaseModel):
    water: int
    sunlight: int
    nutrient: int


class DualResources(BaseModel):
    me: ResourceBundle
    ta: ResourceBundle


class SufficientBundle(BaseModel):
    water: bool
    sunlight: bool
    nutrient: bool


# ---- 1.1 识花 ----

class RecognitionOut(BaseModel):
    recognition_id: int
    image_url: str
    species: str
    main_color: str
    secondary_color: str
    confidence: float
    science_text: str
    flower_image: str
    stage_images: dict[str, str]


# ---- 1.2 种植 / 复种、1.3 花园聚合 ----

class PlantCreateRequest(BaseModel):
    recognition_id: int | None = None  # 识花种植
    species: str | None = None         # 复种（与 main_color 一起）
    main_color: str | None = None


class CareSideMe(BaseModel):
    done: bool
    sufficient: SufficientBundle
    can_care: bool


class CareSideTa(BaseModel):
    done: bool
    sufficient: SufficientBundle


class PlantOut(BaseModel):
    plant_id: int
    species: str
    main_color: str
    stage: str
    stage_name: str
    stage_image: str
    stage_order: int
    is_bloom: bool
    pressed: bool
    needs: ResourceBundle
    me: CareSideMe
    ta: CareSideTa
    next_stage_name: str | None
    stage_advanced_at: datetime | None


class GardenInfo(BaseModel):
    garden_id: int
    user_a: str
    user_b: str


class EventOut(BaseModel):
    id: int
    type: str
    description: str
    delta: dict[str, int]
    occurred_at: datetime


class GardenOut(BaseModel):
    garden: GardenInfo
    resources: DualResources
    plants: list[PlantOut]
    events: list[EventOut]


# ---- 1.4 照料 ----

class CareOut(BaseModel):
    applied: ResourceBundle
    me_done: bool
    ta_done: bool
    stage: str
    stage_changed: bool
    resources: DualResources


# ---- 1.5 压花 / 1.6 花房 ----

class PressOut(BaseModel):
    item_id: int
    species: str
    color: str
    quantity: int


class HouseItemOut(BaseModel):
    item_id: int
    species: str
    color: str
    quantity: int
    flower_image: str


class HouseOut(BaseModel):
    items: list[HouseItemOut]


# ---- 1.7 花束预览 / 1.8 下单 / 1.13 推荐 ----

class BouquetItemIn(BaseModel):
    species: str
    color: str
    count: int = Field(ge=1)


class MaterialItem(BaseModel):
    """响应中的花材项；gifted 仅赠送项为 true（普通项序列化时省略该键）。"""

    species: str
    color: str
    count: int
    gifted: bool | None = None


class BouquetPreviewRequest(BaseModel):
    items: list[BouquetItemIn] = Field(min_length=1)
    bonus: BouquetItemIn | None = None
    occasion: str | None = None


class BouquetOut(BaseModel):
    bouquet_id: int
    preview_url: str | None  # ark 模式异步生成，未就绪时为 null（轮询 GET /bouquets/{id}）
    material_list: list[dict[str, Any]]  # 普通项 {species,color,count}，赠送项另含 gifted:true
    arrangement_note: str | None
    packaging: str | None
    suggestion: str | None
    status: str


class OrderCreateRequest(BaseModel):
    note: str | None = None
    accept_substitute: bool = True


class OrderCreatedOut(BaseModel):
    order_id: int
    bouquet_id: int
    status: str
    shop_name: str


class RecommendRequest(BaseModel):
    occasion: Literal["情侣约会", "毕业季", "生日祝福", "探望问候", "日常惊喜"]


class RecommendOut(BaseModel):
    occasion: str
    items: list[BouquetItemIn]
    bonus_flower: MaterialItem
    reason: str


# ---- 1.9 / 1.10 订单 ----

class TimelineItem(BaseModel):
    status: str
    name: str
    reached: bool


class OrderOut(BaseModel):
    order_id: int
    status: str
    status_name: str
    shop_name: str
    created_at: datetime
    preview_url: str | None  # 下单时预览图可能仍在异步生成
    material_list: list[dict[str, Any]]  # 含 gifted 标记
    note: str | None
    accept_substitute: bool
    timeline: list[TimelineItem]


class OrderListOut(BaseModel):
    orders: list[OrderOut]


# ---- 1.11 模拟互动 ----

class InteractionRequest(BaseModel):
    kind: Literal["mutual_message", "share_video", "streak"]


class InteractionOut(BaseModel):
    resources: DualResources
    event: EventOut


# ---- 1.12 badge ----

class BadgeOut(BaseModel):
    has_update: bool
    message: str


# ---- 1.14 演示快进 / 1.15 演示重置 ----

class FastForwardRequest(BaseModel):
    plant_id: int


class FastForwardOut(BaseModel):
    plant_id: int
    stage: str
    stage_name: str


class ResetOut(BaseModel):
    ok: bool
    resources: DualResources
    house: list[HouseItemOut]
