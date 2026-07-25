"""VLM 识花：优先火山方舟真实视觉模型（settings.AI_PROVIDER=ark），失败降级本地 mock。

mock：按图片字节哈希确定性命中图鉴（同一图片永远识别为同一结果）。
真实：chat/completions 多模态（base64 图片 + JSON 模式），自由识别——品种/颜色不限于图鉴，
图鉴外品种由 catalog 通用画法与颜色表/哈希兜底生成视觉资产。
接口契约不变（API.md §4）：identify_flower(image_path) -> VlmResult。
"""

import base64
import hashlib
import logging
from dataclasses import dataclass

from . import ark, catalog, settings, video

logger = logging.getLogger("ai_gateway.vlm")


@dataclass
class VlmResult:
    species: str           # 品种（中文）
    main_color: str        # 主色（中文，命中该品种可选颜色之一）
    secondary_color: str   # 辅色（同品种另一可选颜色；单色品种则与主色相同）
    confidence: float      # 置信度 0.85–0.97（mock 由哈希派生；真实由模型给出并截断到该区间）
    form: str = "rosette"  # 花型（catalog.FORMS 之一），决定线稿轮廓


def identify_flower(image_path: str) -> VlmResult:
    """识别上传图片中的花。ark 模式优先真实 VLM，异常自动降级 mock。"""
    if settings.AI_PROVIDER == "ark":
        try:
            return _identify_ark(image_path)
        except Exception as e:  # noqa: BLE001 — 任何失败都降级，保证 Demo 不中断
            logger.warning("ark VLM 失败，降级 mock: %s", e)
    return _identify_mock(image_path)


# ---------- 真实 VLM（火山方舟 doubao-seed-2-0-lite） ----------

_SYSTEM = (
    "你是花卉识别专家。识别用户图片中的花朵：species 为中文通用品种名（如绣球、洋桔梗、向日葵，"
    "不确定时给出最接近的常见花卉名）；main_color 为主色，secondary_color 为辅色，均为简洁中文颜色名"
    "（如红、粉、白、黄、紫、蓝、橙、绿），单色花两者相同；"
    "form 为花型，必须从这 7 个英文枚举中选最接近的一个："
    "rosette=重瓣层叠（玫瑰/月季/牡丹/康乃馨）、daisy=单瓣放射（洋甘菊/雏菊/波斯菊）、"
    "disk=舌状花盘（向日葵/非洲菊）、cup=杯状花冠（郁金香）、lily=星型尖瓣（百合/萱草）、"
    "ball=聚伞花球（绣球/丁香，许多小花攒成圆球）、cluster=星点散簇（满天星，细碎小花松散分布）；"
    "confidence 为 0 到 1 的置信度。"
    "只输出 JSON：{\"species\":\"...\",\"main_color\":\"...\",\"secondary_color\":\"...\","
    "\"form\":\"rosette\",\"confidence\":0.9}"
)


def _identify_ark(image_path: str) -> VlmResult:
    with open(image_path, "rb") as f:
        raw = f.read()
    suffix = image_path.rsplit(".", 1)[-1].lower()
    mime = "jpeg" if suffix in ("jpg", "jpeg") else "png"
    data_url = f"data:image/{mime};base64,{base64.b64encode(raw).decode()}"

    result = ark.chat_json(
        [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "识别这朵花。"},
                    # detail=low：低精细度图片理解，实测延时降约 40%（docs/model_api/seed-2.1-turbo.md）
                    {"type": "image_url", "image_url": {"url": data_url, "detail": "low"}},
                ],
            },
        ],
        max_tokens=128,
        model=settings.ARK_VLM_MODEL,
    )

    species = str(result.get("species", "")).strip()
    if not species:
        raise ark.ArkError("品种为空")
    main_color = str(result.get("main_color", "")).strip()
    if not main_color:
        raise ark.ArkError("主色为空")
    secondary_color = str(result.get("secondary_color", "")).strip() or main_color
    form = str(result.get("form", "")).strip()
    if form not in catalog.FORMS:
        form = catalog.form_for(species)  # 非法/缺失：图鉴品种取图鉴画法，否则回落 rosette
    try:
        confidence = min(0.97, max(0.85, float(result.get("confidence", 0.9))))
    except (TypeError, ValueError):
        confidence = 0.9
    return VlmResult(
        species=species,
        main_color=main_color,
        secondary_color=secondary_color,
        confidence=round(confidence, 2),
        form=form,
    )


# ---------- 本地 mock ----------

def _identify_mock(image_path: str) -> VlmResult:
    """读取图片字节做 sha256，由摘要确定性选出品种+颜色与置信度。"""
    with open(image_path, "rb") as f:
        digest = hashlib.sha256(f.read()).digest()

    species_list = list(catalog.CATALOG.keys())
    species = species_list[int.from_bytes(digest[0:4], "big") % len(species_list)]

    colors = list(catalog.CATALOG[species]["colors"].keys())
    main_color = colors[digest[4] % len(colors)]
    secondary_color = colors[(colors.index(main_color) + 1) % len(colors)]

    confidence = round(0.85 + (int.from_bytes(digest[5:9], "big") % 13) * 0.01, 2)

    return VlmResult(
        species=species,
        main_color=main_color,
        secondary_color=secondary_color,
        confidence=confidence,
        form=catalog.form_for(species),
    )


# ---------- 广义的"花"（视频 → 属性 → 花卉匹配，规则见 docs/flower_resemble.md） ----------

RESEMBLE_ATTR_KEYS = ("subject", "shape", "color", "texture")

_ATTR_SYSTEM = (
    "你是视频内容分析专家。用户会给你同一视频按时间顺序抽取的若干帧。"
    "识别视频主体并抽取属性，只输出 JSON："
    "{\"subject\":\"主体名（简洁中文名词，如 烟花/猫爪/喷泉）\","
    "\"shape\":\"形态（整体轮廓与结构动态，如 放射状球形炸开）\","
    "\"color\":\"颜色（主色调，简洁中文）\","
    "\"texture\":\"质感（如 丝绒/绒毛/水雾/玻璃）\"}"
)

_MATCH_SYSTEM = (
    "你是花卉检索专家。用户给你一段视频主体的属性（形态/颜色/质感），"
    "以形态为主、颜色与质感为辅，找出现实世界中最相似的一种真实花卉。"
    "花型 form 必须从 7 个枚举选：rosette=重瓣层叠（玫瑰/牡丹）、daisy=单瓣放射（洋甘菊/雏菊）、"
    "disk=舌状花盘（向日葵）、cup=杯状（郁金香）、lily=星型尖瓣（百合）、"
    "ball=聚伞花球（绣球/蒲公英）、cluster=星点散簇（满天星）；"
    "main_color/secondary_color 为简洁中文色名（红/粉/白/黄/紫/蓝/橙/绿），单色花两者相同。"
    "只输出 JSON：{\"species\":\"...\",\"main_color\":\"...\",\"secondary_color\":\"...\","
    "\"form\":\"...\",\"confidence\":0.9,\"reason\":\"一句话说明为什么像\"}"
)


def identify_resemble(video_path: str) -> tuple[VlmResult, dict, bytes | None]:
    """广义的花识别：返回 (VlmResult, 属性dict, 封面JPEG字节|None)。

    ark：抽帧（每 3s 1 帧 ≤8 帧）→ VLM 抽属性 → LLM 检索匹配；失败降级 mock。
    视频无法解析（VideoFrameError）不降级，直接抛给上层转 422。
    """
    if settings.AI_PROVIDER == "ark":
        try:
            return _resemble_ark(video_path)
        except video.VideoFrameError:
            raise
        except Exception as e:  # noqa: BLE001 — 任何模型失败都降级，保证 Demo 不中断
            logger.warning("ark 广义花识别失败，降级 mock: %s", e)
    return _resemble_mock(video_path)


def _resemble_ark(video_path: str) -> tuple[VlmResult, dict, bytes]:
    frames, poster = video.extract_frames(video_path)

    # 第一段：VLM 抽取主体属性（多帧，detail=low 与拍照识别同策略）
    content: list[dict] = [{"type": "text", "text": "这是同一视频按时间顺序抽出的帧，分析视频主体。"}]
    for frame in frames:
        b64 = base64.b64encode(frame.read_bytes()).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}})
    attrs = ark.chat_json(
        [{"role": "system", "content": _ATTR_SYSTEM}, {"role": "user", "content": content}],
        max_tokens=256,
        model=settings.ARK_VLM_MODEL,
    )
    attrs = {k: str(attrs.get(k, "")).strip() for k in RESEMBLE_ATTR_KEYS}
    if any(not v for v in attrs.values()):
        raise ark.ArkError(f"属性抽取不完整: {attrs}")

    # 第二段：属性 → 花卉检索匹配（纯文本 LLM）
    result = ark.chat_json(
        [
            {"role": "system", "content": _MATCH_SYSTEM},
            {"role": "user", "content": f"视频主体属性：{attrs}。检索最相似的花卉。"},
        ],
        max_tokens=256,
        model=settings.ARK_CHAT_MODEL,
    )
    species = str(result.get("species", "")).strip()
    if not species:
        raise ark.ArkError("品种为空")
    main_color = str(result.get("main_color", "")).strip()
    if not main_color:
        raise ark.ArkError("主色为空")
    secondary_color = str(result.get("secondary_color", "")).strip() or main_color
    form = str(result.get("form", "")).strip()
    if form not in catalog.FORMS:
        form = catalog.form_for(species)
    try:
        confidence = min(0.97, max(0.85, float(result.get("confidence", 0.9))))
    except (TypeError, ValueError):
        confidence = 0.9
    reason = str(result.get("reason", "")).strip()
    if reason:
        attrs["reason"] = reason

    vlm = VlmResult(
        species=species,
        main_color=main_color,
        secondary_color=secondary_color,
        confidence=round(confidence, 2),
        form=form,
    )
    return vlm, attrs, poster


def _resemble_mock(video_path: str) -> tuple[VlmResult, dict, None]:
    """按视频字节哈希确定性命中图鉴 + 模板化属性（离线/降级兜底）。"""
    with open(video_path, "rb") as f:
        digest = hashlib.sha256(f.read()).digest()

    species_list = list(catalog.CATALOG.keys())
    species = species_list[int.from_bytes(digest[0:4], "big") % len(species_list)]
    colors = list(catalog.CATALOG[species]["colors"].keys())
    main_color = colors[digest[4] % len(colors)]
    secondary_color = colors[(colors.index(main_color) + 1) % len(colors)]
    confidence = round(0.85 + (int.from_bytes(digest[5:9], "big") % 13) * 0.01, 2)
    form = catalog.form_for(species)

    attrs = {
        "subject": "视频主体",
        "shape": f"向四周展开的{catalog.FORM_NAMES[form].split('（')[0]}轮廓",
        "color": f"{main_color}色系",
        "texture": "柔和光泽",
        "reason": f"它的形态让人联想到{main_color}色的{species}（演示环境模拟识别）",
    }
    vlm = VlmResult(
        species=species,
        main_color=main_color,
        secondary_color=secondary_color,
        confidence=confidence,
        form=form,
    )
    return vlm, attrs, None
