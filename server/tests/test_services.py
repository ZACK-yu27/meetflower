"""服务层测试（API.md v0.2 §6 清单）：

双人各自入账与归属 / 整组扣除 / 已完成 409 / 缺口 409 / 双方齐升级 /
TA 自动照料（时间注入绕过 8s 延迟）/ 复种 / ×0 灰态 / 推荐（意图→组合+赠送）/
赠送不扣库存 / 备注·替代落库 / fast-forward / reset 幂等，以及识花/压花/订单既有语义。
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app import config
from app.ai_gateway.art import GEN_DIR
from app.models import Badge, Bouquet, HouseItem, Order, Plant, PlantCare, ResourceAccount
from app.schemas import BouquetItemIn
from app.services import DomainError
from app.services import bouquet as bouquet_service
from app.services import demo as demo_service
from app.services import garden as garden_service
from app.services import house as house_service
from app.services import order as order_service
from app.services import recognition as recognition_service
from app.services import resource as resource_service

from conftest import make_image_bytes


# ---------- 公共工具 ----------

def _account(session, user: str) -> ResourceAccount:
    return session.get(ResourceAccount, (config.GARDEN_ID, user))


def _fill_resources(session, water=99, sunlight=99, nutrient=99) -> None:
    """给双方账户补足资源（Demo 测试用）。"""
    for user in config.USERS:
        account = _account(session, user)
        account.water, account.sunlight, account.nutrient = water, sunlight, nutrient
    session.commit()


def _ta_auto_care(session, delay_seconds: float = 9) -> None:
    """时间注入绕过 TA_CARE_DELAY_SECONDS：第一次置 ta_ready_since，第二次（+delay）完成 TA 照料。"""
    t0 = datetime.now()
    garden_service.evaluate_ta_care(session, config.GARDEN_ID, now=t0)
    session.commit()
    garden_service.evaluate_ta_care(
        session, config.GARDEN_ID, now=t0 + timedelta(seconds=delay_seconds)
    )
    session.commit()


def _grow_one_stage(session, plant_id: int) -> None:
    """我照料 + TA 自动照料 → 双方齐升级一阶段（资源需已补足）。"""
    garden_service.care(session, config.GARDEN_ID, plant_id)
    _ta_auto_care(session)


def _grow_to_bloom(session, plant_id: int) -> None:
    _fill_resources(session)
    for expected in ("sprout", "seedling", "bud", "bloom"):
        _grow_one_stage(session, plant_id)
        assert session.get(Plant, plant_id).stage == expected


def _plant_recognition(session, seed: int = 1):
    rec = recognition_service.create_recognition(session, make_image_bytes(seed), ".png")
    plant = garden_service.create_plant(session, config.GARDEN_ID, rec.recognition_id)
    return rec, plant


# ---------- 1.1 识花 ----------

def test_recognition_dedupe(session):
    rec = recognition_service.create_recognition(session, make_image_bytes(1), ".png")
    assert rec.recognition_id == 1
    assert rec.image_url.startswith("/static/uploads/")
    assert set(rec.stage_images) == {"seed", "sprout", "seedling", "bud", "bloom"}
    assert 0.85 <= rec.confidence <= 0.97
    assert rec.science_text
    # 同图再识别 → 内容哈希去重，结果一致
    rec_again = recognition_service.create_recognition(session, make_image_bytes(1), ".png")
    assert rec_again.image_url == rec.image_url
    assert (rec_again.species, rec_again.main_color) == (rec.species, rec.main_color)


# ---------- 1.2 种植 / 复种 ----------

def test_plant_from_recognition(session):
    _, plant = _plant_recognition(session, seed=2)
    assert plant.stage == "seed" and plant.stage_name == "种子" and plant.stage_order == 0
    assert (plant.needs.water, plant.needs.sunlight, plant.needs.nutrient) == (2, 0, 0)  # 向日葵示例值
    assert plant.next_stage_name == "萌芽"
    assert plant.me.done is False and plant.ta.done is False
    assert plant.stage_advanced_at is not None


def test_replant_by_species_color(session):
    """复种：品种+颜色无需 recognition_id；品种/颜色不限于图鉴，图鉴外也能种。"""
    plant = garden_service.create_plant(
        session, config.GARDEN_ID, species="玫瑰", main_color="红"
    )
    assert plant.stage == "seed"
    assert plant.species == "玫瑰" and plant.main_color == "红"
    row = session.get(Plant, plant.plant_id)
    assert row.recognition_id is None  # 复种无识花记录

    # 图鉴外品种：成功种植，从种子阶段开始
    plant2 = garden_service.create_plant(
        session, config.GARDEN_ID, species="绣球", main_color="蓝"
    )
    assert plant2.species == "绣球" and plant2.main_color == "蓝"
    assert plant2.stage == "seed"

    # 图鉴内品种的图鉴外颜色：也允许种植
    plant3 = garden_service.create_plant(
        session, config.GARDEN_ID, species="玫瑰", main_color="蓝"
    )
    assert plant3.species == "玫瑰" and plant3.main_color == "蓝"

    with pytest.raises(DomainError) as exc_info:
        garden_service.create_plant(session, config.GARDEN_ID)  # 两种入参都没给
    assert exc_info.value.status_code == 422


# ---------- 1.11 模拟互动：双人各自入账与归属 ----------

def test_interactions_dual_attribution(session):
    # mutual_message：双方各 +1 水
    out = resource_service.apply_interaction(session, config.GARDEN_ID, "mutual_message")
    assert out.resources.me.water == 1 and out.resources.ta.water == 1
    assert out.event.delta == {"water": 1}
    assert out.event.description == "你们今天互相说过话，各获得 1 滴水"

    # share_video：轮流单方 +1 阳光（第一次 me，第二次 ta），文案区分归属
    out1 = resource_service.apply_interaction(session, config.GARDEN_ID, "share_video")
    assert out1.resources.me.sunlight == 1 and out1.resources.ta.sunlight == 0
    assert out1.event.delta == {"sunlight": 1}
    assert out1.event.description == "你分享了一条视频，获得 1 缕阳光"
    out2 = resource_service.apply_interaction(session, config.GARDEN_ID, "share_video")
    assert out2.resources.me.sunlight == 1 and out2.resources.ta.sunlight == 1
    assert out2.event.description == "TA 分享了一条视频，TA 获得 1 缕阳光"

    # streak：双方各 +1 养料
    out3 = resource_service.apply_interaction(session, config.GARDEN_ID, "streak")
    assert out3.resources.me.nutrient == 1 and out3.resources.ta.nutrient == 1
    assert out3.event.delta == {"nutrient": 1}
    assert out3.event.description == "你们已连续互动 3 天，各获得 1 份养料"

    # 事件流水时间倒序
    view = garden_service.get_garden_view(session, config.GARDEN_ID)
    assert [e.type for e in view.events] == [
        "streak", "share_video", "share_video", "mutual_message",
    ]


# ---------- 1.4 照料：整组扣除 / 已完成 409 / 缺口 409 / 双方齐升级 ----------

def test_care_full_bundle_deduction(session):
    """seed 阶段需水 2：整组扣除，账户只扣当前阶段需求。"""
    _, plant = _plant_recognition(session, seed=3)
    me = _account(session, "me")
    me.water, me.sunlight, me.nutrient = 3, 1, 1
    session.commit()

    result = garden_service.care(session, config.GARDEN_ID, plant.plant_id)
    assert (result.applied.water, result.applied.sunlight, result.applied.nutrient) == (2, 0, 0)
    assert result.me_done is True and result.ta_done is False
    assert result.stage == "seed" and result.stage_changed is False
    # 整组扣除：水 3-2=1，其余不动；ta 账户不受影响
    assert (result.resources.me.water, result.resources.me.sunlight, result.resources.me.nutrient) == (1, 1, 1)
    assert (result.resources.ta.water, result.resources.ta.sunlight, result.resources.ta.nutrient) == (0, 0, 0)


def test_care_already_done_409(session):
    _, plant = _plant_recognition(session, seed=4)
    me = _account(session, "me")
    me.water = 9
    session.commit()
    garden_service.care(session, config.GARDEN_ID, plant.plant_id)
    with pytest.raises(DomainError) as exc_info:
        garden_service.care(session, config.GARDEN_ID, plant.plant_id)
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "你已完成本阶段照料，等 TA 完成后花朵就会成长"


def test_care_insufficient_409(session):
    """缺口提示按实际缺口拼接：单资源与多资源两种情况。"""
    _, plant = _plant_recognition(session, seed=5)
    me = _account(session, "me")
    me.water = 1  # seed 需水 2 → 差 1
    session.commit()
    with pytest.raises(DomainError) as exc_info:
        garden_service.care(session, config.GARDEN_ID, plant.plant_id)
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "还差 1 滴水，去聊天获取吧"

    # 推进到 sprout（需水 3 光 1），构造双资源缺口
    _fill_resources(session)
    _grow_one_stage(session, plant.plant_id)
    assert session.get(Plant, plant.plant_id).stage == "sprout"
    me = _account(session, "me")
    me.water, me.sunlight, me.nutrient = 1, 0, 0  # 差 2 水、1 光
    session.commit()
    with pytest.raises(DomainError) as exc_info:
        garden_service.care(session, config.GARDEN_ID, plant.plant_id)
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "还差 2 滴水、1 缕阳光，去聊天获取吧"


def test_both_done_stage_advance(session):
    """双方各完成一次 → 升级：重置本阶段标记、写 stage_advanced_at、置 badge。"""
    _, plant = _plant_recognition(session, seed=6)
    _fill_resources(session)

    garden_service.care(session, config.GARDEN_ID, plant.plant_id)
    _ta_auto_care(session)

    row = session.get(Plant, plant.plant_id)
    assert row.stage == "sprout"
    assert row.stage_advanced_at is not None
    # 旧阶段 care 记录已删除（本阶段双方标记重置）
    cares = session.scalars(select(PlantCare).where(PlantCare.plant_id == plant.plant_id)).all()
    assert cares == []
    # badge 已置，查看花园后清除
    assert session.get(Badge, config.GARDEN_ID).has_update is True
    garden_service.get_garden_view(session, config.GARDEN_ID)
    assert session.get(Badge, config.GARDEN_ID).has_update is False

    # 我单方完成不升级（等我时 stage 不变）
    me = _account(session, "me")
    me.water, me.sunlight = 9, 9
    session.commit()
    result = garden_service.care(session, config.GARDEN_ID, plant.plant_id)
    assert result.stage_changed is False and result.stage == "sprout"


# ---------- §3 TA 自动照料（时间注入，不真等 8s） ----------

def test_ta_auto_care_delay(session):
    _, plant = _plant_recognition(session, seed=7)
    ta = _account(session, "ta")
    ta.water = 5
    session.commit()

    t0 = datetime.now()
    # 达标首次评估：只置 ta_ready_since，不扣资源、不记完成
    garden_service.evaluate_ta_care(session, config.GARDEN_ID, now=t0)
    session.commit()
    row = session.get(Plant, plant.plant_id)
    assert row.ta_ready_since == t0
    assert _account(session, "ta").water == 5

    # 未满 8s：仍不完成
    garden_service.evaluate_ta_care(
        session, config.GARDEN_ID, now=t0 + timedelta(seconds=config.TA_CARE_DELAY_SECONDS - 1)
    )
    session.commit()
    assert _account(session, "ta").water == 5
    assert garden_service.care_done(session, plant.plant_id, "seed", "ta") is False

    # 满 8s：扣 ta 整组资源、记 (ta) care
    garden_service.evaluate_ta_care(
        session, config.GARDEN_ID, now=t0 + timedelta(seconds=config.TA_CARE_DELAY_SECONDS)
    )
    session.commit()
    assert _account(session, "ta").water == 3  # 5 - 2（seed 需求）
    assert garden_service.care_done(session, plant.plant_id, "seed", "ta") is True
    row = session.get(Plant, plant.plant_id)
    assert row.ta_ready_since is None
    assert row.stage == "seed"  # 我未完成，不升级


def test_ta_auto_care_reset_when_insufficient(session):
    """储备不足 → ta_ready_since 重置为空。"""
    _, plant = _plant_recognition(session, seed=8)
    ta = _account(session, "ta")
    ta.water = 2
    session.commit()
    t0 = datetime.now()
    garden_service.evaluate_ta_care(session, config.GARDEN_ID, now=t0)
    session.commit()
    assert session.get(Plant, plant.plant_id).ta_ready_since == t0

    # 资源被消耗到不足（模拟别处扣减）
    ta.water = 1
    session.commit()
    garden_service.evaluate_ta_care(
        session, config.GARDEN_ID, now=t0 + timedelta(seconds=99)
    )
    session.commit()
    assert session.get(Plant, plant.plant_id).ta_ready_since is None
    assert garden_service.care_done(session, plant.plant_id, "seed", "ta") is False


# ---------- 1.5 / 1.6 压花与花房（含 ×0 灰态项） ----------

def test_press_flow_and_gray_zero_item(session):
    """压花 upsert +1；耗尽库存后 quantity=0 行保留（灰态），按数量降序返回。"""
    rec, plant = _plant_recognition(session, seed=9)
    with pytest.raises(DomainError) as exc_info:  # 未盛放 409
        house_service.press_flower(session, config.GARDEN_ID, plant.plant_id)
    assert exc_info.value.status_code == 409
    assert "尚未盛放" in exc_info.value.detail

    _grow_to_bloom(session, plant.plant_id)
    press = house_service.press_flower(session, config.GARDEN_ID, plant.plant_id)
    assert press.quantity == 1
    assert press.species == rec.species and press.color == rec.main_color

    with pytest.raises(DomainError) as exc_info:  # 重复压花 409
        house_service.press_flower(session, config.GARDEN_ID, plant.plant_id)
    assert exc_info.value.status_code == 409
    assert "已经压花收藏" in exc_info.value.detail

    # 同品种复种再压 → 唯一键 upsert 复用一行
    plant2 = garden_service.create_plant(
        session, config.GARDEN_ID, species=rec.species, main_color=rec.main_color
    )
    _grow_to_bloom(session, plant2.plant_id)
    press2 = house_service.press_flower(session, config.GARDEN_ID, plant2.plant_id)
    assert press2.item_id == press.item_id
    assert press2.quantity == 2

    # ×0 灰态：下单耗尽预置向日葵×1 → 行保留、quantity=0
    bouquet = bouquet_service.preview(
        session, config.GARDEN_ID, [BouquetItemIn(species="向日葵", color="黄", count=1)]
    )
    order_service.create_order(session, bouquet.bouquet_id)
    items = house_service.list_items(session, config.GARDEN_ID).items
    sunflower = next(i for i in items if i.species == "向日葵")
    assert sunflower.quantity == 0  # 灰态项仍在列表中
    assert sunflower.flower_image.endswith("_flower.png")
    quantities = [i.quantity for i in items]
    assert quantities == sorted(quantities, reverse=True)  # 按 quantity 降序


# ---------- 1.7 预览：库存校验 / 赠送花材 / 不扣库存 ----------

def test_preview_insufficient_stock_409(session):
    # 预置花材含玫瑰·红×2（启动播种）
    with pytest.raises(DomainError) as exc_info:
        bouquet_service.preview(
            session, config.GARDEN_ID, [BouquetItemIn(species="玫瑰", color="红", count=3)]
        )
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "玫瑰(红) 库存不足：需要 3，现有 2"
    assert session.scalars(select(Bouquet)).all() == []  # 校验失败不落方案
    assert session.scalars(select(Order)).all() == []


def test_preview_with_bonus_and_suggestion(session):
    """bonus 参与合成、items_json 标 gifted:true、预览不扣库存；主色 >2 给轻量建议。"""
    bouquet = bouquet_service.preview(
        session,
        config.GARDEN_ID,
        [
            BouquetItemIn(species="玫瑰", color="红", count=2),
            BouquetItemIn(species="洋甘菊", color="白", count=1),
        ],
        bonus=BouquetItemIn(species="满天星", color="白", count=1),
        occasion="情侣约会",
    )
    assert bouquet.status == "draft"
    assert bouquet.preview_url == f"/static/gen/bouquet_{bouquet.bouquet_id}.png"
    assert (GEN_DIR / f"bouquet_{bouquet.bouquet_id}.png").exists()
    assert bouquet.material_list == [
        {"species": "玫瑰", "color": "红", "count": 2},
        {"species": "洋甘菊", "color": "白", "count": 1},
        {"species": "满天星", "color": "白", "count": 1, "gifted": True},
    ]
    assert bouquet.arrangement_note and "情侣约会" in bouquet.arrangement_note
    assert bouquet.packaging
    # 主色去重后 红+白 两种（≤2）→ 无轻量建议
    assert bouquet.suggestion is None
    # 未扣库存
    house = {i.species: i.quantity for i in house_service.list_items(session, config.GARDEN_ID).items}
    assert house["玫瑰"] == 2 and house["洋甘菊"] == 2


def test_preview_unknown_species_409(session):
    """品种/颜色不限于图鉴：图鉴外花材进入预览后按库存校验，无库存即 409。"""
    with pytest.raises(DomainError) as exc_info:
        bouquet_service.preview(
            session, config.GARDEN_ID, [BouquetItemIn(species="绣球", color="蓝", count=1)]
        )
    assert exc_info.value.status_code == 409  # 库存不足（绣球无库存）


# ---------- 1.13 AI 推荐搭配 ----------

def test_recommend_by_occasion(session):
    """意图 → 库存组合 + 1 种赠送花材；赠送与 items 不重复。"""
    # 预置库存：玫瑰红×2、洋甘菊白×2、向日葵黄×1
    out = bouquet_service.recommend(session, config.GARDEN_ID, "情侣约会")
    assert out.occasion == "情侣约会"
    assert 1 <= len(out.items) <= 2  # 从当前库存选 1–2 种
    stock = {("玫瑰", "红"): 2, ("洋甘菊", "白"): 2, ("向日葵", "黄"): 1}
    for item in out.items:
        key = (item.species, item.color)
        assert key in stock and 1 <= item.count <= stock[key]
    bonus = out.bonus_flower
    assert bonus.gifted is True and bonus.count == 1
    assert (bonus.species, bonus.color) not in {(i.species, i.color) for i in out.items}
    assert out.reason

    with pytest.raises(DomainError) as exc_info:
        bouquet_service.recommend(session, config.GARDEN_ID, "开业大吉")
    assert exc_info.value.status_code == 422


def test_recommend_empty_stock_still_gives_bonus(session):
    """库存为空：items 为空，仍给出赠送花材。"""
    for item in session.scalars(select(HouseItem)).all():
        item.quantity = 0
    session.commit()
    out = bouquet_service.recommend(session, config.GARDEN_ID, "毕业季")
    assert out.items == []
    assert out.bonus_flower.gifted is True
    assert (out.bonus_flower.species, out.bonus_flower.color) == ("向日葵", "黄")


# ---------- 1.8–1.10 订单：赠送不扣库存 / 备注·替代落库 / 重复 409 / 惰性推进 ----------

def test_order_gifted_not_deducted_and_note_persisted(session):
    """赠送花材不校验不扣减；note/accept_substitute 落库并在详情返回。"""
    bouquet = bouquet_service.preview(
        session,
        config.GARDEN_ID,
        [BouquetItemIn(species="向日葵", color="黄", count=1)],
        bonus=BouquetItemIn(species="满天星", color="白", count=1),  # 无库存，赠送不校验
        occasion="毕业季",
    )
    order = order_service.create_order(
        session, bouquet.bouquet_id, note="请下午 5 点后送达", accept_substitute=False
    )
    assert order.status == "accepted"
    assert order.shop_name == "春风花店·抖音本地生活（模拟）"

    house = {i.species: i.quantity for i in house_service.list_items(session, config.GARDEN_ID).items}
    assert house["向日葵"] == 0  # 只扣非赠送项
    assert "满天星" not in house  # 赠送项不产生库存扣减

    detail = order_service.get_order(session, order.order_id)
    assert detail.note == "请下午 5 点后送达"
    assert detail.accept_substitute is False
    assert detail.material_list == [
        {"species": "向日葵", "color": "黄", "count": 1},
        {"species": "满天星", "color": "白", "count": 1, "gifted": True},
    ]
    row = session.get(Order, order.order_id)
    assert row.note == "请下午 5 点后送达" and row.accept_substitute is False

    # 已 sent 重复提交 409
    with pytest.raises(DomainError) as exc_info:
        order_service.create_order(session, bouquet.bouquet_id)
    assert exc_info.value.status_code == 409
    assert "已下单" in exc_info.value.detail


def test_order_defaults_and_lazy_advance(session):
    """accept_substitute 默认 true；订单按创建时长惰性推进。"""
    bouquet = bouquet_service.preview(
        session, config.GARDEN_ID, [BouquetItemIn(species="玫瑰", color="红", count=1)]
    )
    order = order_service.create_order(session, bouquet.bouquet_id)
    detail = order_service.get_order(session, order.order_id)
    assert detail.accept_substitute is True and detail.note is None
    assert detail.status == "accepted" and detail.status_name == "已接单"
    assert [t.reached for t in detail.timeline] == [True, False, False, False]

    order_row = session.get(Order, order.order_id)
    for elapsed, expected, name in ((20, "making", "制作中"), (50, "delivering", "配送中"), (75, "done", "已送达")):
        order_row.created_at = datetime.now() - timedelta(seconds=elapsed)
        session.commit()
        detail = order_service.get_order(session, order.order_id)
        assert detail.status == expected and detail.status_name == name
    assert [t.reached for t in detail.timeline] == [True, True, True, True]

    orders = order_service.list_orders(session)
    assert [o.order_id for o in orders.orders] == [order.order_id]
    assert orders.orders[0].status == "done"


def test_order_not_found_404(session):
    with pytest.raises(DomainError) as exc_info:
        order_service.create_order(session, 999)
    assert exc_info.value.status_code == 404
    with pytest.raises(DomainError) as exc_info:
        order_service.get_order(session, 999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "订单不存在"


# ---------- 1.14 演示快进 ----------

def test_fast_forward(session):
    _, plant = _plant_recognition(session, seed=10)
    out = demo_service.fast_forward(session, config.GARDEN_ID, plant.plant_id)
    assert out.stage == "bloom" and out.stage_name == "盛放"
    row = session.get(Plant, plant.plant_id)
    assert row.stage == "bloom" and row.stage_advanced_at is not None
    assert session.get(Badge, config.GARDEN_ID).has_update is True

    with pytest.raises(DomainError) as exc_info:  # 已盛放 409
        demo_service.fast_forward(session, config.GARDEN_ID, plant.plant_id)
    assert exc_info.value.status_code == 409

    with pytest.raises(DomainError) as exc_info:  # 植株不存在 404
        demo_service.fast_forward(session, config.GARDEN_ID, 999)
    assert exc_info.value.status_code == 404


# ---------- 1.15 演示重置（幂等 + 预置花材） ----------

def test_reset_idempotent(session):
    # 制造脏数据：植株、互动事件、资源变动、压花、花束、订单
    _, plant = _plant_recognition(session, seed=11)
    resource_service.apply_interaction(session, config.GARDEN_ID, "mutual_message")
    _grow_to_bloom(session, plant.plant_id)
    house_service.press_flower(session, config.GARDEN_ID, plant.plant_id)
    bouquet = bouquet_service.preview(
        session, config.GARDEN_ID, [BouquetItemIn(species="向日葵", color="黄", count=1)]
    )
    order_service.create_order(session, bouquet.bouquet_id)

    out = demo_service.reset(session)
    assert out.ok is True
    assert (out.resources.me.water, out.resources.me.sunlight, out.resources.me.nutrient) == (0, 0, 0)
    assert (out.resources.ta.water, out.resources.ta.sunlight, out.resources.ta.nutrient) == (0, 0, 0)
    # 预置花材恢复：玫瑰红×2、洋甘菊白×2、向日葵黄×1
    house = {(i.species, i.color): i.quantity for i in out.house}
    assert house == {("玫瑰", "红"): 2, ("洋甘菊", "白"): 2, ("向日葵", "黄"): 1}

    # 全表清空确认
    for model in (Plant, PlantCare, Order, Bouquet):
        assert session.scalars(select(model)).all() == []
    view = garden_service.get_garden_view(session, config.GARDEN_ID)
    assert view.plants == [] and view.events == []

    # 幂等：再调一次结果一致
    out2 = demo_service.reset(session)
    assert out2.ok is True
    assert {(i.species, i.color): i.quantity for i in out2.house} == house
