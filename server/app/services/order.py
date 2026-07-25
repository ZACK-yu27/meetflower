"""订单服务：发送花店（单事务扣库存[跳过赠送项] + 方案置 sent + 创建订单落备注/替代）+ 惰性状态推进。"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import config
from ..models import Bouquet, Order
from ..schemas import (
    OrderCreatedOut,
    OrderListOut,
    OrderOut,
    TimelineItem,
)
from . import DomainError
from .bouquet import _stock, check_stock


def create_order(
    session: Session,
    bouquet_id: int,
    note: str | None = None,
    accept_substitute: bool = True,
) -> OrderCreatedOut:
    bouquet = session.get(Bouquet, bouquet_id)
    if bouquet is None:
        raise DomainError(404, "花束方案不存在")
    if bouquet.status == "sent":
        raise DomainError(409, "该花束方案已下单，请勿重复提交")

    material = list(bouquet.items_json)
    chargeable = [m for m in material if not m.get("gifted")]  # 赠送花材不校验、不扣减
    check_stock(session, config.GARDEN_ID, chargeable)

    # 单事务：扣库存 + bouquet→sent + 创建订单（落 note/accept_substitute）
    for it in chargeable:
        item = _stock(session, config.GARDEN_ID, it["species"], it["color"])
        item.quantity -= it["count"]
    bouquet.status = "sent"
    now = datetime.now()
    order = Order(
        bouquet_id=bouquet.id,
        shop_name=config.SHOP_NAME,
        status="accepted",
        note=note,
        accept_substitute=accept_substitute,
        created_at=now,
        status_updated_at=now,
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    return OrderCreatedOut(order_id=order.id, bouquet_id=bouquet.id, status=order.status, shop_name=order.shop_name)


def advance_order(order: Order, now: datetime | None = None) -> None:
    """按创建至今时长惰性推进状态（0–15s accepted / 15–40s making / 40–70s delivering / ≥70s done）。"""
    now = now or datetime.now()
    elapsed = (now - order.created_at).total_seconds()
    target = config.ORDER_FLOW[0][0]
    for status, threshold in config.ORDER_FLOW:
        if elapsed >= threshold:
            target = status
    if target != order.status:
        order.status = target
        order.status_updated_at = now


def order_out(order: Order) -> OrderOut:
    statuses = [s for s, _ in config.ORDER_FLOW]
    current = statuses.index(order.status)
    return OrderOut(
        order_id=order.id,
        status=order.status,
        status_name=config.ORDER_STATUS_NAMES[order.status],
        shop_name=order.shop_name,
        created_at=order.created_at,
        preview_url=order.bouquet.preview_url,
        material_list=list(order.bouquet.items_json),
        note=order.note,
        accept_substitute=order.accept_substitute,
        timeline=[
            TimelineItem(status=s, name=n, reached=(i <= current))
            for i, (s, n) in enumerate(config.ORDER_TIMELINE_NAMES)
        ],
    )


def get_order(session: Session, order_id: int) -> OrderOut:
    order = session.get(Order, order_id)
    if order is None:
        raise DomainError(404, "订单不存在")
    advance_order(order)
    session.commit()
    return order_out(order)


def list_orders(session: Session) -> OrderListOut:
    orders = list(session.scalars(select(Order).order_by(Order.created_at.desc(), Order.id.desc())).all())
    for order in orders:
        advance_order(order)
    session.commit()
    return OrderListOut(orders=[order_out(o) for o in orders])
