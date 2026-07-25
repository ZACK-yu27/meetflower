"""火山方舟真实模型烟测：VLM 识花 / LLM 科普 / 推荐搭配 / 搭配说明 / 包装建议 / Seedream 花束生图。

用法：server/.venv/Scripts/python scripts/ark_smoke.py
读取 server/.env（AI_PROVIDER=ark + ARK_API_KEY），全部真实调用；任一步失败即非零退出。
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))

from app.ai_gateway import settings  # noqa: E402
from app.ai_gateway.art import stage_image_png  # noqa: E402
from app.ai_gateway.imagegen import BouquetItem, generate_bouquet  # noqa: E402
from app.ai_gateway.llm import arrangement_note, flower_profile, packaging_suggestion, recommend_bouquet  # noqa: E402
from app.ai_gateway.vlm import identify_flower  # noqa: E402

print(f"provider={settings.AI_PROVIDER} chat={settings.ARK_CHAT_MODEL} image={settings.ARK_IMAGE_MODEL}")
assert settings.AI_PROVIDER == "ark", "AI_PROVIDER 不是 ark（检查 server/.env）"

fails = []

# 1) VLM 识花：用 Pillow 生成的向日葵·黄盛放图作输入（写临时文件供 VLM 读取）
bloom_path = ROOT / "server" / "app" / "assets" / "uploads" / "ark_smoke_bloom.png"
bloom_path.parent.mkdir(parents=True, exist_ok=True)
bloom_path.write_bytes(stage_image_png("向日葵", "黄", "bloom"))
t0 = time.time()
vlm = identify_flower(str(bloom_path))
print(f"[1] VLM 识花: {vlm.species}/{vlm.main_color}/辅{vlm.secondary_color} conf={vlm.confidence} ({time.time()-t0:.1f}s)")
if vlm.species != "向日葵":
    fails.append(f"VLM 识别为 {vlm.species}（输入是向日葵绘制图）")

# 2) LLM 科普
t0 = time.time()
profile = flower_profile(vlm.species, vlm.main_color, vlm.secondary_color)
print(f"[2] 科普文案({time.time()-t0:.1f}s): {profile.science_text[:80]}...")
if len(profile.science_text) < 30:
    fails.append("科普文案异常")

# 3) 推荐搭配
t0 = time.time()
rec = recommend_bouquet("情侣约会", [
    {"species": "玫瑰", "color": "红", "quantity": 2},
    {"species": "洋甘菊", "color": "白", "quantity": 2},
])
print(f"[3] 推荐搭配({time.time()-t0:.1f}s): items={rec['items']} bonus={rec['bonus_flower']}")
print(f"    reason: {rec['reason']}")

# 4) 搭配说明 + 包装建议
material = rec["items"] + [rec["bonus_flower"]]
t0 = time.time()
note = arrangement_note(material, "情侣约会")
pack = packaging_suggestion(material, "情侣约会")
print(f"[4] 搭配说明({time.time()-t0:.1f}s): {note}")
print(f"    包装建议: {pack}")

# 5) Seedream 花束生图
t0 = time.time()
items = [BouquetItem(**{k: i[k] for k in ("species", "color", "count")}) for i in material]
data, mime = generate_bouquet(items, "ark_smoke_bouquet")
size = len(data)
print(f"[5] 花束生图({time.time()-t0:.1f}s): mime={mime} ({size//1024} KB)")
if size < 50 * 1024:
    fails.append(f"生图字节异常（{size} bytes）——可能走了 Pillow 降级，查看日志")

print()
print("RESULT:", "ALL PASS" if not fails else f"CHECK: {fails}")
sys.exit(0 if not fails else 1)
