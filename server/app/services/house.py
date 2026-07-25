"""花房服务：压花收藏（唯一键 upsert）+ 库存查询（含 quantity=0 灰态项，PRD F5）。"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai_gateway import flower_image_url
from ..models import HouseItem
from ..schemas import HouseItemOut, HouseOut, PressOut
from . import DomainError
from .garden import get_plant


def press_flower(session: Session, garden_id: int, plant_id: int) -> PressOut:
    plant = get_plant(session, garden_id, plant_id)
    if plant.pressed:
        raise DomainError(409, "这朵花已经压花收藏过了")
    if plant.stage != "bloom":
        raise DomainError(409, "花朵尚未盛放，不能压花收藏")

    item = session.scalar(
        select(HouseItem).where(
            HouseItem.garden_id == garden_id,
            HouseItem.species == plant.species,
            HouseItem.color == plant.main_color,
        )
    )
    if item is None:
        item = HouseItem(
            garden_id=garden_id,
            species=plant.species,
            color=plant.main_color,
            quantity=0,
            flower_image=flower_image_url(plant.species, plant.main_color),
        )
        session.add(item)
    item.quantity += 1

    plant.pressed = True
    plant.pressed_at = datetime.now()
    session.commit()
    session.refresh(item)

    return PressOut(item_id=item.id, species=item.species, color=item.color, quantity=item.quantity)


def list_items(session: Session, garden_id: int) -> HouseOut:
    """含 quantity=0 的灰态项，按 quantity 降序、再按品种排序。"""
    items = session.scalars(
        select(HouseItem)
        .where(HouseItem.garden_id == garden_id)
        .order_by(HouseItem.quantity.desc(), HouseItem.species, HouseItem.color)
    ).all()
    return HouseOut(
        items=[
            HouseItemOut(
                item_id=i.id,
                species=i.species,
                color=i.color,
                quantity=i.quantity,
                flower_image=i.flower_image,
            )
            for i in items
        ]
    )
