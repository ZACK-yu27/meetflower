"""ORM 模型：API.md v0.2 §2 全部表（破坏性变更，删库重建）。"""

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, LargeBinary, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Image(Base):
    """图片二进制存储（上传原图 / Seedream 花束图）：重启与重新部署不丢失，经 /api/v1/images/{id} 访问。"""

    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)  # 内容哈希或业务名，get-or-create 去重
    data: Mapped[bytes] = mapped_column(LargeBinary)
    mime: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class SessionGarden(Base):
    """匿名会话 → 花园映射：每位访客（前端 localStorage UUID）一个独立花园。"""

    __tablename__ = "session_gardens"

    session_id: Mapped[str] = mapped_column(primary_key=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class Recognition(Base):
    __tablename__ = "recognitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    garden_id: Mapped[int | None] = mapped_column(ForeignKey("gardens.id"), default=None)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("images.id"), default=None)
    image_path: Mapped[str]  # VLM 临时文件路径（仅识别期间使用，不作为访问 URL）
    species: Mapped[str]
    main_color: Mapped[str]
    secondary_color: Mapped[str]
    confidence: Mapped[float]
    science_text: Mapped[str] = mapped_column(Text)
    stage_images: Mapped[dict] = mapped_column(JSON)  # {stage: /api/v1/art/stage/...}
    flower_image: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class Garden(Base):
    __tablename__ = "gardens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_a: Mapped[str]
    user_b: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    recognition_id: Mapped[int | None] = mapped_column(ForeignKey("recognitions.id"), default=None)  # 复种无
    species: Mapped[str]
    main_color: Mapped[str]
    secondary_color: Mapped[str]
    stage: Mapped[str] = mapped_column(default="seed")
    ta_ready_since: Mapped[datetime | None] = mapped_column(default=None)  # TA 储备达标起的计时点
    stage_advanced_at: Mapped[datetime | None] = mapped_column(default=None)  # 进入当前阶段的时间
    pressed: Mapped[bool] = mapped_column(default=False)
    pressed_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class PlantCare(Base):
    """某株某阶段某用户已完成一次照料（整组扣除后写入；升级时删除该阶段两条）。"""

    __tablename__ = "plant_cares"
    __table_args__ = (UniqueConstraint("plant_id", "stage", "user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"))
    stage: Mapped[str]
    user: Mapped[str]  # me / ta
    completed_at: Mapped[datetime] = mapped_column(default=datetime.now)


class ResourceAccount(Base):
    __tablename__ = "resource_accounts"

    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"), primary_key=True)
    user: Mapped[str] = mapped_column(primary_key=True)  # me / ta
    water: Mapped[int] = mapped_column(default=0)
    sunlight: Mapped[int] = mapped_column(default=0)
    nutrient: Mapped[int] = mapped_column(default=0)


class ResourceEvent(Base):
    __tablename__ = "resource_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    type: Mapped[str]
    description: Mapped[str]
    delta_json: Mapped[dict] = mapped_column(JSON)  # 单资源增量，如 {"water": 1}
    occurred_at: Mapped[datetime] = mapped_column(default=datetime.now)


class HouseItem(Base):
    __tablename__ = "house_items"
    __table_args__ = (UniqueConstraint("garden_id", "species", "color"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"))
    species: Mapped[str]
    color: Mapped[str]
    quantity: Mapped[int] = mapped_column(default=0)  # quantity=0 行保留（灰态项）
    flower_image: Mapped[str]


class Bouquet(Base):
    __tablename__ = "bouquets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    garden_id: Mapped[int | None] = mapped_column(ForeignKey("gardens.id"), default=None)
    items_json: Mapped[list] = mapped_column(JSON)  # [{species, color, count(, gifted: true)}]
    preview_url: Mapped[str | None] = mapped_column(default=None)
    occasion: Mapped[str | None] = mapped_column(default=None)
    arrangement_note: Mapped[str | None] = mapped_column(Text, default=None)
    packaging: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="draft")  # draft / sent
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bouquet_id: Mapped[int] = mapped_column(ForeignKey("bouquets.id"))
    shop_name: Mapped[str]
    status: Mapped[str] = mapped_column(default="accepted")
    note: Mapped[str | None] = mapped_column(Text, default=None)  # 用户备注（可空）
    accept_substitute: Mapped[bool] = mapped_column(default=True)  # 是否接受相似花材替代
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    status_updated_at: Mapped[datetime] = mapped_column(default=datetime.now)

    bouquet: Mapped[Bouquet] = relationship()


class Badge(Base):
    __tablename__ = "badges"

    garden_id: Mapped[int] = mapped_column(ForeignKey("gardens.id"), primary_key=True)
    has_update: Mapped[bool] = mapped_column(default=False)
    message: Mapped[str] = mapped_column(default="")
