"""1.12 花园新变化提示：GET /api/v1/badge（查看花园 1.3 后清除）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..models import Badge
from ..schemas import BadgeOut

router = APIRouter(tags=["badge"])


@router.get("/badge", response_model=BadgeOut)
def get_badge(db: Session = Depends(get_db)):
    badge = db.get(Badge, config.GARDEN_ID)
    return BadgeOut(
        has_update=badge.has_update if badge is not None else False,
        message=config.BADGE_MESSAGE,
    )
