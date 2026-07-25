"""ai_gateway 冒烟脚本：在 server/ 下激活 venv 后运行 `python -m app.ai_gateway.smoke`。

覆盖：identify_flower（含确定性校验）→ flower_profile → ensure_stage_images → generate_bouquet。
"""

import io
import random

from PIL import Image, ImageDraw

from .art import GEN_DIR, ensure_stage_images
from .imagegen import BouquetItem, generate_bouquet
from .llm import flower_profile
from .vlm import identify_flower


def _make_test_image(seed: int) -> str:
    """构造一张内容随 seed 变化的测试图，落盘到 assets/uploads/。"""
    rnd = random.Random(seed)
    img = Image.new("RGB", (120, 120), (rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)))
    d = ImageDraw.Draw(img)
    for _ in range(6):  # 随机色块，保证不同 seed 字节不同
        x0, y0 = rnd.randrange(100), rnd.randrange(100)
        d.rectangle([x0, y0, x0 + rnd.randrange(10, 40), y0 + rnd.randrange(10, 40)],
                    fill=(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)))
    path = GEN_DIR.parent / "uploads" / f"smoke_test_{seed}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return str(path)


def main() -> None:
    print("== 1. identify_flower ==")
    results = []
    for seed in (1, 2, 3):
        path = _make_test_image(seed)
        r1 = identify_flower(path)
        r2 = identify_flower(path)  # 同图再识别一次，校验确定性
        assert r1 == r2, f"同一图片两次识别结果不一致: {r1} != {r2}"
        assert 0.85 <= r1.confidence <= 0.97, f"置信度越界: {r1.confidence}"
        results.append(r1)
        print(f"  图{seed}: {r1.species}({r1.main_color}/辅{r1.secondary_color}) 置信度={r1.confidence}")

    print("== 2. flower_profile ==")
    for r in results:
        p = flower_profile(r.species, r.main_color, r.secondary_color)
        stages = [(s.stage, s.water, s.sunlight, s.nutrient, s.buffer_seconds) for s in p.growth_rhythm]
        assert [s[0] for s in stages] == ["seed", "sprout", "seedling", "bud", "bloom"]
        print(f"  {r.species}: {p.science_text}")
        print(f"    growth_rhythm={stages}")

    print("== 3. ensure_stage_images ==")
    for species, color in [("玫瑰", "红"), ("向日葵", "黄"), ("满天星", "紫")]:
        urls = ensure_stage_images(species, color)
        assert set(urls) == {"seed", "sprout", "seedling", "bud", "bloom"}
        for u in urls.values():
            name = u.rsplit("/", 1)[-1]
            assert (GEN_DIR / name).exists(), f"文件不存在: {name}"
        print(f"  {species}({color}): {urls['bloom']}")

    print("== 4. generate_bouquet ==")
    url = generate_bouquet(
        [BouquetItem("玫瑰", "红", 3), BouquetItem("洋甘菊", "白", 3), BouquetItem("满天星", "紫", 2)],
        "smoke_bouquet",
    )
    assert (GEN_DIR / "smoke_bouquet.png").exists()
    print(f"  花束预览: {url}")

    print("\nSMOKE OK ✅")


if __name__ == "__main__":
    main()
