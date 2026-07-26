"""花艺规则库（花束搭配 + 预览图编排）：业务规则 docs/floristry_rules.md 的确定性实现。

设计原则：规则由 Python 执行（每次都一致），LLM 只负责文案措辞。
- 推荐：select_items() 确定性选品/配比/赠送花材；reason 由 LLM 撰写（校验长度，不合格回落模板）
- 预览图：build_image_prompt() 按编排配方表生成结构/落位/包装色，组装生图提示词
- 文案：arrangement/packaging 的模板兜底与长度校验规则也在这里，llm.py 调用
"""

from . import catalog

# ---------- 色彩规则（§2） ----------

# 色系分组：同色系优先；邻近色系次之；白/奶油为中性提亮色（占比最多约 30%）
COLOR_FAMILY = {
    "红": "暖红", "粉": "暖红", "橙": "暖红",
    "黄": "暖黄",
    "蓝": "冷色", "紫": "冷色",
    "白": "中性",
    "绿": "叶色",
}
# 邻近色系（跨系协调的边界）
_ADJACENT = {
    ("暖红", "暖黄"), ("冷色", "中性"), ("暖红", "中性"), ("暖黄", "中性"),
}
_NEUTRAL = "中性"


def _family(color: str) -> str:
    return COLOR_FAMILY.get(catalog.normalize_color(color), _NEUTRAL)


def colors_harmonious(color_a: str, color_b: str) -> bool:
    """两色是否协调：同色系 / 邻近色系 / 任一方为中性提亮色。"""
    fa, fb = _family(color_a), _family(color_b)
    if fa == fb or fa == _NEUTRAL or fb == _NEUTRAL:
        return True
    return (fa, fb) in _ADJACENT or (fb, fa) in _ADJACENT


# ---------- 意图偏好（§1.2 评分依据） ----------

# 意图 → (偏好品种, 偏好色系)。评分：品种命中 +3，色系命中 +2，提亮色 +0.5
OCCASION_PREFS = {
    "情侣约会": (["玫瑰", "郁金香"], ["暖红"]),
    "毕业季": (["向日葵", "洋甘菊"], ["暖黄"]),
    "生日祝福": (["郁金香", "玫瑰", "绣球"], ["暖红", "暖黄"]),
    "探望问候": (["百合", "洋甘菊"], ["中性", "暖红"]),
    "日常惊喜": (["洋甘菊", "绣球", "满天星"], ["中性", "冷色", "暖红"]),
}

# 赠送花材候选（提亮/增加层次，按优先级）：默认优先满天星
_BONUS_CANDIDATES = [("满天星", "白"), ("洋甘菊", "白"), ("满天星", "紫")]


def _score(entry: dict, pref_species: list[str], pref_families: list[str]) -> float:
    score = 0.0
    if entry["species"] in pref_species:
        score += 3
    if _family(entry["color"]) in pref_families:
        score += 2
    if _family(entry["color"]) == _NEUTRAL:
        score += 0.5  # 提亮色加成
    return score


def select_items(occasion: str, available: list[dict]) -> tuple[list[dict], dict]:
    """确定性选品（§1）：从 quantity>0 库存选 1 种主花（+有合适辅花时 1 种），
    再选不与 items 重复的 bonus_flower（默认优先满天星）。

    available = [{species, color, quantity}]（已过滤 quantity>0）。
    返回 (items, bonus_flower)：朵数为配方固定（主 3 / 辅 1，主/辅约 7:3）——
    库存 quantity 是"使用次数"而非朵数，1 个库存可支持若干朵，朵数不与库存比较。
    """
    pref_species, pref_families = OCCASION_PREFS.get(occasion, ([], []))
    ranked = sorted(
        available,
        key=lambda e: (-_score(e, pref_species, pref_families), -e["quantity"], e["species"], e["color"]),
    )

    items: list[dict] = []
    if ranked:
        main = ranked[0]
        main_count = 3
        items.append({"species": main["species"], "color": main["color"], "count": main_count})
        # 辅花：色彩协调（同色/邻近色，避免两种大花并列）且非同一品种+颜色
        for cand in ranked[1:]:
            if (cand["species"], cand["color"]) == (main["species"], main["color"]):
                continue
            if not colors_harmonious(main["color"], cand["color"]):
                continue
            items.append({"species": cand["species"], "color": cand["color"],
                          "count": max(1, round(main_count * 3 / 7))})  # 主/辅约 7:3
            break

    taken = {(i["species"], i["color"]) for i in items}
    bonus_species, bonus_color = next(
        (s, c) for s, c in _BONUS_CANDIDATES if (s, c) not in taken
    )
    bonus_flower = {"species": bonus_species, "color": bonus_color, "count": 1, "gifted": True}
    return items, bonus_flower


def reason_template(items: list[dict], bonus_flower: dict, occasion: str) -> str:
    """推荐理由模板（20–30 字，LLM 不合格时兜底）：写清主花、配花/赠送花材与送花意图。"""
    main = items[0] if items else None
    if main is None:
        return f"{bonus_flower['color']}{bonus_flower['species']}一束，适合{occasion}的心意。"
    sub = next((i for i in items[1:] if not i.get("gifted")), None)
    parts = f"{main['color']}{main['species']}作主花"
    if sub:
        parts += f"，配{sub['color']}{sub['species']}"
    parts += f"，赠{bonus_flower['color']}{bonus_flower['species']}添层次，正合{occasion}。"
    return parts


# ---------- 预览图编排配方（§预览图-1） ----------

# 花材结构 → (构图, 落位)
_COMPOSITION = {
    1: ("圆润半球形", "同种花成簇，中心略高、边缘略低"),
    2: ("前低后高的圆三角", "主花在中心偏前；辅花环绕两侧与前下方"),
    3: ("自然扇形三角", "主花成组聚焦；辅花重复 2–3 处；点缀只填边缘空隙"),
}


def composition(items: list) -> tuple[str, str]:
    """按花材结构查编排配方表：1 种 / 主+辅 / 主+辅+点缀（赠送花材算点缀，触发第 3 行）。"""
    normal = [i for i in items if not getattr(i, "gifted", False)]
    n_species = len({i.species for i in normal})
    has_gifted = any(getattr(i, "gifted", False) for i in items)
    key = 3 if (has_gifted or n_species >= 3) else (2 if n_species == 2 else 1)
    return _COMPOSITION[key]


# 主色 → (低饱和包装纸色, 丝带色)：取主色深浅色或低饱和中性色
PACKAGING_COLORS = {
    "红": ("裸粉", "酒红"),
    "粉": ("象牙白", "香槟粉"),
    "黄": ("牛皮色", "深绿"),
    "白": ("浅灰", "香槟金"),
    "紫": ("米白", "银灰"),
    "蓝": ("雾灰蓝", "藏青"),
    "橙": ("奶油", "焦糖"),
    "绿": ("米白", "墨绿"),
}


def packaging_for(main_color: str) -> tuple[str, str]:
    """(包装纸色, 丝带色)，未收录色回落中性。"""
    return PACKAGING_COLORS.get(catalog.normalize_color(main_color), ("米白", "浅棕"))


def main_item(items: list):
    """主花 = 非赠送花材中朵数最多者（构图与包装色围绕它展开）。"""
    normal = [i for i in items if not getattr(i, "gifted", False)]
    pool = normal or list(items)
    return max(pool, key=lambda i: i.count, default=None)


def build_image_prompt(items: list) -> str:
    """按编排配方组装 Seedream 生图提示词（§预览图-2 模板）。"""
    materials = "、".join(
        f"{i.count}朵{i.color}{i.species}" + ("（赠送）" if getattr(i, "gifted", False) else "")
        for i in items
    )
    structure, placement = composition(items)
    main = main_item(items)
    paper, ribbon = packaging_for(main.color if main else "白")
    return (
        f"一束写实鲜花花束的商业摄影，必须清楚呈现且只呈现这些花材：{materials}。"
        f"花艺结构：{structure}；花材落位：{placement}。主花集中在中心偏前，辅花向两侧与前下方展开，"
        "花头前低后高、疏密自然，主色集中在视觉中心，辅色形成少量呼应。"
        f"包装：低饱和{paper}双层扇形包装纸，{ribbon}丝带；暖米色纯色背景，柔和自然光，"
        "浅景深，正方形构图，高级花艺摄影，花朵新鲜饱满。"
        "禁止：文字、水印、人物、手绘风格、额外花种、错误花色、机械并排、遮挡主花、花材数量明显不符。"
    )


# ---------- 文案校验与模板（§预览图-2 末段） ----------

def note_template(items: list[dict], occasion: str | None) -> str:
    """搭配说明模板（20–30 字）：主花、辅花/赠送花材、场景。"""
    if not items:
        return "一束随手而搭的清新花束。"
    main = items[0]
    note = f"{main['color']}{main['species']}作主花"
    gifted = next((i for i in items if i.get("gifted")), None)
    others = [i for i in items[1:] if not i.get("gifted")]
    if others:
        note += "，配" + "、".join(f"{i['color']}{i['species']}" for i in others)
    if gifted:
        note += f"，{gifted['color']}{gifted['species']}点缀"
    if occasion:
        note += f"，适合{occasion}"
    return note + "。"


def packaging_template(items: list[dict]) -> str:
    """包装建议模板（10–20 字）：纸材、颜色、丝带及衬托关系。"""
    main = items[0] if items else {"species": "花", "color": "白"}
    paper, ribbon = packaging_for(main["color"])
    return f"{paper}雾面纸配{ribbon}丝带，衬{main['color']}花更柔。"
