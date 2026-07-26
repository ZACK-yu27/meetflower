"""floristry 规则库常驻断言：选品/配比/赠送/色彩/构图/文案模板/生图提示词。

规则文档 docs/floristry_rules.md；实现 server/app/ai_gateway/floristry.py。
"""

from app.ai_gateway import floristry
from app.ai_gateway.imagegen import BouquetItem


def _stock(*rows: tuple[str, str, int]) -> list[dict]:
    return [{"species": s, "color": c, "quantity": q} for s, c, q in rows]


# ---------- 选品（§一-1） ----------

def test_select_items_main_hits_occasion_preference():
    """情侣约会 + 库存有红玫瑰 → 主花必须是玫瑰·红（品种+色系双命中）。"""
    items, bonus = floristry.select_items(
        "情侣约会", _stock(("洋甘菊", "白", 9), ("玫瑰", "红", 2), ("向日葵", "黄", 5))
    )
    assert (items[0]["species"], items[0]["color"]) == ("玫瑰", "红")


def test_select_items_recipe_counts():
    """朵数为配方固定（主 3 / 辅 1，约 7:3），与库存使用次数无关；主辅不同品种色。"""
    available = _stock(("玫瑰", "红", 1), ("洋甘菊", "白", 1))  # 库存仅 1 次也不影响朵数
    items, _ = floristry.select_items("情侣约会", available)
    assert 1 <= len(items) <= 2
    assert items[0]["count"] == 3
    if len(items) == 2:
        assert items[1]["count"] == 1
    assert len({(i["species"], i["color"]) for i in items}) == len(items)


def test_select_items_sub_must_be_harmonious():
    """辅花必须与主花色彩协调：红玫瑰主花不应配向日葵黄以外的冲突冷色。"""
    items, _ = floristry.select_items(
        "情侣约会", _stock(("玫瑰", "红", 3), ("绣球", "蓝", 9))
    )
    # 红（暖红）与蓝（冷色）非邻近 → 只能单主花
    assert len(items) == 1


def test_select_items_empty_stock():
    """库存为空：items 空，但仍给出赠送花材。"""
    items, bonus = floristry.select_items("生日祝福", [])
    assert items == []
    assert bonus["gifted"] is True


def test_bonus_default_babysbreath_not_duplicated():
    """赠送花材默认满天星·白；若 items 已含满天星·白则换候选；永不为 items 重复项。"""
    _, bonus = floristry.select_items("情侣约会", _stock(("玫瑰", "红", 2)))
    assert (bonus["species"], bonus["color"]) == ("满天星", "白")
    assert bonus["gifted"] is True and bonus["count"] == 1

    items, bonus2 = floristry.select_items(
        "日常惊喜", _stock(("满天星", "白", 5))
    )
    taken = {(i["species"], i["color"]) for i in items}
    assert (bonus2["species"], bonus2["color"]) not in taken


# ---------- 色彩规则（§一-2） ----------

def test_colors_harmonious():
    assert floristry.colors_harmonious("红", "粉")      # 同色系
    assert floristry.colors_harmonious("红", "白")      # 中性提亮百搭
    assert floristry.colors_harmonious("红", "黄")      # 邻近色系
    assert not floristry.colors_harmonious("红", "蓝")  # 暖红 × 冷色
    assert floristry.colors_harmonious("红色", "粉")    # 色名归一化


# ---------- 构图与包装（§二-1） ----------

def _items(*rows: tuple[str, str, int, bool]) -> list[BouquetItem]:
    return [BouquetItem(species=s, color=c, count=n, gifted=g) for s, c, n, g in rows]


def test_composition_recipes():
    one = _items(("玫瑰", "红", 3, False))
    two = _items(("玫瑰", "红", 3, False), ("洋甘菊", "白", 1, False))
    dotted = _items(("玫瑰", "红", 3, False), ("满天星", "白", 1, True))
    assert floristry.composition(one)[0] == "圆润半球形"
    assert floristry.composition(two)[0] == "前低后高的圆三角"
    assert floristry.composition(dotted)[0] == "自然扇形三角"  # 赠送花材算点缀


def test_main_item_excludes_gifted():
    items = _items(("玫瑰", "红", 2, False), ("满天星", "白", 9, True))
    main = floristry.main_item(items)
    assert (main.species, main.color) == ("玫瑰", "红")


def test_packaging_for_known_and_unknown_color():
    paper, ribbon = floristry.packaging_for("红")
    assert paper and ribbon
    assert floristry.packaging_for("镭射银") == ("米白", "浅棕")  # 未收录回落中性


# ---------- 文案模板（§二-3） ----------

def test_reason_template_length_and_content():
    available = _stock(("玫瑰", "红", 2), ("洋甘菊", "白", 2))
    items, bonus = floristry.select_items("情侣约会", available)
    reason = floristry.reason_template(items, bonus, "情侣约会")
    assert 10 <= len(reason) <= 45
    assert "玫瑰" in reason and "满天星" in reason and "情侣约会" in reason


def test_note_and_packaging_template_length():
    items = [
        {"species": "玫瑰", "color": "红", "count": 2},
        {"species": "满天星", "color": "白", "count": 1, "gifted": True},
    ]
    note = floristry.note_template(items, "情侣约会")
    assert 10 <= len(note) <= 40
    assert "玫瑰" in note and "情侣约会" in note
    packaging = floristry.packaging_template(items)
    assert 8 <= len(packaging) <= 30


# ---------- 生图提示词（§二-2） ----------

def test_build_image_prompt_elements():
    items = _items(("玫瑰", "红", 2, False), ("满天星", "白", 1, True))
    prompt = floristry.build_image_prompt(items)
    assert "2朵红玫瑰" in prompt            # materials 清单
    assert "1朵白满天星（赠送）" in prompt    # 赠送标注
    assert "自然扇形三角" in prompt           # 编排配方结构词
    assert "花材落位" in prompt
    assert "包装" in prompt and "丝带" in prompt
    assert "禁止" in prompt and "额外花种" in prompt
