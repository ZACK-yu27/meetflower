"""Pillow 程序化绘制：5 个成长阶段图 + 花朵特写大图（200x200 PNG）。

设计规范 v2.0 §10 口径：阶段图统一为地栽版——透明底、植物从土丘中长出（无花盆）：
种子=土丘+半埋种粒、萌芽=破土小芽、幼苗=茎叶、花苞=茎顶花苞、盛放=完整花朵；
特写图：透明底大花头（供花房/花束复用）。已生成的文件直接复用。
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from . import catalog

# 生成图落盘目录：server/app/assets/gen（与 cwd 无关，按本文件位置推导）
GEN_DIR = Path(__file__).resolve().parent.parent / "assets" / "gen"
GEN_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE = 200          # 阶段图/特写图边长
URL_PREFIX = "/static/gen"

# 通用配色
_SEED = "#4A3222"
_STEM = "#4E8A3C"
_LEAF = "#5FA24A"
# 土丘配色（自然深棕，RGB 元组便于渐变插值）
_SOIL_TOP = (138, 95, 56)      # 表层土（亮）
_SOIL_BOTTOM = (62, 38, 20)    # 深层土（暗）
_SOIL_DARK = (46, 28, 14)
_SOIL_LIGHT = (164, 118, 74)


def _soil_at(f: float) -> tuple[int, int, int]:
    """土丘纵向 f（0=表土，1=底土）处的渐变颜色。"""
    return tuple(int(_SOIL_TOP[i] + (_SOIL_BOTTOM[i] - _SOIL_TOP[i]) * f) for i in range(3))


def _shade(hex_color: str, factor: float) -> tuple[int, int, int]:
    """factor>1 调亮，<1 调暗十六进制颜色。"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (
        min(255, max(0, int(r * factor))),
        min(255, max(0, int(g * factor))),
        min(255, max(0, int(b * factor))),
    )


def _rotate_layer(img: Image.Image, layer: Image.Image, angle: float, cx: float, cy: float) -> None:
    """把图层绕 (cx, cy) 旋转 angle 度后叠到 img 上。"""
    rotated = layer.rotate(angle, resample=Image.BICUBIC, center=(cx, cy))
    img.alpha_composite(rotated)


def _draw_petal(img: Image.Image, cx: float, cy: float, r: float, angle: float,
                length: float, width: float, fill, outline) -> None:
    """画一片绕花心 angle 度的椭圆花瓣（根部朝花心）。"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    dist = r * length * 0.5          # 花瓣中心到花心的距离
    rx, ry = r * length * 0.55, r * width
    d.ellipse([cx + dist - rx, cy - ry, cx + dist + rx, cy + ry], fill=fill, outline=outline)
    _rotate_layer(img, layer, angle, cx, cy)


# ---------- 各品种花头绘制 ----------

def _head_layered_round(img, cx, cy, r, base, params):
    """玫瑰：多层圆瓣，外深内浅，层间错开角度。"""
    outline = _shade(base, 0.75)
    for li, (count, rf) in enumerate(params["layers"]):
        fill = _shade(base, 0.92 + li * 0.08)
        for i in range(count):
            _draw_petal(img, cx, cy, r, i * 360 / count + li * 20, rf, 0.30, fill, outline)
    # 花心旋涡（图鉴外品种无 center_hex 时取主色深调）
    center = params.get("center_hex") or "#%02X%02X%02X" % _shade(base, 0.5)
    cr = r * 0.16
    d = ImageDraw.Draw(img)
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=center)
    d.arc([cx - cr * 0.7, cy - cr * 0.7, cx + cr * 0.7, cy + cr * 0.7], 30, 300,
          fill=_shade(base, 1.2), width=max(1, int(r * 0.05)))


def _head_slender_many(img, cx, cy, r, base, params):
    """向日葵：细长多瓣 + 深芯籽盘。"""
    outline = _shade(base, 0.78)
    n = params["petal_count"]
    for i in range(n):  # 外圈
        _draw_petal(img, cx, cy, r, i * 360 / n, params["petal_len"], params["petal_w"], _shade(base, 0.96), outline)
    for i in range(n):  # 内圈稍短，错开半格
        _draw_petal(img, cx, cy, r, (i + 0.5) * 360 / n, params["petal_len"] * 0.72,
                    params["petal_w"], base, outline)
    cr = r * 0.42
    d = ImageDraw.Draw(img)
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=params["center_hex"],
              outline=_shade(params["center_hex"], 0.7))
    # 籽点：两圈亮褐色小点
    for ring, rr in enumerate((0.28, 0.16)):
        cnt = 10 - ring * 3
        for i in range(cnt):
            a = math.radians(i * 360 / cnt + ring * 18)
            px, py = cx + math.cos(a) * r * rr, cy + math.sin(a) * r * rr
            pr = r * 0.035
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=_shade(params["center_hex"], 1.6))


def _head_daisy(img, cx, cy, r, base, params):
    """洋甘菊：白细瓣 + 黄芯。"""
    outline = _shade("#B9B29E", 1.0)
    n = params["petal_count"]
    for i in range(n):
        _draw_petal(img, cx, cy, r, i * 360 / n, params["petal_len"], params["petal_w"], base, outline)
    cr = r * 0.30
    d = ImageDraw.Draw(img)
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=params["center_hex"],
              outline=_shade(params["center_hex"], 0.8))
    rnd = random.Random(7)
    for _ in range(8):  # 花心颗粒感
        px = cx + rnd.uniform(-0.5, 0.5) * cr
        py = cy + rnd.uniform(-0.5, 0.5) * cr
        pr = r * 0.03
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=_shade(params["center_hex"], 0.82))


def _head_cup(img, cx, cy, r, base, _params):
    """郁金香：杯状花冠（两侧瓣 + 中瓣，顶部刻出缺口）。"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    outline = _shade(base, 0.72)
    # 两侧瓣（稍暗）
    d.ellipse([cx - 0.74 * r, cy - 0.82 * r, cx - 0.02 * r, cy + 0.52 * r], fill=_shade(base, 0.86), outline=outline)
    d.ellipse([cx + 0.02 * r, cy - 0.82 * r, cx + 0.74 * r, cy + 0.52 * r], fill=_shade(base, 0.86), outline=outline)
    # 中瓣（稍亮，略高）
    d.ellipse([cx - 0.38 * r, cy - 0.95 * r, cx + 0.38 * r, cy + 0.50 * r], fill=_shade(base, 1.06), outline=outline)
    # 底部收圆
    d.ellipse([cx - 0.55 * r, cy + 0.10 * r, cx + 0.55 * r, cy + 0.62 * r], fill=_shade(base, 0.95))
    # 顶部缺口：用减 alpha 的方式刻出郁金香经典唇形
    eraser = Image.new("L", img.size, 0)
    ImageDraw.Draw(eraser).ellipse(
        [cx - 0.16 * r, cy - 1.15 * r, cx + 0.16 * r, cy - 0.70 * r], fill=255)
    layer.putalpha(ImageChops.subtract(layer.getchannel("A"), eraser))
    img.alpha_composite(layer)


def _head_lily(img, cx, cy, r, base, params):
    """百合：6 片尖瓣两轮排列 + 花蕊。"""
    outline = _shade(base, 0.78)
    n = params["petal_count"]
    d = ImageDraw.Draw(img)
    for i in range(n):
        a = math.radians(i * 360 / n + 30)
        length = r if i % 2 == 0 else r * 0.86
        fill = base if i % 2 == 0 else _shade(base, 0.93)
        dx, dy = math.cos(a), math.sin(a)
        px, py = -dy, dx  # 垂直方向
        pts = [
            (cx + px * 0.10 * r, cy + py * 0.10 * r),
            (cx + dx * 0.55 * length + px * 0.24 * length, cy + dy * 0.55 * length + py * 0.24 * length),
            (cx + dx * length, cy + dy * length),
            (cx + dx * 0.55 * length - px * 0.24 * length, cy + dy * 0.55 * length - py * 0.24 * length),
            (cx - px * 0.10 * r, cy - py * 0.10 * r),
        ]
        d.polygon(pts, fill=fill, outline=outline)
    # 花蕊：5 根细丝 + 褐色花药，1 根更长的心皮
    for i in range(5):
        a = math.radians(i * 360 / 5 + 60)
        tx, ty = cx + math.cos(a) * 0.48 * r, cy + math.sin(a) * 0.48 * r
        d.line([cx, cy, tx, ty], fill="#C99A3C", width=max(1, int(r * 0.04)))
        ar = r * 0.07
        d.ellipse([tx - ar, ty - ar, tx + ar, ty + ar], fill="#8A5A24")
    d.line([cx, cy, cx + 0.12 * r, cy - 0.55 * r], fill="#7BAE5A", width=max(1, int(r * 0.05)))
    pr = r * 0.08
    d.ellipse([cx + 0.12 * r - pr, cy - 0.55 * r - pr, cx + 0.12 * r + pr, cy - 0.55 * r + pr], fill="#7BAE5A")


def _head_cluster(img, cx, cy, r, base, params):
    """满天星：小点簇，每点是一朵五瓣迷你花。"""
    rnd = random.Random(42)
    dot_r = r * params["dot_r"]
    outline = _shade(base, 0.8)
    d = ImageDraw.Draw(img)
    for _ in range(params["dot_count"]):
        a = rnd.uniform(0, math.tau)
        dist = rnd.uniform(0.1, 0.85) * r
        px, py = cx + math.cos(a) * dist, cy + math.sin(a) * dist
        for k in range(5):  # 5 片小圆瓣
            pa = math.radians(k * 72 + 18)
            qx, qy = px + math.cos(pa) * dot_r * 0.9, py + math.sin(pa) * dot_r * 0.9
            pr = dot_r * 0.62
            d.ellipse([qx - pr, qy - pr, qx + pr, qy + pr], fill=base, outline=outline)
        cr = dot_r * 0.5
        d.ellipse([px - cr, py - cr, px + cr, py + cr], fill=_shade(base, 1.1 if base != "#F3F0E9" else 0.9))


_HEAD_STYLES = {
    "layered_round": _head_layered_round,
    "slender_many": _head_slender_many,
    "cup": _head_cup,
    "daisy": _head_daisy,
    "lily": _head_lily,
    "cluster": _head_cluster,
}


def draw_flower_head(img: Image.Image, cx: float, cy: float, r: float, species: str, color: str) -> None:
    """在 RGBA 图上 (cx,cy) 处画半径 r 的花头；图鉴品种用专属画法，其余用通用画法。"""
    base = catalog.color_hex(species, color)
    params = catalog.draw_params(species)
    _HEAD_STYLES[params["style"]](img, cx, cy, r, base, params)


def render_flower_head(size: int, species: str, color: str) -> Image.Image:
    """渲染透明底花朵特写图（imagegen 合成花束时缩放复用）。"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw_flower_head(img, size / 2, size / 2, size * 0.46, species, color)
    return img


# ---------- 阶段图 ----------

def _draw_mound(img: Image.Image) -> None:
    """底部土丘：扁椭圆土堆（深棕竖向渐变 + 颗粒/土块纹理 + 丘脚散土），顶面 y≈148。"""
    cx, cy, rx, ry = 100, 170, 66, 22
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # 竖向渐变：表层亮、深层暗，逐行按椭圆宽度截弦
    for y in range(cy - ry, cy + ry + 1):
        half = rx * math.sqrt(max(0.0, 1.0 - ((y - cy) / ry) ** 2))
        d.line([cx - half, y, cx + half, y],
               fill=_soil_at((y - (cy - ry)) / (2 * ry)) + (255,))
    rnd = random.Random(2024)
    # 颗粒纹理：明暗土粒随机散布（限制在椭圆内）
    for _ in range(150):
        a = rnd.uniform(0, math.tau)
        rr = math.sqrt(rnd.uniform(0, 1))
        px = cx + math.cos(a) * rr * (rx - 3)
        py = cy + math.sin(a) * rr * (ry - 3)
        pr = rnd.uniform(0.8, 1.8)
        color = rnd.choice([_SOIL_DARK, _SOIL_LIGHT, _SOIL_BOTTOM])
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=color + (rnd.randint(80, 150),))
    # 土块：几团较大的深色扁块
    for _ in range(6):
        a = rnd.uniform(0, math.tau)
        rr = math.sqrt(rnd.uniform(0, 1))
        px = cx + math.cos(a) * rr * (rx - 10)
        py = cy + math.sin(a) * rr * (ry - 6)
        pr = rnd.uniform(2.5, 4.5)
        d.ellipse([px - pr, py - pr * 0.7, px + pr, py + pr * 0.7], fill=_SOIL_DARK + (110,))
    # 根部土壤散开感：丘脚外零星散土点
    for _ in range(16):
        px = cx + rnd.uniform(-rx * 1.3, rx * 1.3)
        py = cy + rnd.uniform(-ry * 0.2, ry * 1.25)
        if ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 < 1:
            continue  # 只撒在土丘外
        pr = rnd.uniform(0.8, 2.0)
        d.ellipse([px - pr, py - pr, px + pr, py + pr],
                  fill=rnd.choice([_SOIL_TOP, _SOIL_BOTTOM]) + (rnd.randint(120, 200),))
    img.alpha_composite(layer)


def _draw_leaf(img: Image.Image, x: float, y: float, angle: float, length: float) -> None:
    """单片叶子：绕 (x,y) 旋转的椭圆 + 叶脉。"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w = length * 0.30
    d.ellipse([x, y - w, x + length, y + w], fill=_LEAF, outline=_shade(_LEAF, 0.7))
    d.line([x + 2, y, x + length - 2, y], fill=_shade(_LEAF, 0.72), width=1)
    _rotate_layer(img, layer, angle, x, y)


def _draw_stem(d: ImageDraw.ImageDraw, top_y: float) -> None:
    d.line([100, 148, 100, top_y], fill=_STEM, width=4)


def _stage_image(species: str, color: str, stage: str) -> Image.Image:
    """地栽版阶段图：透明底，植物从土丘中长出，主体尽量撑满 200x200 画面。"""
    img = Image.new("RGBA", (IMG_SIZE, IMG_SIZE), (0, 0, 0, 0))
    _draw_mound(img)
    d = ImageDraw.Draw(img)

    if stage == "seed":
        d.ellipse([94, 144, 106, 155], fill=_SEED)  # 种粒
        d.chord([93, 149, 107, 158], 0, 180, fill=_soil_at(0.12))  # 下半覆土，呈半埋状态
    elif stage == "sprout":
        _draw_stem(d, 124)
        _draw_leaf(img, 100, 126, -150, 13)
        _draw_leaf(img, 100, 126, -30, 13)
    elif stage == "seedling":
        _draw_stem(d, 94)
        _draw_leaf(img, 100, 126, -155, 24)
        _draw_leaf(img, 100, 114, -25, 24)
        _draw_leaf(img, 100, 96, -90, 14)
    elif stage == "bud":
        _draw_stem(d, 80)
        _draw_leaf(img, 100, 124, -155, 22)
        _draw_leaf(img, 100, 112, -25, 22)
        # 花苞：品种色椭圆苞体 + 尖顶 + 绿色萼片
        base = catalog.color_hex(species, color)
        d.polygon([(92, 80), (108, 80), (100, 90)], fill=_STEM)  # 萼片
        d.ellipse([89, 50, 111, 82], fill=_shade(base, 0.95), outline=_shade(base, 0.7))
        d.polygon([(94, 52), (106, 52), (100, 40)], fill=_shade(base, 0.85), outline=_shade(base, 0.7))
    elif stage == "bloom":
        _draw_stem(d, 122)
        _draw_leaf(img, 100, 138, -155, 22)
        _draw_leaf(img, 100, 128, -25, 22)
        draw_flower_head(img, 100, 76, 48, species, color)
    return img


# ---------- 对外接口（API.md §4） ----------

def stage_image_url(species: str, main_color: str, stage: str) -> str:
    return f"{URL_PREFIX}/{catalog.file_stem(species, main_color)}_{stage}.png"


def flower_image_url(species: str, main_color: str) -> str:
    return f"{URL_PREFIX}/{catalog.file_stem(species, main_color)}_flower.png"


def ensure_stage_images(species: str, main_color: str) -> dict[str, str]:
    """为 (品种,颜色) 生成 5 阶段图 + 花朵特写图（已存在则复用），返回 {stage: url}。"""
    stem = catalog.file_stem(species, main_color)
    urls: dict[str, str] = {}
    for stage in catalog.STAGES:
        path = GEN_DIR / f"{stem}_{stage}.png"
        if not path.exists():
            _stage_image(species, main_color, stage).save(path)
        urls[stage] = f"{URL_PREFIX}/{path.name}"
    flower_path = GEN_DIR / f"{stem}_flower.png"
    if not flower_path.exists():
        render_flower_head(IMG_SIZE, species, main_color).save(flower_path)
    return urls
