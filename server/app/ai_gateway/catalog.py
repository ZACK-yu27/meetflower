"""花卉图鉴与通用品种兜底：品种/颜色/花型规则、绘制参数、科普文案模板、全局生长节律。

线稿生成规则（单一事实来源，任何修改必须同步 flower-lineart skill）：

【颜色规则】
1. VLM 只许返回 STANDARD_COLORS 中的简洁中文色名（红/粉/白/黄/紫/蓝/橙/绿）；
2. 渲染色 = 图鉴精确 hex > 通用色表 GENERIC_COLORS > 哈希派生（仅未收录色名）；
3. 色名先经 normalize_color 归一化（去空格、去尾部"色"字），未收录才走哈希。

【花型（轮廓）规则】
1. 花型枚举 FORMS：rosette 重瓣层叠 / daisy 单瓣放射 / disk 舌状花盘 / cup 杯状 /
   lily 星型尖瓣 / ball 聚伞花球（绣球型）/ cluster 星点散簇（满天星型）；
2. 图鉴品种轮廓恒取图鉴 draw（不受 VLM 影响）；
3. 图鉴外品种轮廓取 VLM 识别的 form（非法值回落 rosette）；
4. form 经 URL 传递到渲染端点，保证「识别什么花型就画什么轮廓」。

2026-07-25 起取消品种限制：CATALOG 外品种/颜色全部可用，经 GENERIC_COLORS /
draw_params / science_text_for 等兜底函数获得通用渲染与文案。
"""

import colorsys
import hashlib

# 成长阶段顺序（seed=0 … bloom=4）
STAGES = ["seed", "sprout", "seedling", "bud", "bloom"]

# 标准色名（VLM 输出约束 + 通用色表键）
STANDARD_COLORS = ["红", "粉", "白", "黄", "紫", "蓝", "橙", "绿"]

# 花型枚举（轮廓规则见模块 docstring）
FORMS = ["rosette", "daisy", "disk", "cup", "lily", "ball", "cluster"]
FORM_NAMES = {
    "rosette": "重瓣层叠（玫瑰/月季/牡丹/康乃馨）",
    "daisy": "单瓣放射（洋甘菊/雏菊/波斯菊）",
    "disk": "舌状花盘（向日葵/非洲菊）",
    "cup": "杯状花冠（郁金香）",
    "lily": "星型尖瓣（百合/萱草）",
    "ball": "聚伞花球（绣球/丁香）",
    "cluster": "星点散簇（满天星）",
}

# 全局统一生长节律（API.md v0.2 §0：向日葵示例值，每阶段"每个人"所需资源，无缓冲期）
GROWTH_RHYTHM = [
    {"stage": "seed", "water": 2, "sunlight": 0, "nutrient": 0},
    {"stage": "sprout", "water": 3, "sunlight": 1, "nutrient": 0},
    {"stage": "seedling", "water": 4, "sunlight": 2, "nutrient": 2},
    {"stage": "bud", "water": 5, "sunlight": 3, "nutrient": 3},
    {"stage": "bloom", "water": 0, "sunlight": 0, "nutrient": 0},  # 终态
]

# 图鉴：6 品种，含颜色 hex、花瓣绘制参数（供 art.py 按 style 分派）、科普文案模板
# draw.style 取值：layered_round 玫瑰 / slender_many 向日葵 / cup 郁金香
#                  daisy 洋甘菊 / lily 百合 / cluster 满天星
CATALOG = {
    "玫瑰": {
        "species_en": "rose",
        "colors": {
            "红": {"color_en": "red", "hex": "#D2364C"},
            "粉": {"color_en": "pink", "hex": "#F2A7C3"},
            "白": {"color_en": "white", "hex": "#F5EFE3"},
        },
        "draw": {"style": "layered_round", "layers": [(9, 0.95), (7, 0.68), (5, 0.42)], "center_hex": "#8E1F33"},
        "science_template": (
            "{species}是蔷薇科蔷薇属的灌木，{main_color}色花瓣层层叠叠，是花店里永远的明星。"
            "{main_color}{species}象征热烈而真挚的爱意，送人自带浪漫加成。"
            "养护小贴士：喜阳光充足、通风良好的环境，浇水见干见湿即可。"
        ),
    },
    "向日葵": {
        "species_en": "sunflower",
        "colors": {
            "黄": {"color_en": "yellow", "hex": "#F7B32B"},
        },
        "draw": {"style": "slender_many", "petal_count": 18, "petal_len": 1.0, "petal_w": 0.16, "center_hex": "#6B4422"},
        "science_template": (
            "{species}是菊科向日葵属的一年生草本，{main_color}色舌状花围着深褐色花盘，永远朝着太阳转。"
            "它寓意忠诚、阳光与「沉默的爱」，看着就让人心情变好。"
            "养护小贴士：名副其实的喜阳选手，日照越足开得越旺，保持土壤微湿即可。"
        ),
    },
    "郁金香": {
        "species_en": "tulip",
        "colors": {
            "红": {"color_en": "red", "hex": "#E1424B"},
            "黄": {"color_en": "yellow", "hex": "#F7C948"},
            "紫": {"color_en": "purple", "hex": "#8E5EA2"},
        },
        "draw": {"style": "cup"},
        "science_template": (
            "{species}是百合科郁金香属的球根花卉，{main_color}色杯状花冠挺拔优雅，是春天的信使。"
            "{main_color}{species}寓意爱的告白与永远的祝福，一束就能撑起整个桌面。"
            "养护小贴士：喜凉爽怕酷热，切花插瓶时少加水、勤换水，能开得更久。"
        ),
    },
    "洋甘菊": {
        "species_en": "chamomile",
        "colors": {
            "白": {"color_en": "white", "hex": "#FAF7EC"},
        },
        "draw": {"style": "daisy", "petal_count": 14, "petal_len": 1.0, "petal_w": 0.17, "center_hex": "#F2C230"},
        "science_template": (
            "{species}是菊科母菊属的草本小花，{main_color}色细瓣托着金黄花心，自带治愈气质。"
            "它寓意逆境中的坚强与温柔，晒干后还能泡一杯安神的{species}茶。"
            "养护小贴士：皮实好养，喜光也耐半阴，保持通风、避免积水就好。"
        ),
    },
    "百合": {
        "species_en": "lily",
        "colors": {
            "白": {"color_en": "white", "hex": "#F6F1E6"},
            "粉": {"color_en": "pink", "hex": "#E8A0B4"},
        },
        "draw": {"style": "lily", "petal_count": 6},
        "science_template": (
            "{species}是百合科百合属的球根花卉，{main_color}色六片尖瓣舒展大方，香气清雅。"
            "{main_color}{species}寓意纯洁、庄严与百年好合，是祝福场合的常客。"
            "养护小贴士：喜凉爽湿润，切花记得摘掉花药，既防染色又能延长花期。"
        ),
    },
    "满天星": {
        "species_en": "babysbreath",
        "colors": {
            "紫": {"color_en": "purple", "hex": "#B39DDB"},
            "白": {"color_en": "white", "hex": "#F3F0E9"},
        },
        "draw": {"style": "cluster", "dot_count": 16, "dot_r": 0.14},
        "science_template": (
            "{species}是石竹科石头花属的草本，{main_color}色小花星星点点聚成一片，像把银河握在手里。"
            "它寓意清纯、思念与「甘愿做配角」的守护，也是花束里最百搭的配角。"
            "养护小贴士：喜干燥通风，倒挂阴干即成干花，能陪你很久很久。"
        ),
    },
    "绣球": {
        "species_en": "hydrangea",
        "colors": {
            "蓝": {"color_en": "blue", "hex": "#7C9FDC"},
            "粉": {"color_en": "pink", "hex": "#F0A8C0"},
            "紫": {"color_en": "purple", "hex": "#A98FD4"},
        },
        "draw": {"style": "ball", "floret_count": 14},
        "science_template": (
            "{species}是绣球花科绣球属的灌木，{main_color}色小花密密攒成圆润花球，团团可爱。"
            "{main_color}{species}寓意团圆、美满与希望，花色还会随土壤酸碱变换。"
            "养护小贴士：喜半阴湿润，花球怕暴晒，缺水会立刻蔫头，及时补水就能精神回来。"
        ),
    },
}


def get_species(species: str) -> dict:
    """按中文品种名取图鉴条目，未知品种抛 KeyError。"""
    return CATALOG[species]


# ---------- 图鉴外品种/颜色通用兜底（取消品种限制后） ----------

# 标准色名 → (英文, hex)；未收录的色名走哈希派生（稳定）
GENERIC_COLORS = {
    "红": ("red", "#D2364C"),
    "粉": ("pink", "#F2A7C3"),
    "白": ("white", "#F5EFE3"),
    "黄": ("yellow", "#F7B32B"),
    "紫": ("purple", "#8E5EA2"),
    "蓝": ("blue", "#4A7FC4"),
    "橙": ("orange", "#E8833A"),
    "绿": ("green", "#5FA24A"),
}

# 各花型的通用绘制参数（图鉴外品种按 form 选用；图鉴品种恒用图鉴 draw）
_FORM_DRAW = {
    "rosette": {"style": "layered_round", "layers": [(9, 0.95), (7, 0.68), (5, 0.42)]},
    "daisy": {"style": "daisy", "petal_count": 14, "petal_len": 1.0, "petal_w": 0.17, "center_hex": "#F2C230"},
    "disk": {"style": "slender_many", "petal_count": 18, "petal_len": 1.0, "petal_w": 0.16, "center_hex": "#6B4422"},
    "cup": {"style": "cup"},
    "lily": {"style": "lily", "petal_count": 6},
    "ball": {"style": "ball", "floret_count": 14},
    "cluster": {"style": "cluster", "dot_count": 16, "dot_r": 0.14},
}

_GENERIC_SCIENCE_TEMPLATE = (
    "{species}是一株姿态动人的花，{main_color}色花冠是它最醒目的名片。"
    "{main_color}{species}象征着真挚而独特的心意，适合送给重要的人。"
    "养护小贴士：保持通风与适度光照，浇水见干见湿即可。"
)


def _stable_int(s: str) -> int:
    return int.from_bytes(hashlib.sha256(s.encode("utf-8")).digest()[:8], "big")


def normalize_color(color: str) -> str:
    """色名归一化：去空白、去尾部「色」字（如「蓝色」→「蓝」）、去英文句点。"""
    c = (color or "").strip().rstrip(".。")
    if c.endswith("色") and len(c) > 1:
        c = c[:-1]
    return c


def form_for(species: str, hint: str | None = None) -> str:
    """花型解析：图鉴品种恒取图鉴画法对应的 form > VLM hint（合法才用）> rosette。"""
    entry = CATALOG.get(species)
    if entry:
        style = entry["draw"]["style"]
        for form, draw in _FORM_DRAW.items():
            if draw["style"] == style:
                return form
    if hint in FORMS:
        return hint
    return "rosette"


def species_en(species: str) -> str:
    """品种英文名；图鉴外品种用稳定哈希名（custom_xxxxxxxx）。"""
    entry = CATALOG.get(species)
    if entry:
        return entry["species_en"]
    return f"custom_{_stable_int('sp:' + species) % 0xFFFFFFFF:08x}"


def color_en(species: str, color: str) -> str:
    """颜色英文名：图鉴精确值 > 通用颜色表 > 稳定哈希名。"""
    color = normalize_color(color)
    entry = CATALOG.get(species)
    if entry and color in entry["colors"]:
        return entry["colors"][color]["color_en"]
    if color in GENERIC_COLORS:
        return GENERIC_COLORS[color][0]
    return f"c{_stable_int('co:' + color) % 0xFFFFFF:06x}"


def color_hex(species: str, color: str) -> str:
    """颜色 hex：图鉴精确值 > 通用颜色表 > 哈希派生（高饱和亮色调，稳定）。"""
    color = normalize_color(color)
    entry = CATALOG.get(species)
    if entry and color in entry["colors"]:
        return entry["colors"][color]["hex"]
    if color in GENERIC_COLORS:
        return GENERIC_COLORS[color][1]
    hue = (_stable_int("hex:" + species + color) % 360) / 360.0
    r, g, b = colorsys.hls_to_rgb(hue, 0.62, 0.72)
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def draw_params(species: str, form: str | None = None) -> dict:
    """绘制参数：图鉴品种恒用图鉴画法；图鉴外品种按 form 取通用花型画法（见 FORMS）。"""
    entry = CATALOG.get(species)
    if entry:
        return dict(entry["draw"])
    return dict(_FORM_DRAW[form_for(species, form)])


def science_text_for(species: str, main_color: str, secondary_color: str) -> str:
    """mock 科普文案：图鉴品种用专属模板，图鉴外品种用通用模板。"""
    entry = CATALOG.get(species)
    template = entry["science_template"] if entry else _GENERIC_SCIENCE_TEMPLATE
    return template.format(species=species, main_color=main_color, secondary_color=secondary_color)


def file_stem(species: str, color: str) -> str:
    """文件名前缀：{species_en}_{color_en}，如 rose_red / custom_1a2b3c4d_blue。"""
    return f"{species_en(species)}_{color_en(species, color)}"
