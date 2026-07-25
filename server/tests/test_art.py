"""线稿渲染回归测试（flower-lineart skill 验收清单的机器部分）：

1. 颜色一致：/art/flower/{species}/{color}.png 返回图的主色必须与 URL 色名一致
   —— 防 `.png` 后缀污染色名落哈希随机色的 bug 复发（2026-07-25 生产事故）。
2. 轮廓一致：带 form 的 URL 200 且花型生效；图鉴品种绣球画花球（ball）。
3. 图鉴外品种 + 任意 form 可渲染（取消品种限制后的兜底路径）。
"""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.db import get_db
from app.main import app


@pytest.fixture()
def client(session):
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _dominant_rgb(png: bytes) -> tuple[int, int, int]:
    """取 PNG 非透明像素的平均 RGB（花头主体色）。"""
    img = Image.open(io.BytesIO(png)).convert("RGBA")
    pixels = [(r, g, b) for r, g, b, a in img.getdata() if a > 200]
    assert pixels, "渲染结果没有不透明像素"
    n = len(pixels)
    return (
        sum(p[0] for p in pixels) // n,
        sum(p[1] for p in pixels) // n,
        sum(p[2] for p in pixels) // n,
    )


def test_flower_color_matches_url_red(client):
    """玫瑰/红.png：主色必须是红色系（.png 后缀不得污染色名）。"""
    resp = client.get("/api/v1/art/flower/玫瑰/红.png")
    assert resp.status_code == 200
    r, g, b = _dominant_rgb(resp.content)
    assert r > g + 30 and r > b + 30, f"期望红色系，实际均值 RGB=({r},{g},{b})"


def test_flower_color_matches_url_yellow(client):
    """向日葵/黄.png：主色必须是黄色系。"""
    resp = client.get("/api/v1/art/flower/向日葵/黄.png")
    assert resp.status_code == 200
    r, g, b = _dominant_rgb(resp.content)
    assert r > b + 40 and g > b + 20, f"期望黄色系，实际均值 RGB=({r},{g},{b})"


def test_flower_color_matches_url_white(client):
    """洋甘菊/白.png：主色必须是白色系（RGB 都高且接近）。"""
    resp = client.get("/api/v1/art/flower/洋甘菊/白.png")
    assert resp.status_code == 200
    r, g, b = _dominant_rgb(resp.content)
    assert min(r, g, b) > 150 and abs(r - g) < 40, f"期望白色系，实际均值 RGB=({r},{g},{b})"


def test_hydrangea_ball_form_blue(client):
    """绣球/蓝/ball.png：花球轮廓 + 蓝色系（图鉴新品种）。"""
    resp = client.get("/api/v1/art/flower/绣球/蓝/ball.png")
    assert resp.status_code == 200
    r, g, b = _dominant_rgb(resp.content)
    assert b > r + 15 and b > g + 5, f"期望蓝色系，实际均值 RGB=({r},{g},{b})"


def test_off_catalog_species_with_form(client):
    """图鉴外品种 + 合法 form：渲染 200，色名走通用色表（蓝 → 蓝色系）。"""
    for form in ("rosette", "daisy", "disk", "cup", "lily", "ball", "cluster"):
        resp = client.get(f"/api/v1/art/flower/洋桔梗/蓝/{form}.png")
        assert resp.status_code == 200, f"form={form} 渲染失败"
    r, g, b = _dominant_rgb(client.get("/api/v1/art/flower/洋桔梗/蓝/daisy.png").content)
    assert b > r, f"期望蓝色系，实际均值 RGB=({r},{g},{b})"


def test_stage_routes_with_and_without_form(client):
    """阶段图两种 URL 形态都可渲染；非法阶段 404。"""
    assert client.get("/api/v1/art/stage/玫瑰/红/bloom.png").status_code == 200
    assert client.get("/api/v1/art/stage/绣球/蓝/ball/bloom.png").status_code == 200
    assert client.get("/api/v1/art/stage/玫瑰/红/nope.png").status_code == 404


def test_color_name_normalization(client):
    """色名归一化：尾部「色」字等价于标准色名（蓝色 == 蓝）。"""
    r1 = client.get("/api/v1/art/flower/洋桔梗/蓝.png").content
    r2 = client.get("/api/v1/art/flower/洋桔梗/蓝色.png").content
    assert r1 == r2
