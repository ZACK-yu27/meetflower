"""Demo 服务：演示快进（1.14 直升 bloom）与演示重置（1.15 清空 + 重新播种预置花材）。"""

from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from .. import config
from ..models import (
    Bouquet,
    HouseItem,
    Order,
    Plant,
    PlantCare,
    Recognition,
    ResourceAccount,
    ResourceEvent,
    Badge,
)
from ..schemas import DualResources, FastForwardOut, ResetOut
from . import DomainError
from .garden import (
    _set_badge,
    account_bundle,
    get_account,
    get_plant,
    seed_db,
)
from .house import list_items


def fast_forward(session: Session, garden_id: int, plant_id: int) -> FastForwardOut:
    """对该植株逐级结算（视为双方均已照料）直升至 bloom，写 stage_advanced_at 并置 badge。"""
    plant = get_plant(session, garden_id, plant_id)
    if plant.pressed:
        raise DomainError(409, "这朵花已压花收藏，无法快进")
    if plant.stage == "bloom":
        raise DomainError(409, "花朵已经盛放，无需快进")

    session.execute(delete(PlantCare).where(PlantCare.plant_id == plant.id))
    plant.stage = "bloom"
    plant.ta_ready_since = None
    plant.stage_advanced_at = datetime.now()
    _set_badge(session, garden_id)
    session.commit()

    return FastForwardOut(plant_id=plant.id, stage=plant.stage, stage_name=config.STAGE_NAMES[plant.stage])


def reset(session: Session) -> ResetOut:
    """单事务：清空全部演示数据 → 重新播种（花园 1 + 双方账户归零 + badge + 预置花材）。幂等。"""
    for model in (
        Order,
        Bouquet,
        PlantCare,
        Plant,
        ResourceEvent,
        ResourceAccount,
        HouseItem,
        Badge,
        Recognition,
    ):
        session.execute(delete(model))
    seed_db(session)  # 重新播种（内部 commit）

    me = get_account(session, config.GARDEN_ID, "me")
    ta = get_account(session, config.GARDEN_ID, "ta")
    house = list_items(session, config.GARDEN_ID)
    return ResetOut(
        ok=True,
        resources=DualResources(me=account_bundle(me), ta=account_bundle(ta)),
        house=house.items,
    )
