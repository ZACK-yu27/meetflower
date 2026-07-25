"""Demo 路由：1.11 模拟互动（P-chat 模拟器）/ 1.14 演示快进 / 1.15 演示重置。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..schemas import (
    FastForwardOut,
    FastForwardRequest,
    InteractionOut,
    InteractionRequest,
    ResetOut,
)
from ..services import demo as demo_service
from ..services import resource as resource_service

router = APIRouter(tags=["demo"])


@router.post("/demo/interactions", response_model=InteractionOut)
def interact(body: InteractionRequest, db: Session = Depends(get_db)):
    return resource_service.apply_interaction(db, config.GARDEN_ID, body.kind)


@router.post("/demo/fast-forward", response_model=FastForwardOut)
def fast_forward(body: FastForwardRequest, db: Session = Depends(get_db)):
    return demo_service.fast_forward(db, config.GARDEN_ID, body.plant_id)


@router.post("/demo/reset", response_model=ResetOut)
def reset(db: Session = Depends(get_db)):
    return demo_service.reset(db)
