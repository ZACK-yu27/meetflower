"""花束预览生图：优先火山方舟 Seedream 写实花束摄影（settings.AI_PROVIDER=ark），失败降级 Pillow 合成。

mock：包装纸（扇形）+ 按清单排布的花头（复用 art.py 的花头绘制）+ 缎带/阴影点缀。
接口契约不变（API.md §4）：generate_bouquet(items, out_stem) -> /static/gen/{out_stem}.png。
"""

import logging
import math
import random
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFilter

from . import ark, settings
from .art import GEN_DIR, render_flower_head

logger = logging.getLogger("ai_gateway.imagegen")

URL_PREFIX = "/static/gen"
SIZE = 600

# 配色
_BG_TOP = "#FBF6EC"
_BG_BOTTOM = "#F1E5CE"
_PAPER_FRONT = "#DCC096"   # 包装纸（牛皮纸色）
_PAPER_BACK = "#E9D8B8"
_STEM = "#4E8A3C"
_RIBBON = "#C2495C"


@dataclass
class BouquetItem:
    species: str
    color: str
    count: int


def _vgradient(size: int, top: str, bottom: str) -> Image.Image:
    """竖直渐变底色。"""
    def rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    t, b = rgb(top), rgb(bottom)
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        f = y / (size - 1)
        d.line([(0, y), (size, y)],
               fill=tuple(int(t[i] + (b[i] - t[i]) * f) for i in range(3)))
    return img


def _head_positions(n: int, rnd: random.Random) -> tuple[list[tuple[float, float]], int]:
    """按总数把花头排成扇形 1~3 层，返回 [(x, y)] 与花头半径。"""
    rows = 1 if n <= 3 else (2 if n <= 6 else 3)
    head_r = 62 if n <= 4 else (54 if n <= 7 else 46)
    row_ys = [150 + i * 80 for i in range(rows)]
    # 每层朵数：上层多、下层少，形成饱满扇形
    counts = []
    left = n
    for i in range(rows):
        c = math.ceil(left / (rows - i))
        counts.append(c)
        left -= c
    pos: list[tuple[float, float]] = []
    for y, c in zip(row_ys, counts):
        spread = min(320, 90 * c)
        for j in range(c):
            x = 300 + (j - (c - 1) / 2) * (spread / max(1, c - 1) if c > 1 else 0)
            pos.append((x + rnd.uniform(-8, 8), y + rnd.uniform(-6, 6)))
    return pos, head_r


def generate_bouquet(items: list[BouquetItem], out_stem: str) -> str:
    """花束预览图。ark 模式优先 Seedream 写实生成，失败降级 Pillow 合成。"""
    if settings.AI_PROVIDER == "ark":
        try:
            return _generate_ark(items, out_stem)
        except Exception as e:  # noqa: BLE001 — 任何失败都降级，保证 Demo 不中断
            logger.warning("ark 生图失败，降级 Pillow: %s", e)
    return _generate_mock(items, out_stem)


# ---------- 真实生图（火山方舟 doubao-seedream-5-0-pro） ----------

def _build_prompt(items: list[BouquetItem]) -> str:
    flowers = "、".join(f"{it.count} 朵{it.color}色{it.species}" for it in items)
    return (
        f"一束写实风格的鲜花花束特写商业摄影：花材为{flowers}，"
        "花朵新鲜饱满、高低错落，牛皮纸扇形包装，系深色缎带蝴蝶结，"
        "暖米色纯色背景，柔和自然光，浅景深，正方形构图，高清花艺摄影质感"
    )


def _generate_ark(items: list[BouquetItem], out_stem: str) -> str:
    data = ark.image_b64(_build_prompt(items), size="1K")
    # Seedream 返回格式随参数（jpeg/png），按魔数定扩展名
    ext = ".png" if data.startswith(b"\x89PNG") else ".jpg"
    (GEN_DIR / f"{out_stem}{ext}").write_bytes(data)
    return settings.public_url(f"{URL_PREFIX}/{out_stem}{ext}")


# ---------- 本地 Pillow 合成（mock） ----------

def _generate_mock(items: list[BouquetItem], out_stem: str) -> str:
    """合成图保存到 assets/gen/{out_stem}.png，返回 /static/gen/{out_stem}.png。"""
    rnd = random.Random(out_stem)
    img = _vgradient(SIZE, _BG_TOP, _BG_BOTTOM).convert("RGBA")

    # 展开花材清单
    heads: list[tuple[str, str]] = []
    for it in items:
        heads.extend([(it.species, it.color)] * it.count)
    rnd.shuffle(heads)
    positions, head_r = _head_positions(len(heads), rnd)
    gather = (300, 430)  # 花茎收束点（包装纸腰部）

    d = ImageDraw.Draw(img)

    # 1) 花茎：从各花头底部到收束点
    for (x, y) in positions:
        d.line([x, y + head_r * 0.7, gather[0], gather[1]], fill=_STEM, width=5)

    # 2) 包装纸：后层大张扇形 + 前层扇形 + 折痕
    d.polygon([(120, 330), (300, 235), (480, 330), (355, 575), (245, 575)], fill=_PAPER_BACK)
    front = [(165, 300), (435, 300), (338, 568), (262, 568)]
    d.polygon(front, fill=_PAPER_FRONT)
    for fx in (165, 250, 350, 435):  # 折痕
        d.line([fx, 302, 300 + (fx - 300) * 0.12, 566], fill="#C4A374", width=2)

    # 3) 花头阴影：半透明椭圆偏移 + 高斯模糊
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for (x, y) in positions:
        r = head_r * 0.95
        sd.ellipse([x - r + 8, y - r + 14, x + r + 8, y + r + 14], fill=(60, 40, 20, 70))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7)))

    # 4) 花头：复用 art.py 的花头渲染，随机小角度旋转增加自然感
    for (species, color), (x, y) in zip(heads, positions):
        head = render_flower_head(head_r * 2, species, color)
        head = head.rotate(rnd.uniform(-18, 18), resample=Image.BICUBIC)
        img.alpha_composite(head, (int(x - head_r), int(y - head_r)))

    # 5) 缎带：横向束带 + 蝴蝶结
    band_y = 428
    d.line([228, band_y, 372, band_y], fill=_RIBBON, width=16)
    d.polygon([(300, band_y), (262, band_y - 26), (268, band_y + 22)], fill=_RIBBON)
    d.polygon([(300, band_y), (338, band_y - 26), (332, band_y + 22)], fill=_RIBBON)
    d.polygon([(300, band_y), (262, band_y - 26), (268, band_y + 22)], outline="#9E3446")
    d.polygon([(300, band_y), (338, band_y - 26), (332, band_y + 22)], outline="#9E3446")
    d.ellipse([292, band_y - 8, 308, band_y + 8], fill="#9E3446")

    out_path = GEN_DIR / f"{out_stem}.png"
    img.convert("RGB").save(out_path)
    return settings.public_url(f"{URL_PREFIX}/{out_stem}.png")
