"""Demo 服务：演示快进（1.14 直升 bloom）与演示重置（1.15 清空 + 重新播种预置花材）。"""

from datetime import datetime

from sqlalchemy import delete, select
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
    seed_garden,
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


def reset(session: Session, garden_id: int) -> ResetOut:
    """单事务：清空该花园的演示数据 → 重新播种（双方账户归零 + badge + 预置花材）。幂等。"""
    plant_ids = select(Plant.id).where(Plant.garden_id == garden_id)
    session.execute(delete(PlantCare).where(PlantCare.plant_id.in_(plant_ids)))
    session.execute(delete(Plant).where(Plant.garden_id == garden_id))
    bouquet_ids = select(Bouquet.id).where(Bouquet.garden_id == garden_id)
    session.execute(delete(Order).where(Order.bouquet_id.in_(bouquet_ids)))
    session.execute(delete(Bouquet).where(Bouquet.garden_id == garden_id))
    session.execute(delete(ResourceEvent).where(ResourceEvent.garden_id == garden_id))
    session.execute(delete(ResourceAccount).where(ResourceAccount.garden_id == garden_id))
    session.execute(delete(HouseItem).where(HouseItem.garden_id == garden_id))
    session.execute(delete(Badge).where(Badge.garden_id == garden_id))
    session.execute(delete(Recognition).where(Recognition.garden_id == garden_id))
    seed_garden(session, garden_id)
    session.commit()

    me = get_account(session, garden_id, "me")
    ta = get_account(session, garden_id, "ta")
    house = list_items(session, garden_id)
    return ResetOut(
        ok=True,
        resources=DualResources(me=account_bundle(me), ta=account_bundle(ta)),
        house=house.items,
    )
