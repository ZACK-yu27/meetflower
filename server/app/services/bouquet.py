"""花束服务：AI 推荐搭配（1.13）+ 预览（1.7：库存快照校验、赠送花材不校验、搭配说明/包装建议/轻量建议）。

预览首响优化（ark 模式）：搭配说明与包装建议并行调用（无依赖）；预览图异步生成回写，
首响 preview_url 为 null，前端经 GET /api/v1/bouquets/{id} 轮询。mock 模式全部同步。
"""

import logging
from concurrent.futures import ThreadPoolExecutor

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import config
from ..ai_gateway import BouquetItem, generate_bouquet
from ..ai_gateway import settings as ai_settings
from ..ai_gateway.llm import arrangement_note, packaging_suggestion, recommend_bouquet
from ..db import SessionLocal
from ..image_store import image_url, save_image
from ..models import Bouquet, HouseItem
from ..schemas import (
    BouquetItemIn,
    BouquetOut,
    MaterialItem,
    RecommendOut,
)
from . import DomainError

logger = logging.getLogger("services.bouquet")

# 组合主色超过该数量时给轻量建议（API.md 1.7）
_SUGGESTION_TEXT = "主色较多，可减少一种主色，花束会更柔和"


def _stock(session: Session, garden_id: int, species: str, color: str) -> HouseItem | None:
    return session.scalar(
        select(HouseItem).where(
            HouseItem.garden_id == garden_id,
            HouseItem.species == species,
            HouseItem.color == color,
        )
    )


def _aggregate(items: list[BouquetItemIn], gifted: bool) -> list[dict]:
    """按品种+颜色汇总（保持首次出现顺序）；赠送项标 gifted: true。品种/颜色不限于图鉴。"""
    aggregated: dict[tuple[str, str], int] = {}
    for it in items:
        key = (it.species, it.color)
        aggregated[key] = aggregated.get(key, 0) + it.count
    material = [{"species": s, "color": c, "count": n} for (s, c), n in aggregated.items()]
    if gifted:
        for m in material:
            m["gifted"] = True
    return material


def check_stock(session: Session, garden_id: int, items: list[dict]) -> None:
    """库存校验（调用方负责跳过 gifted 项），不足抛 409（消息格式见 API.md 1.7）。"""
    for it in items:
        item = _stock(session, garden_id, it["species"], it["color"])
        have = item.quantity if item is not None else 0
        if it["count"] > have:
            raise DomainError(
                409, f"{it['species']}({it['color']}) 库存不足：需要 {it['count']}，现有 {have}"
            )


def _texts_parallel(material: list[dict], occasion: str | None) -> tuple[str, str]:
    """搭配说明 + 包装建议并行调用（无依赖；ark 模式省约一半文案时间）。"""
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_note = ex.submit(arrangement_note, material, occasion)
        f_pack = ex.submit(packaging_suggestion, material, occasion)
        return f_note.result(), f_pack.result()


def _gen_items(material: list[dict]) -> list[BouquetItem]:
    return [BouquetItem(species=m["species"], color=m["color"], count=m["count"]) for m in material]


def fill_preview_image(bouquet_id: int, material: list[dict]) -> None:
    """后台任务：生成花束预览图入库并回写（ark 失败内部自动降级 Pillow，不抛异常）。"""
    db = SessionLocal()
    try:
        bouquet = db.get(Bouquet, bouquet_id)
        if bouquet is None or bouquet.preview_url:
            return
        data, mime = generate_bouquet(_gen_items(material), out_stem=f"bouquet_{bouquet_id}")
        img = save_image(db, f"bouquet_{bouquet_id}", data, mime)
        bouquet.preview_url = image_url(img.id)
        db.commit()
    except Exception:  # noqa: BLE001 — 后台任务静默兜底
        logger.exception("花束预览图异步生成失败 bouquet_id=%s", bouquet_id)
    finally:
        db.close()


def bouquet_out(bouquet: Bouquet) -> BouquetOut:
    colors = {m["color"] for m in bouquet.items_json}
    suggestion = _SUGGESTION_TEXT if len(colors) > 2 else None
    return BouquetOut(
        bouquet_id=bouquet.id,
        preview_url=bouquet.preview_url,
        material_list=list(bouquet.items_json),
        arrangement_note=bouquet.arrangement_note,
        packaging=bouquet.packaging,
        suggestion=suggestion,
        status=bouquet.status,
    )


def get_bouquet(session: Session, bouquet_id: int) -> BouquetOut:
    """轮询用：按 id 取花束方案（预览图补齐后 preview_url 非空）。"""
    bouquet = session.get(Bouquet, bouquet_id)
    if bouquet is None:
        raise DomainError(404, "花束方案不存在")
    return bouquet_out(bouquet)


def preview(
    session: Session,
    garden_id: int,
    items: list[BouquetItemIn],
    bonus: BouquetItemIn | None = None,
    occasion: str | None = None,
    background: BackgroundTasks | None = None,
) -> BouquetOut:
    normal = _aggregate(items, gifted=False)
    gifted = _aggregate([bonus], gifted=True) if bonus is not None else []
    material = normal + gifted

    check_stock(session, garden_id, normal)  # 快照校验不扣减；bonus 不校验

    bouquet = Bouquet(garden_id=garden_id, items_json=material, occasion=occasion, status="draft")
    session.add(bouquet)
    session.flush()  # 先拿 id 作为图片名

    # mock 同步生图（Pillow 瞬时）；ark 首响先返回、预览图异步补齐
    async_image = ai_settings.AI_PROVIDER == "ark" and background is not None
    if not async_image:
        data, mime = generate_bouquet(_gen_items(material), out_stem=f"bouquet_{bouquet.id}")
        img = save_image(session, f"bouquet_{bouquet.id}", data, mime)
        bouquet.preview_url = image_url(img.id)

    bouquet.arrangement_note, bouquet.packaging = _texts_parallel(material, occasion)
    session.commit()
    session.refresh(bouquet)

    if async_image:
        background.add_task(fill_preview_image, bouquet.id, material)

    return bouquet_out(bouquet)


def recommend(session: Session, garden_id: int, occasion: str) -> RecommendOut:
    """AI 推荐搭配（1.13）：mock LLM 按意图从当前库存可用花材选 1–2 种 + 1 种赠送花材。"""
    if occasion not in config.OCCASIONS:
        raise DomainError(422, f"未知的送花意图：{occasion}")
    available = [
        {"species": i.species, "color": i.color, "quantity": i.quantity}
        for i in session.scalars(
            select(HouseItem)
            .where(HouseItem.garden_id == garden_id, HouseItem.quantity > 0)
            .order_by(HouseItem.quantity.desc(), HouseItem.species, HouseItem.color)
        ).all()
    ]
    result = recommend_bouquet(occasion, available)
    return RecommendOut(
        occasion=occasion,
        items=[BouquetItemIn(**i) for i in result["items"]],
        bonus_flower=MaterialItem(**result["bonus_flower"]),
        reason=result["reason"],
    )
