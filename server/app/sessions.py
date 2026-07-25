"""匿名 Session → 花园 解析依赖。

前端在 localStorage 保存 UUID，所有请求带 X-Session-Id 头；
首次见到的新会话自动创建并播种一个独立花园（幂等，并发安全）。
未带头的请求（旧客户端 / 测试）回落到启动播种的默认花园 1。
"""

from fastapi import Depends, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import config
from .db import get_db
from .models import Garden, SessionGarden
from .services.garden import seed_garden

DEFAULT_SESSION = "default"


def resolve_garden_id(request: Request, db: Session = Depends(get_db)) -> int:
    sid = (request.headers.get("X-Session-Id") or "").strip() or DEFAULT_SESSION
    row = db.get(SessionGarden, sid)
    if row is not None:
        return row.garden_id
    if sid == DEFAULT_SESSION:
        return config.GARDEN_ID  # 启动时已播种
    try:
        garden = Garden(user_a=config.USER_A, user_b=config.USER_B)
        db.add(garden)
        db.flush()  # 拿自增 id
        seed_garden(db, garden.id)
        db.add(SessionGarden(session_id=sid, garden_id=garden.id))
        db.commit()
        return garden.id
    except IntegrityError:  # 同一会话并发首访：另一请求已创建
        db.rollback()
        row = db.get(SessionGarden, sid)
        if row is None:
            raise
        return row.garden_id
