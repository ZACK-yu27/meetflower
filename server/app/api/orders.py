"""订单路由：1.9 详情 / 1.10 列表（读取时惰性推进状态）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import OrderListOut, OrderOut
from ..services import order as order_service

router = APIRouter(tags=["orders"])


@router.get("/orders", response_model=OrderListOut)
def list_orders(db: Session = Depends(get_db)):
    return order_service.list_orders(db)


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    return order_service.get_order(db, order_id)
