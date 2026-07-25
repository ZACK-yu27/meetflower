"""LLM 文案与推荐：优先火山方舟真实模型（settings.AI_PROVIDER=ark），失败降级本地模板 mock。

- flower_profile：2–4 句中文科普（生长节律始终来自 catalog，属产品配置而非模型职责）
- recommend_bouquet：按送花意图推荐组合 + 赠送 1 种花材 + 理由（JSON 模式，结果校验后不合格降级）
- arrangement_note / packaging_suggestion：一句话搭配说明 / 包装建议
接口契约不变（API.md §4）。
"""

import json
import logging
from dataclasses import dataclass

from . import ark, catalog, settings

logger = logging.getLogger("ai_gateway.llm")


@dataclass
class StageSpec:
    stage: str           # seed / sprout / seedling / bud / bloom
    water: int
    sunlight: int
    nutrient: int


@dataclass
class FlowerProfile:
    science_text: str                # 2–4 句科普文案
    growth_rhythm: list[StageSpec]   # 全局统一生长节律（无缓冲期）


def flower_profile(species: str, main_color: str, secondary_color: str) -> FlowerProfile:
    """科普文案：ark 模式由真实模型撰写，失败降级图鉴模板；生长节律恒取 catalog。"""
    rhythm = [StageSpec(**row) for row in catalog.GROWTH_RHYTHM]
    if settings.AI_PROVIDER == "ark":
        try:
            return FlowerProfile(
                science_text=_profile_ark(species, main_color, secondary_color),
                growth_rhythm=rhythm,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("ark 科普文案失败，降级模板: %s", e)
    return FlowerProfile(
        science_text=_profile_mock(species, main_color, secondary_color),
        growth_rhythm=rhythm,
    )


def _profile_ark(species: str, main_color: str, secondary_color: str) -> str:
    text = ark.chat_text(
        [
            {
                "role": "user",
                "content": (
                    f"为「{main_color}色{species}」（辅色 {secondary_color}）写 2 句中文花卉科普："
                    "一句形态特征、一句花语寓意带养护小贴士。"
                    "语气轻快温暖，面向年轻用户；不要标题、不要列表、不要emoji，直接输出一个自然段。"
                ),
            }
        ],
        max_tokens=200,
    )
    if len(text) < 20:
        raise ark.ArkError(f"科普文案过短: {text!r}")
    return text


def _profile_mock(species: str, main_color: str, secondary_color: str) -> str:
    return catalog.science_text_for(species, main_color, secondary_color)


# ---------- AI 推荐搭配 / 搭配说明 / 包装建议（API.md §4） ----------

# 意图 → 赠送花材（mock 规则用；ark 模式下仅作降级）
_OCCASION_BONUS = {
    "情侣约会": ("玫瑰", "红"),
    "毕业季": ("向日葵", "黄"),
    "生日祝福": ("郁金香", "粉"),
    "探望问候": ("百合", "白"),
    "日常惊喜": ("洋甘菊", "白"),
}

_OCCASION_REASON_TAIL = {
    "情侣约会": "是情侣约会的经典之选",
    "毕业季": "献给前程似锦的毕业时刻",
    "生日祝福": "为生日送上最明亮的祝福",
    "探望问候": "探望时带去温柔与牵挂",
    "日常惊喜": "是平凡日子里的一束小惊喜",
}

# 主色 → (包装纸, 丝带)
_PACKAGING_BY_COLOR = {
    "红": ("奶白色雾面纸", "浅粉丝带"),
    "粉": ("象牙白棉纸", "香槟粉丝带"),
    "黄": ("牛皮色纸", "深绿丝带"),
    "白": ("浅灰雾面纸", "香槟金丝带"),
    "紫": ("米白色纸", "银灰丝带"),
}


def _resolve_color(species: str, color: str) -> str:
    """图鉴内品种：颜色不在可选范围内时回落到第一色；图鉴外品种：颜色原样保留。"""
    entry = catalog.CATALOG.get(species)
    if entry is None:
        return color
    colors = list(entry["colors"].keys())
    return color if color in colors else colors[0]


def recommend_bouquet(occasion: str, available: list[dict]) -> dict:
    """按送花意图推荐组合。

    available = [{species, color, quantity}]（quantity>0 的库存）；
    返回 {items: [{species, color, count}], bonus_flower: {species, color, count, gifted: True}, reason: str}。
    """
    if settings.AI_PROVIDER == "ark":
        try:
            return _recommend_ark(occasion, available)
        except Exception as e:  # noqa: BLE001
            logger.warning("ark 推荐搭配失败，降级规则: %s", e)
    return _recommend_mock(occasion, available)


def _recommend_ark(occasion: str, available: list[dict]) -> dict:
    result = ark.chat_json(
        [
            {
                "role": "system",
                "content": (
                    "你是花艺师。根据送花意图为用户推荐花束组合，只输出 JSON："
                    "{\"items\":[{\"species\":\"...\",\"color\":\"...\",\"count\":1}],"
                    "\"bonus_flower\":{\"species\":\"...\",\"color\":\"...\",\"count\":1},"
                    "\"reason\":\"...\"}。"
                    "规则：items 只能从给定库存中选 1–2 种（每种至多 2 朵，count 不超过库存）；"
                    "bonus_flower 是额外赠送的 1 种花材（不用用户种），品种不限，可以是任意常见花卉或配花，"
                    "尽量不与 items 重复；reason 为 30–60 字中文推荐理由。"
                ),
            },
            {
                "role": "user",
                "content": f"送花意图：{occasion}。库存：{json.dumps(available, ensure_ascii=False)}",
            },
        ],
        max_tokens=512,
    )

    # 校验：items 必须来自库存且不超量
    stock = {(e["species"], e["color"]): e["quantity"] for e in available}
    items = []
    for i in result.get("items") or []:
        key = (str(i.get("species", "")), str(i.get("color", "")))
        if key in stock:
            items.append({"species": key[0], "color": key[1],
                          "count": max(1, min(2, int(i.get("count", 1)), stock[key]))})
    items = items[:2]
    if available and not items:
        raise ark.ArkError("推荐 items 均不在库存内")

    b = result.get("bonus_flower") or {}
    bonus_species = str(b.get("species", "")).strip()
    if not bonus_species:
        raise ark.ArkError("赠送花材品种为空")
    bonus_color = _resolve_color(bonus_species, str(b.get("color", "")).strip() or "白")
    if (bonus_species, bonus_color) in {(i["species"], i["color"]) for i in items}:
        bonus_species, bonus_color = "满天星", "白"
    bonus_flower = {"species": bonus_species, "color": bonus_color, "count": 1, "gifted": True}

    reason = str(result.get("reason", "")).strip()
    if len(reason) < 10:
        raise ark.ArkError(f"推荐理由过短: {reason!r}")
    return {"items": items, "bonus_flower": bonus_flower, "reason": reason}


def _recommend_mock(occasion: str, available: list[dict]) -> dict:
    items = [
        {"species": e["species"], "color": e["color"], "count": min(2, e["quantity"])}
        for e in available[:2]
        if e["quantity"] > 0
    ]
    bonus_species, bonus_color = _OCCASION_BONUS.get(occasion, ("满天星", "白"))
    bonus_color = _resolve_color(bonus_species, bonus_color)
    if (bonus_species, bonus_color) in {(i["species"], i["color"]) for i in items}:
        bonus_species, bonus_color = "满天星", "白"
    bonus_flower = {"species": bonus_species, "color": bonus_color, "count": 1, "gifted": True}

    item_names = "、".join(f"{i['color']}{i['species']}" for i in items) or "当季花材"
    tail = _OCCASION_REASON_TAIL.get(occasion, "恰到好处的心意之选")
    reason = f"{item_names}象征真挚心意，搭配{bonus_color}{bonus_species}增添层次，{tail}。"
    return {"items": items, "bonus_flower": bonus_flower, "reason": reason}


def arrangement_note(items: list[dict], occasion: str | None) -> str:
    """预览时的搭配说明（一句话）。"""
    if settings.AI_PROVIDER == "ark":
        try:
            return _note_ark(items, occasion)
        except Exception as e:  # noqa: BLE001
            logger.warning("ark 搭配说明失败，降级模板: %s", e)
    return _note_mock(items, occasion)


def _note_ark(items: list[dict], occasion: str | None) -> str:
    desc = "、".join(
        f"{i['count']}朵{i['color']}{i['species']}" + ("（赠送）" if i.get("gifted") else "")
        for i in items
    ) or "无花材"
    text = ark.chat_text(
        [
            {
                "role": "user",
                "content": (
                    f"花束花材：{desc}。送花意图：{occasion or '未指定'}。"
                    "用一句话（20–40字）说明这束花的搭配思路：主花是谁、配花与层次如何、适合什么心意。"
                    "不要标题和列表，直接输出这句话。"
                ),
            }
        ],
        max_tokens=120,
    )
    if len(text) < 10:
        raise ark.ArkError(f"搭配说明过短: {text!r}")
    return text


def _note_mock(items: list[dict], occasion: str | None) -> str:
    if not items:
        return "一束随手而搭的清新花束。"
    main = items[0]
    note = f"{main['color']}{main['species']}作主花"
    gifted = next((i for i in items if i.get("gifted")), None)
    others = [i for i in items[1:] if i is not gifted]
    if others:
        note += "，配" + "、".join(f"{i['color']}{i['species']}" for i in others)
    if gifted:
        note += f"，{gifted['color']}{gifted['species']}作点缀增添浪漫层次"
    if occasion:
        note += f"，适合{occasion}"
    return note + "。"


def packaging_suggestion(items: list[dict], occasion: str | None) -> str:
    """包装建议一句话。"""
    if settings.AI_PROVIDER == "ark":
        try:
            return _packaging_ark(items, occasion)
        except Exception as e:  # noqa: BLE001
            logger.warning("ark 包装建议失败，降级模板: %s", e)
    return _packaging_mock(items, occasion)


def _packaging_ark(items: list[dict], occasion: str | None) -> str:
    main = items[0] if items else {"species": "花", "color": "白"}
    text = ark.chat_text(
        [
            {
                "role": "user",
                "content": (
                    f"一束以{main['color']}{main['species']}为主的花束，送花意图：{occasion or '未指定'}。"
                    "给一句包装建议（20–40字）：推荐具体的包装纸材质/颜色和丝带颜色，并说明它如何衬托花材气质。"
                    "不要标题和列表，直接输出这句话。"
                ),
            }
        ],
        max_tokens=120,
    )
    if len(text) < 10:
        raise ark.ArkError(f"包装建议过短: {text!r}")
    return text


def _packaging_mock(items: list[dict], occasion: str | None) -> str:
    main = items[0] if items else {"species": "花", "color": "白"}
    paper, ribbon = _PACKAGING_BY_COLOR.get(main["color"], _PACKAGING_BY_COLOR["白"])
    note = f"建议{paper}包裹，配{ribbon}，突出{main['color']}{main['species']}的气质"
    if occasion:
        note += f"，贴合{occasion}的心意"
    return note + "。"
