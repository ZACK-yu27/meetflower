"""LLM 文案与推荐：优先火山方舟真实模型（settings.AI_PROVIDER=ark），失败降级本地模板 mock。

- flower_profile：2–4 句中文科普（生长节律始终来自 catalog，属产品配置而非模型职责）
- recommend_bouquet：选品/配比/赠送花材由 floristry 规则库确定性执行（docs/floristry_rules.md），
  LLM 只撰写推荐理由（20–30 字，长度校验不合格回落模板）——保证每次都按规则搭配
- arrangement_note / packaging_suggestion：一句话搭配说明 / 包装建议（模板兜底也在 floristry）
接口契约不变（API.md §4）。
"""

import logging
from dataclasses import dataclass

from . import ark, catalog, floristry, settings

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


# ---------- AI 推荐搭配 / 搭配说明 / 包装建议（API.md §4，规则库 floristry） ----------

def recommend_bouquet(occasion: str, available: list[dict]) -> dict:
    """按送花意图推荐组合。

    available = [{species, color, quantity}]（quantity>0 的库存）；
    选品/配比/赠送花材由 floristry.select_items 确定性执行（每次都按规则）；
    LLM 仅撰写 20–30 字推荐理由（ark），长度校验不合格或 mock 模式回落规则模板。
    返回 {items: [{species, color, count}], bonus_flower: {species, color, count, gifted: True}, reason: str}。
    """
    items, bonus_flower = floristry.select_items(occasion, available)
    reason: str | None = None
    if settings.AI_PROVIDER == "ark":
        try:
            reason = _reason_ark(occasion, items, bonus_flower)
        except Exception as e:  # noqa: BLE001
            logger.warning("ark 推荐理由失败，回落规则模板: %s", e)
    if not reason:
        reason = floristry.reason_template(items, bonus_flower, occasion)
    return {"items": items, "bonus_flower": bonus_flower, "reason": reason}


def _reason_ark(occasion: str, items: list[dict], bonus_flower: dict) -> str:
    desc = "、".join(f"{i['count']}朵{i['color']}{i['species']}" for i in items) or "无"
    text = ark.chat_text(
        [
            {
                "role": "user",
                "content": (
                    f"送花意图：{occasion}。花艺师已按规则选定花束：{desc}，"
                    f"另赠{bonus_flower['color']}{bonus_flower['species']}。"
                    "写 20–30 字推荐理由，写清主花、配花/赠送花材与送花意图。"
                    "不要标题和列表，直接输出这句话。"
                ),
            }
        ],
        max_tokens=80,
    )
    if not (10 <= len(text) <= 45):
        raise ark.ArkError(f"推荐理由长度不合格({len(text)}字): {text!r}")
    return text


def arrangement_note(items: list[dict], occasion: str | None) -> str:
    """预览时的搭配说明（20–30 字：主花、辅花/赠送花材和场景）。"""
    if settings.AI_PROVIDER == "ark":
        try:
            return _note_ark(items, occasion)
        except Exception as e:  # noqa: BLE001
            logger.warning("ark 搭配说明失败，降级模板: %s", e)
    return floristry.note_template(items, occasion)


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
                    "写 20–30 字搭配说明：点明主花、辅花/赠送花材和适合的场景。"
                    "不要标题和列表，直接输出这句话。"
                ),
            }
        ],
        max_tokens=80,
    )
    if not (10 <= len(text) <= 40):
        raise ark.ArkError(f"搭配说明长度不合格({len(text)}字): {text!r}")
    return text


def packaging_suggestion(items: list[dict], occasion: str | None) -> str:
    """包装建议（10–20 字：纸材、颜色、丝带及衬托关系）。"""
    if settings.AI_PROVIDER == "ark":
        try:
            return _packaging_ark(items, occasion)
        except Exception as e:  # noqa: BLE001
            logger.warning("ark 包装建议失败，降级模板: %s", e)
    return floristry.packaging_template(items)


def _packaging_ark(items: list[dict], occasion: str | None) -> str:
    main = items[0] if items else {"species": "花", "color": "白"}
    paper, ribbon = floristry.packaging_for(main["color"])
    text = ark.chat_text(
        [
            {
                "role": "user",
                "content": (
                    f"一束以{main['color']}{main['species']}为主的花束，送花意图：{occasion or '未指定'}。"
                    f"参考配色：{paper}包装纸、{ribbon}丝带。"
                    "写 10–20 字包装建议：纸材、颜色、丝带及它如何衬托花材。"
                    "不要标题和列表，直接输出这句话。"
                ),
            }
        ],
        max_tokens=60,
    )
    if not (8 <= len(text) <= 30):
        raise ark.ArkError(f"包装建议长度不合格({len(text)}字): {text!r}")
    return text
