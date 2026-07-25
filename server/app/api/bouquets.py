"""花束路由：1.7 预览 / 1.8 发送花店 / 1.13 AI 推荐搭配 / GET 轮询（预览图异步补齐）。"""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..schemas import (
    BouquetOut,
    BouquetPreviewRequest,
    OrderCreateRequest,
    OrderCreatedOut,
    RecommendOut,
    RecommendRequest,
)
from ..services import bouquet as bouquet_service
from ..services import order as order_service

router = APIRouter(tags=["bouquets"])


@router.post("/bouquets/preview", response_model=BouquetOut)
def preview(body: BouquetPreviewRequest, background: BackgroundTasks, db: Session = Depends(get_db)):
    return bouquet_service.preview(
        db, config.GARDEN_ID, body.items, bonus=body.bonus, occasion=body.occasion,
        background=background,
    )


@router.get("/bouquets/{bouquet_id}", response_model=BouquetOut)
def read_bouquet(bouquet_id: int, db: Session = Depends(get_db)):
    return bouquet_service.get_bouquet(db, bouquet_id)


@router.post("/bouquets/recommend", response_model=RecommendOut)
def recommend(body: RecommendRequest, db: Session = Depends(get_db)):
    return bouquet_service.recommend(db, config.GARDEN_ID, body.occasion)


@router.post("/bouquets/{bouquet_id}/orders", response_model=OrderCreatedOut)
def send_to_shop(bouquet_id: int, body: OrderCreateRequest, db: Session = Depends(get_db)):
    return order_service.create_order(
        db, bouquet_id, note=body.note, accept_substitute=body.accept_substitute
    )
