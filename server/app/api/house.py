"""花房库存：1.6 GET /api/v1/flower-house（按当前会话的花园）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import HouseOut
from ..services import house as house_service
from ..sessions import resolve_garden_id

router = APIRouter(tags=["flower-house"])


@router.get("/flower-house", response_model=HouseOut)
def flower_house(garden_id: int = Depends(resolve_garden_id), db: Session = Depends(get_db)):
    return house_service.list_items(db, garden_id)
