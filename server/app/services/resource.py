"""资源服务：模拟互动双人入账（share_video 轮流单方）+ 来源事件流水（API.md 1.11）。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import config
from ..models import ResourceEvent
from ..schemas import DualResources, InteractionOut
from . import DomainError
from .garden import account_bundle, evaluate_ta_care, event_out, get_account


def apply_interaction(session: Session, garden_id: int, kind: str) -> InteractionOut:
    spec = config.INTERACTION_EVENTS.get(kind)
    if spec is None:
        raise DomainError(422, f"未知的互动类型：{kind}")

    me = get_account(session, garden_id, "me")
    ta = get_account(session, garden_id, "ta")
    delta = spec["delta"]

    if spec["target"] == "both":
        for account in (me, ta):
            for res, n in delta.items():
                setattr(account, res, getattr(account, res) + n)
        description = spec["description"]
    else:  # alternate：轮流 me/ta 单方入账（按该 kind 既有事件数奇偶）
        count = session.scalar(
            select(func.count(ResourceEvent.id)).where(
                ResourceEvent.garden_id == garden_id, ResourceEvent.type == kind
            )
        ) or 0
        receiver = "me" if count % 2 == 0 else "ta"
        account = me if receiver == "me" else ta
        for res, n in delta.items():
            setattr(account, res, getattr(account, res) + n)
        description = spec["descriptions"][receiver]

    event = ResourceEvent(
        garden_id=garden_id,
        type=kind,
        description=description,
        delta_json=dict(delta),
    )
    session.add(event)
    evaluate_ta_care(session, garden_id)  # §3：互动后惰性评估 TA 自动照料
    session.commit()
    session.refresh(event)

    return InteractionOut(
        resources=DualResources(me=account_bundle(me), ta=account_bundle(ta)),
        event=event_out(event),
    )
