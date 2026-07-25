"""全局常量：Demo 设定、生长节律、订单节奏、互动事件语义、预置花材（API.md v0.2 §0/§1、PRD v0.3）。"""

from pathlib import Path

from app.ai_gateway.catalog import GROWTH_RHYTHM, STAGES

# ---- Demo 固定设定 ----
GARDEN_ID = 1
USER_A = "我"
USER_B = "小葵"
USERS = ("me", "ta")  # user 字段取值仅 "me" | "ta"

# ---- 成长阶段（GROWTH_RHYTHM / STAGES 来自 ai_gateway.catalog；每阶段"每个人"所需资源，无缓冲期） ----
STAGE_NAMES = {
    "seed": "种子",
    "sprout": "萌芽",
    "seedling": "幼苗",
    "bud": "花苞",
    "bloom": "盛放",
}
# 按阶段名索引的需求模板：{"seed": {"stage","water","sunlight","nutrient"}, ...}
STAGE_SPECS = {row["stage"]: row for row in GROWTH_RHYTHM}

# ---- TA 自动照料（API.md §3）：TA 储备达标后延迟自动完成 ----
TA_CARE_DELAY_SECONDS = 8

# ---- 订单节奏（不变）：0–15s accepted / 15–40s making / 40–70s delivering / ≥70s done ----
ORDER_FLOW = [("accepted", 0), ("making", 15), ("delivering", 40), ("done", 70)]
ORDER_STATUS_NAMES = {
    "accepted": "已接单",
    "making": "制作中",
    "delivering": "配送中",
    "done": "已送达",
}
ORDER_TIMELINE_NAMES = [
    ("accepted", "花店已接单"),
    ("making", "花束制作中"),
    ("delivering", "骑手配送中"),
    ("done", "已送达，收到同款鲜花花束"),
]
SHOP_NAME = "春风花店·抖音本地生活（模拟）"

# ---- 模拟互动事件（API.md 1.11）：target=both 双方各得 / alternate 轮流单方 ----
INTERACTION_EVENTS = {
    "mutual_message": {
        "target": "both",
        "delta": {"water": 1},
        "description": "你们今天互相说过话，各获得 1 滴水",
    },
    "share_video": {
        "target": "alternate",
        "delta": {"sunlight": 1},
        "descriptions": {
            "me": "你分享了一条视频，获得 1 缕阳光",
            "ta": "TA 分享了一条视频，TA 获得 1 缕阳光",
        },
    },
    "streak": {
        "target": "both",
        "delta": {"nutrient": 1},
        "description": "你们已连续互动 3 天，各获得 1 份养料",
    },
}

# ---- 送花意图枚举（1.13） ----
OCCASIONS = ["情侣约会", "毕业季", "生日祝福", "探望问候", "日常惊喜"]

# ---- 预置花材（启动播种与 1.15 重置；PRD F8） ----
PRESTOCK_HOUSE = [
    {"species": "玫瑰", "color": "红", "quantity": 2},
    {"species": "洋甘菊", "color": "白", "quantity": 2},
    {"species": "向日葵", "color": "黄", "quantity": 1},
]

# ---- 花园新变化提示（1.12） ----
BADGE_MESSAGE = "花园有新的变化，去看看吧"

# ---- 上传约束与静态目录 ----
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
UPLOADS_DIR = ASSETS_DIR / "uploads"
GEN_DIR = ASSETS_DIR / "gen"
for _d in (ASSETS_DIR, UPLOADS_DIR, GEN_DIR):
    _d.mkdir(parents=True, exist_ok=True)
