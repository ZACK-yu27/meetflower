"""HTTP 层冒烟测试（TestClient，API.md v0.2）：识花 → 种植 → 互动（双人入账）→ 照料 →
花园聚合 → badge → 推荐/预览/下单 → fast-forward → reset，静态图 URL 可访问，404/422 统一中文 detail。
"""

import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

from conftest import make_image_bytes

PLANT_KEYS = {
    "plant_id", "species", "main_color", "stage", "stage_name", "stage_image",
    "stage_order", "is_bloom", "pressed", "needs", "me", "ta",
    "next_stage_name", "stage_advanced_at",
}


@pytest.fixture()
def client(session):
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:  # 触发 lifespan（播种到 env 指定的临时库，与 session 互不影响）
        yield c
    app.dependency_overrides.clear()


def test_http_smoke(client):
    # 1.1 识花（multipart 上传）
    resp = client.post("/api/v1/recognitions", files={"image": ("flower.png", make_image_bytes(7), "image/png")})
    assert resp.status_code == 200
    rec = resp.json()
    assert set(rec) == {
        "recognition_id", "image_url", "species", "main_color", "secondary_color",
        "confidence", "science_text", "flower_image", "stage_images", "resemble",
    }
    assert rec["resemble"] is None  # 拍照识别无相似属性
    # 静态图 URL 可访问
    assert client.get(rec["image_url"]).status_code == 200
    assert client.get(rec["flower_image"]).status_code == 200
    assert client.get(rec["stage_images"]["bloom"]).status_code == 200

    # 1.1b 轮询端点：GET /api/v1/recognitions/{id} 返回同一结果；未知 id 404
    resp = client.get(f"/api/v1/recognitions/{rec['recognition_id']}")
    assert resp.status_code == 200 and resp.json()["species"] == rec["species"]
    assert resp.json()["science_text"]  # mock 模式科普同步生成
    assert client.get("/api/v1/recognitions/999").status_code == 404

    # 1.2 种植（识花）与复种（品种+颜色）
    resp = client.post("/api/v1/gardens/1/plants", json={"recognition_id": rec["recognition_id"]})
    assert resp.status_code == 200
    plant = resp.json()
    assert set(plant) == PLANT_KEYS
    assert plant["stage"] == "seed" and plant["stage_name"] == "种子"
    assert plant["needs"] == {"water": 2, "sunlight": 0, "nutrient": 0}
    assert plant["me"]["done"] is False and plant["ta"]["done"] is False

    resp = client.post("/api/v1/gardens/1/plants", json={"species": "玫瑰", "main_color": "红"})
    assert resp.status_code == 200
    replant = resp.json()
    assert replant["species"] == "玫瑰" and replant["main_color"] == "红"

    # 1.11 三种模拟互动（双人入账）
    resp = client.post("/api/v1/demo/interactions", json={"kind": "mutual_message"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["resources"]["me"]["water"] == 1 and body["resources"]["ta"]["water"] == 1
    assert body["event"]["delta"] == {"water": 1}
    resp = client.post("/api/v1/demo/interactions", json={"kind": "mutual_message"})
    assert resp.json()["resources"]["me"]["water"] == 2  # 再互发一次凑够 seed 需水 2

    resp = client.post("/api/v1/demo/interactions", json={"kind": "share_video"})
    body = resp.json()
    assert body["resources"]["me"]["sunlight"] == 1 and body["resources"]["ta"]["sunlight"] == 0  # 轮流，首次归 me
    resp = client.post("/api/v1/demo/interactions", json={"kind": "streak"})
    body = resp.json()
    assert body["resources"]["me"]["nutrient"] == 1 and body["resources"]["ta"]["nutrient"] == 1

    # 1.4 照料（整组扣除）
    resp = client.post(f"/api/v1/gardens/1/plants/{plant['plant_id']}/care", json={})
    assert resp.status_code == 200
    care = resp.json()
    assert set(care) == {"applied", "me_done", "ta_done", "stage", "stage_changed", "resources"}
    assert care["applied"] == {"water": 2, "sunlight": 0, "nutrient": 0}
    assert care["me_done"] is True and care["ta_done"] is False
    assert care["stage"] == "seed" and care["stage_changed"] is False
    assert care["resources"]["me"]["water"] == 0

    # 已完成本阶段 → 409
    resp = client.post(f"/api/v1/gardens/1/plants/{plant['plant_id']}/care", json={})
    assert resp.status_code == 409
    assert "已完成本阶段照料" in resp.json()["detail"]

    # 1.3 花园聚合（触发 TA 自动照料评估：ta 水够 → 置 ta_ready_since，未满 8s 未完成）
    resp = client.get("/api/v1/gardens/1")
    assert resp.status_code == 200
    view = resp.json()
    assert view["garden"] == {"garden_id": 1, "user_a": "我", "user_b": "小葵"}
    assert set(view["resources"]) == {"me", "ta"}
    assert len(view["plants"]) == 2 and set(view["plants"][0]) == PLANT_KEYS
    first = next(p for p in view["plants"] if p["plant_id"] == plant["plant_id"])
    assert first["me"]["done"] is True and first["me"]["can_care"] is False
    assert first["ta"]["done"] is False
    assert first["ta"]["sufficient"]["water"] is True  # ta 有 2 水 ≥ 需求 2
    assert len(view["events"]) == 4
    assert set(view["events"][0]) == {"id", "type", "description", "delta", "occurred_at"}

    # 1.12 badge（查看花园后已清除）
    resp = client.get("/api/v1/badge")
    assert resp.status_code == 200
    assert resp.json() == {"has_update": False, "message": "花园有新的变化，去看看吧"}

    # 1.13 AI 推荐搭配（预置库存：玫瑰红×2、洋甘菊白×2、向日葵黄×1）
    resp = client.post("/api/v1/bouquets/recommend", json={"occasion": "情侣约会"})
    assert resp.status_code == 200
    rec_out = resp.json()
    assert set(rec_out) == {"occasion", "items", "bonus_flower", "reason"}
    assert 1 <= len(rec_out["items"]) <= 2
    assert rec_out["bonus_flower"]["gifted"] is True

    # 1.7 预览（含赠送花材）→ 1.8 下单（备注/替代）→ 1.9 详情
    resp = client.post("/api/v1/bouquets/preview", json={
        "items": rec_out["items"],
        "bonus": {k: rec_out["bonus_flower"][k] for k in ("species", "color", "count")},
        "occasion": "情侣约会",
    })
    assert resp.status_code == 200
    preview = resp.json()
    assert preview["status"] == "draft"
    assert preview["material_list"][-1]["gifted"] is True
    assert preview["arrangement_note"] and preview["packaging"]
    assert client.get(preview["preview_url"]).status_code == 200

    # 1.7b 轮询端点：GET /api/v1/bouquets/{id} 返回同一方案；未知 id 404
    resp = client.get(f"/api/v1/bouquets/{preview['bouquet_id']}")
    assert resp.status_code == 200
    polled = resp.json()
    assert polled["preview_url"] == preview["preview_url"]  # mock 模式预览图同步生成
    assert polled["material_list"] == preview["material_list"]
    assert client.get("/api/v1/bouquets/999").status_code == 404

    resp = client.post(f"/api/v1/bouquets/{preview['bouquet_id']}/orders",
                       json={"note": "请下午 5 点后送达", "accept_substitute": False})
    assert resp.status_code == 200
    order = resp.json()
    assert order["status"] == "accepted"
    assert order["shop_name"] == "春风花店·抖音本地生活（模拟）"

    resp = client.get(f"/api/v1/orders/{order['order_id']}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["note"] == "请下午 5 点后送达" and detail["accept_substitute"] is False
    assert [t["reached"] for t in detail["timeline"]] == [True, False, False, False]

    # 1.14 演示快进 → 1.5 压花
    resp = client.post("/api/v1/demo/fast-forward", json={"plant_id": replant["plant_id"]})
    assert resp.status_code == 200
    assert resp.json() == {"plant_id": replant["plant_id"], "stage": "bloom", "stage_name": "盛放"}
    resp = client.post(f"/api/v1/gardens/1/plants/{replant['plant_id']}/press", json={})
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 1  # 推荐已消耗预置玫瑰红×2 → 压花后灰态行 +1

    # 1.6 花房（含 ×0 灰态项：向日葵×1 若被推荐消耗则为 0）
    resp = client.get("/api/v1/flower-house")
    assert resp.status_code == 200
    house = resp.json()["items"]
    assert all(set(i) == {"item_id", "species", "color", "quantity", "flower_image"} for i in house)
    quantities = [i["quantity"] for i in house]
    assert quantities == sorted(quantities, reverse=True)

    # 1.15 演示重置（幂等）
    resp = client.post("/api/v1/demo/reset", json={})
    assert resp.status_code == 200
    reset = resp.json()
    assert reset["ok"] is True
    assert reset["resources"] == {
        "me": {"water": 0, "sunlight": 0, "nutrient": 0},
        "ta": {"water": 0, "sunlight": 0, "nutrient": 0},
    }
    assert {(i["species"], i["color"]): i["quantity"] for i in reset["house"]} == {
        ("玫瑰", "红"): 2, ("洋甘菊", "白"): 2, ("向日葵", "黄"): 1,
    }
    resp = client.post("/api/v1/demo/reset", json={})
    assert resp.status_code == 200 and resp.json()["ok"] is True


def test_http_errors(client):
    # 404 中文 detail
    resp = client.get("/api/v1/orders/999")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "订单不存在"}

    resp = client.post("/api/v1/gardens/1/plants/999/care", json={})
    assert resp.status_code == 404
    assert resp.json() == {"detail": "植株不存在"}

    resp = client.post("/api/v1/gardens/1/plants", json={"recognition_id": 999})
    assert resp.status_code == 404
    assert resp.json() == {"detail": "识花记录不存在"}

    # 409 照料资源缺口（无资源时直接照料新植株）
    resp = client.post("/api/v1/gardens/1/plants", json={"species": "玫瑰", "main_color": "红"})
    plant_id = resp.json()["plant_id"]
    resp = client.post(f"/api/v1/gardens/1/plants/{plant_id}/care", json={})
    assert resp.status_code == 409
    assert resp.json()["detail"] == "还差 2 滴水，去聊天获取吧"

    # 422：互动 kind 枚举
    resp = client.post("/api/v1/demo/interactions", json={"kind": "bogus"})
    assert resp.status_code == 422
    assert isinstance(resp.json()["detail"], str)
    assert resp.json()["detail"].startswith("参数错误")

    # 422：推荐 occasion 枚举
    resp = client.post("/api/v1/bouquets/recommend", json={"occasion": "开业大吉"})
    assert resp.status_code == 422
    assert resp.json()["detail"].startswith("参数错误")

    # 图鉴外品种复种也放行（品种限制已放开）：返回 200
    resp = client.post("/api/v1/gardens/1/plants", json={"species": "绣球", "main_color": "蓝"})
    assert resp.status_code == 200
    assert resp.json()["species"] == "绣球" and resp.json()["main_color"] == "蓝"

    # 422：不支持的图片格式
    resp = client.post("/api/v1/recognitions", files={"image": ("a.gif", b"GIF89a", "image/gif")})
    assert resp.status_code == 422
    assert resp.json() == {"detail": "仅支持 jpg/png 格式的图片"}


def test_resemble_video_mock(client):
    """广义的花（mock 路径，离线确定性）：视频端点 → resemble 属性 → 种入花园。"""
    video_bytes = b"FAKE-MP4-" + bytes(range(256)) * 8  # mock 只按字节哈希，不真正解码
    resp = client.post(
        "/api/v1/recognitions/video",
        files={"video": ("clip.mp4", video_bytes, "video/mp4")},
    )
    assert resp.status_code == 200
    rec = resp.json()
    # resemble 属性齐全（flower_resemble.md §3.1 四字段 + reason）
    attrs = rec["resemble"]
    assert attrs and all(attrs[k] for k in ("subject", "shape", "color", "texture", "reason"))
    assert rec["science_text"]  # mock 科普同步生成
    assert rec["image_url"] == ""  # mock 无封面帧
    assert client.get(rec["stage_images"]["bloom"]).status_code == 200

    # 轮询端点回读同一记录：resemble 持久化
    resp = client.get(f"/api/v1/recognitions/{rec['recognition_id']}")
    assert resp.status_code == 200 and resp.json()["resemble"] == attrs

    # 与拍照识别同一后续流程：可种入花园
    resp = client.post("/api/v1/gardens/1/plants", json={"recognition_id": rec["recognition_id"]})
    assert resp.status_code == 200
    plant = resp.json()
    assert plant["species"] == rec["species"] and plant["main_color"] == rec["main_color"]

    # 同一视频字节 → 查重秒回：直接复用上次识别记录（同一 recognition_id）
    resp2 = client.post(
        "/api/v1/recognitions/video",
        files={"video": ("clip.mp4", video_bytes, "video/mp4")},
    )
    assert resp2.json()["recognition_id"] == rec["recognition_id"]


def test_resemble_video_rejects_bad_input(client):
    """非法视频：格式 422；空内容 422。"""
    resp = client.post(
        "/api/v1/recognitions/video",
        files={"video": ("a.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 422
    assert resp.json() == {"detail": "仅支持 mp4/mov/webm 格式的视频"}

    resp = client.post(
        "/api/v1/recognitions/video",
        files={"video": ("a.mp4", b"", "video/mp4")},
    )
    assert resp.status_code == 422
    assert resp.json() == {"detail": "视频内容为空"}
