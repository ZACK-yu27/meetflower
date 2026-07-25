"""花园服务：启动播种（双人账户+预置花材）、种植/复种、聚合视图、双人整组照料、升级检查、TA 自动照料。

成长语义（API.md §3）：每阶段双方各自整组扣除需求资源、各记一条 plant_cares；
双方齐 → 升阶段（删除该阶段两条记录、ta_ready_since 置空、写 stage_advanced_at、置 badge）；bloom 终态。
"""

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .. import config
from ..ai_gateway.art import ensure_stage_images, flower_image_url, stage_image_url
from ..ai_gateway.catalog import CATALOG
from ..models import (
    Badge,
    Garden,
    HouseItem,
    Plant,
    PlantCare,
    Recognition,
    ResourceAccount,
    ResourceEvent,
)
from ..schemas import (
    CareOut,
    CareSideMe,
    CareSideTa,
    DualResources,
    EventOut,
    GardenInfo,
    GardenOut,
    PlantOut,
    ResourceBundle,
    SufficientBundle,
)
from . import DomainError

_RESOURCES = ("water", "sunlight", "nutrient")
# 缺口提示文案：资源 -> (单位, 名称)，如「2 滴水」「1 缕阳光」「3 份养料」
_LACK_TEXT = {"water": ("滴", "水"), "sunlight": ("缕", "阳光"), "nutrient": ("份", "养料")}


# ---- 启动播种（幂等：只补缺失行；启动与 1.15 重置共用） ----

def seed_db(session: Session) -> None:
    """播种 garden id=1、双方资源账户（me/ta 归零）、badge、预置花材 PRESTOCK_HOUSE。"""
    if session.get(Garden, config.GARDEN_ID) is None:
        session.add(Garden(id=config.GARDEN_ID, user_a=config.USER_A, user_b=config.USER_B))
    for user in config.USERS:
        if session.get(ResourceAccount, (config.GARDEN_ID, user)) is None:
            session.add(ResourceAccount(garden_id=config.GARDEN_ID, user=user))
    if session.get(Badge, config.GARDEN_ID) is None:
        session.add(Badge(garden_id=config.GARDEN_ID, has_update=False, message=config.BADGE_MESSAGE))
    for item in config.PRESTOCK_HOUSE:
        exists = session.scalar(
            select(HouseItem).where(
                HouseItem.garden_id == config.GARDEN_ID,
                HouseItem.species == item["species"],
                HouseItem.color == item["color"],
            )
        )
        if exists is None:
            session.add(
                HouseItem(
                    garden_id=config.GARDEN_ID,
                    species=item["species"],
                    color=item["color"],
                    quantity=item["quantity"],
                    flower_image=flower_image_url(item["species"], item["color"]),
                )
            )
    session.commit()


# ---- 内部工具 ----

def get_garden(session: Session, garden_id: int) -> Garden:
    garden = session.get(Garden, garden_id)
    if garden is None:
        raise DomainError(404, "花园不存在")
    return garden


def get_account(session: Session, garden_id: int, user: str) -> ResourceAccount:
    account = session.get(ResourceAccount, (garden_id, user))
    if account is None:  # 防御：播种缺失时补一行
        account = ResourceAccount(garden_id=garden_id, user=user)
        session.add(account)
        session.flush()
    return account


def get_plant(session: Session, garden_id: int, plant_id: int) -> Plant:
    plant = session.get(Plant, plant_id)
    if plant is None or plant.garden_id != garden_id:
        raise DomainError(404, "植株不存在")
    return plant


def account_bundle(account: ResourceAccount) -> ResourceBundle:
    return ResourceBundle(water=account.water, sunlight=account.sunlight, nutrient=account.nutrient)


def care_done(session: Session, plant_id: int, stage: str, user: str) -> bool:
    return (
        session.scalar(
            select(PlantCare.id).where(
                PlantCare.plant_id == plant_id, PlantCare.stage == stage, PlantCare.user == user
            )
        )
        is not None
    )


def _sufficient(account: ResourceAccount, spec: dict) -> SufficientBundle:
    """储备是否 ≥ 单项需求（需求为 0 时该项恒 true）。"""
    return SufficientBundle(**{res: getattr(account, res) >= spec[res] for res in _RESOURCES})


def _set_badge(session: Session, garden_id: int) -> None:
    badge = session.get(Badge, garden_id)
    if badge is None:
        badge = Badge(garden_id=garden_id)
        session.add(badge)
    badge.has_update = True
    badge.message = config.BADGE_MESSAGE


def try_advance(session: Session, plant: Plant) -> bool:
    """升级检查：当前阶段双方均完成 → 升阶段（重置标记、写 stage_advanced_at、置 badge）。bloom 终态。"""
    if plant.stage == "bloom":
        return False
    if not (
        care_done(session, plant.id, plant.stage, "me")
        and care_done(session, plant.id, plant.stage, "ta")
    ):
        return False
    session.execute(
        delete(PlantCare).where(PlantCare.plant_id == plant.id, PlantCare.stage == plant.stage)
    )
    order = config.STAGES.index(plant.stage)
    plant.stage = config.STAGES[order + 1]
    plant.ta_ready_since = None
    plant.stage_advanced_at = datetime.now()
    _set_badge(session, plant.garden_id)
    return True


def evaluate_ta_care(session: Session, garden_id: int, now: datetime | None = None) -> None:
    """TA 自动照料惰性评估（garden GET 与 demo/interactions 后调用，API.md §3）。

    对每株非 bloom/pressed 植株：ta 未完成本阶段且储备达标 → ta_ready_since 计时，
    距今 ≥ TA_CARE_DELAY_SECONDS → 扣 ta 整组资源、记 (ta) care、再做升级检查；储备不足则计时清零。
    """
    now = now or datetime.now()
    plants = session.scalars(
        select(Plant).where(
            Plant.garden_id == garden_id, Plant.stage != "bloom", Plant.pressed.is_(False)
        )
    ).all()
    for plant in plants:
        if care_done(session, plant.id, plant.stage, "ta"):
            continue  # TA 已完成本阶段，等我完成
        spec = config.STAGE_SPECS[plant.stage]
        account = get_account(session, garden_id, "ta")
        if all(getattr(account, res) >= spec[res] for res in _RESOURCES):
            if plant.ta_ready_since is None:
                plant.ta_ready_since = now
            elif (now - plant.ta_ready_since).total_seconds() >= config.TA_CARE_DELAY_SECONDS:
                for res in _RESOURCES:
                    setattr(account, res, getattr(account, res) - spec[res])
                session.add(PlantCare(plant_id=plant.id, stage=plant.stage, user="ta"))
                plant.ta_ready_since = None
                session.flush()  # autoflush=False：先落库让 try_advance 的查询可见
                try_advance(session, plant)
        else:
            plant.ta_ready_since = None


def plant_out(session: Session, plant: Plant) -> PlantOut:
    spec = config.STAGE_SPECS[plant.stage]
    order = config.STAGES.index(plant.stage)
    is_bloom = plant.stage == "bloom"
    me_account = get_account(session, plant.garden_id, "me")
    ta_account = get_account(session, plant.garden_id, "ta")
    me_done = care_done(session, plant.id, plant.stage, "me")
    ta_done = care_done(session, plant.id, plant.stage, "ta")
    me_sufficient = _sufficient(me_account, spec)
    return PlantOut(
        plant_id=plant.id,
        species=plant.species,
        main_color=plant.main_color,
        stage=plant.stage,
        stage_name=config.STAGE_NAMES[plant.stage],
        stage_image=stage_image_url(plant.species, plant.main_color, plant.stage),
        stage_order=order,
        is_bloom=is_bloom,
        pressed=plant.pressed,
        needs=ResourceBundle(water=spec["water"], sunlight=spec["sunlight"], nutrient=spec["nutrient"]),
        me=CareSideMe(
            done=me_done,
            sufficient=me_sufficient,
            can_care=(not me_done) and all(me_sufficient.model_dump().values()) and not is_bloom and not plant.pressed,
        ),
        ta=CareSideTa(done=ta_done, sufficient=_sufficient(ta_account, spec)),
        next_stage_name=None if is_bloom else config.STAGE_NAMES[config.STAGES[order + 1]],
        stage_advanced_at=plant.stage_advanced_at,
    )


def event_out(event: ResourceEvent) -> EventOut:
    return EventOut(
        id=event.id,
        type=event.type,
        description=event.description,
        delta=event.delta_json,
        occurred_at=event.occurred_at,
    )


# ---- 1.2 种植 / 复种 ----

def create_plant(
    session: Session,
    garden_id: int,
    recognition_id: int | None = None,
    species: str | None = None,
    main_color: str | None = None,
) -> PlantOut:
    get_garden(session, garden_id)
    secondary_color: str
    if recognition_id is not None:
        recognition = session.get(Recognition, recognition_id)
        if recognition is None:
            raise DomainError(404, "识花记录不存在")
        species = recognition.species
        main_color = recognition.main_color
        secondary_color = recognition.secondary_color
    elif species and main_color:
        entry = CATALOG.get(species)
        ensure_stage_images(species, main_color)  # 视觉资产走 catalog 复用；图鉴外品种由通用画法兜底
        if entry is not None and main_color in entry["colors"]:
            colors = list(entry["colors"].keys())
            secondary_color = colors[(colors.index(main_color) + 1) % len(colors)]
        else:
            secondary_color = main_color  # 图鉴外品种/颜色：辅色与主色相同
    else:
        raise DomainError(422, "请提供 recognition_id 或品种+颜色")

    plant = Plant(
        garden_id=garden_id,
        recognition_id=recognition_id,
        species=species,
        main_color=main_color,
        secondary_color=secondary_color,
        stage="seed",
        stage_advanced_at=datetime.now(),
    )
    session.add(plant)
    session.commit()
    session.refresh(plant)
    return plant_out(session, plant)


# ---- 1.3 花园聚合视图 ----

def get_garden_view(session: Session, garden_id: int) -> GardenOut:
    garden = get_garden(session, garden_id)
    evaluate_ta_care(session, garden_id)  # §3：TA 自动照料评估（内含升级检查）
    plants = list(
        session.scalars(select(Plant).where(Plant.garden_id == garden_id).order_by(Plant.id)).all()
    )
    # 用户查看了花园 → 清除 badge（含本次推进刚置上的）
    badge = session.get(Badge, garden_id)
    if badge is not None:
        badge.has_update = False
    session.commit()

    me = get_account(session, garden_id, "me")
    ta = get_account(session, garden_id, "ta")
    events = list(
        session.scalars(
            select(ResourceEvent)
            .where(ResourceEvent.garden_id == garden_id)
            .order_by(ResourceEvent.occurred_at.desc(), ResourceEvent.id.desc())
            .limit(20)
        ).all()
    )
    return GardenOut(
        garden=GardenInfo(garden_id=garden.id, user_a=garden.user_a, user_b=garden.user_b),
        resources=DualResources(me=account_bundle(me), ta=account_bundle(ta)),
        plants=[plant_out(session, p) for p in plants],
        events=[event_out(e) for e in events],
    )


# ---- 1.4 照料（我：整组扣除 + 记录完成；双方齐 → 升级） ----

def care(session: Session, garden_id: int, plant_id: int) -> CareOut:
    plant = get_plant(session, garden_id, plant_id)
    if plant.pressed:
        raise DomainError(409, "这朵花已压花收藏，无需再照料")
    if plant.stage == "bloom":
        raise DomainError(409, "花朵已盛放，无需再照料")
    if care_done(session, plant.id, plant.stage, "me"):
        raise DomainError(409, "你已完成本阶段照料，等 TA 完成后花朵就会成长")

    spec = config.STAGE_SPECS[plant.stage]
    account = get_account(session, garden_id, "me")
    lacks = [
        (res, spec[res] - getattr(account, res))
        for res in _RESOURCES
        if getattr(account, res) < spec[res]
    ]
    if lacks:
        parts = "、".join(f"{amount} {_LACK_TEXT[res][0]}{_LACK_TEXT[res][1]}" for res, amount in lacks)
        raise DomainError(409, f"还差 {parts}，去聊天获取吧")

    # 单事务：整组扣除 → 记录 (me) care → 双方齐则升级
    for res in _RESOURCES:
        setattr(account, res, getattr(account, res) - spec[res])
    session.add(PlantCare(plant_id=plant.id, stage=plant.stage, user="me"))
    session.flush()  # autoflush=False：先落库让 try_advance 的查询可见
    stage_changed = try_advance(session, plant)
    session.commit()

    ta_account = get_account(session, garden_id, "ta")
    return CareOut(
        applied=ResourceBundle(water=spec["water"], sunlight=spec["sunlight"], nutrient=spec["nutrient"]),
        me_done=care_done(session, plant.id, plant.stage, "me"),
        ta_done=care_done(session, plant.id, plant.stage, "ta"),
        stage=plant.stage,
        stage_changed=stage_changed,
        resources=DualResources(me=account_bundle(account), ta=account_bundle(ta_account)),
    )
