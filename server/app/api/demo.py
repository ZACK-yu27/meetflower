"""Demo 路由：1.11 模拟互动（P-chat 模拟器）/ 1.14 演示快进 / 1.15 演示重置（按当前会话花园）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
from ..sessions import resolve_garden_id

router = APIRouter(tags=["demo"])


@router.post("/demo/interactions", response_model=InteractionOut)
def interact(
    body: InteractionRequest,
    garden_id: int = Depends(resolve_garden_id),
    db: Session = Depends(get_db),
):
    return resource_service.apply_interaction(db, garden_id, body.kind)


@router.post("/demo/fast-forward", response_model=FastForwardOut)
def fast_forward(
    body: FastForwardRequest,
    garden_id: int = Depends(resolve_garden_id),
    db: Session = Depends(get_db),
):
    return demo_service.fast_forward(db, garden_id, body.plant_id)


@router.post("/demo/reset", response_model=ResetOut)
def reset(garden_id: int = Depends(resolve_garden_id), db: Session = Depends(get_db)):
    return demo_service.reset(db, garden_id)
