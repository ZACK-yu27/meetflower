"""1.6 花房库存：GET /api/v1/flower-house。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..schemas import HouseOut
from ..services import house as house_service

router = APIRouter(tags=["flower-house"])


@router.get("/flower-house", response_model=HouseOut)
def flower_house(db: Session = Depends(get_db)):
    return house_service.list_items(db, config.GARDEN_ID)
