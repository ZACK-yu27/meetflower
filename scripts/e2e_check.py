#!/usr/bin/env python
"""抖音花园 MVP 端到端闭环验证脚本（docs/API.md v0.2 全链路）。

链路：1.12 badge 健康检查 → 1.1 识花 → 1.2 种植（含图鉴外品种复种）→ 1.4 缺口 409 负向
     → 1.11 互动双人入账语义（互发消息双方水+1 / 分享视频轮流单方光+1 / 连续互动双方养+1）
     → 完整一级真实双人照料（我整组扣除 care → 已完成 409 → 等 TA 8s 自动照料 → 双方齐升级，验证 badge）
     → 1.14 fast-forward 直升 bloom（查看完整成长旅程）→ 1.5 压花 → 1.6 花房
     → 1.7 自由搭配预览（不扣库存 / 库存不足 409 / suggestion）→ 1.8 下单消耗到 ×0 灰态
     → 1.2 复种（{species, main_color}）→ 1.13 AI 推荐（含 422 负向）→ 1.7 预览（bonus 赠送 + occasion）
     → 1.8 下单（note/accept_substitute，gifted 不扣库存）→ 1.9/1.10 订单惰性推进到 done
     → 1.15 demo/reset 幂等 + 预置花材 + 清空重播种。

前置：后端已启动（cd server && uvicorn app.main:app --port 8000），且数据库为干净播种状态。
运行：server/.venv/Scripts/python scripts/e2e_check.py（依赖 httpx + Pillow，均在 server venv 中）。
退出码：全部通过 0；任一步骤失败非零。真实等待 ≈ TA 8s + 订单 70s，总时长 ≤ 4 分钟。
"""

from __future__ import annotations

import io
import sys
import time

import httpx
from PIL import Image, ImageDraw

# Windows 控制台/重定向下强制 UTF-8 输出，避免中文日志乱码
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure") and (_stream.encoding or "").lower() != "utf-8":
        _stream.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000"
TA_DELAY_S = 8          # config.TA_CARE_DELAY_SECONDS：TA 储备达标后自动照料延迟
ORDER_DEADLINE_S = 100  # 订单 70s 后 done，留余量
TOTAL_DEADLINE_S = 240  # 全程硬上限 4 分钟

RESOURCES = ("water", "sunlight", "nutrient")
# API.md §0 生长节律（向日葵示例值，每阶段"每个人"所需资源）
STAGE_NEEDS = {
    "seed": {"water": 2, "sunlight": 0, "nutrient": 0},
    "sprout": {"water": 3, "sunlight": 1, "nutrient": 0},
}
# 预置花材（API.md 1.15 / config.PRESTOCK_HOUSE）
PRESTOCK = {("玫瑰", "红"): 2, ("洋甘菊", "白"): 2, ("向日葵", "黄"): 1}
ZERO_TARGET = ("向日葵", "黄")  # ×0 灰态 + 复种的目标花材（预置量 1，可能被压花 +1）

_step = 0


def log(msg: str) -> None:
    print(f"        {msg}", flush=True)


def step(title: str) -> None:
    global _step
    _step += 1
    print(f"\n[STEP {_step:02d}] {title}", flush=True)


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    log(f"OK  {msg}")


def must(resp: httpx.Response, what: str) -> dict:
    if resp.status_code != 200:
        raise AssertionError(f"{what} 失败：HTTP {resp.status_code} {resp.text[:200]}")
    return resp.json()


def make_flower_png(petal_hex: str, center_hex: str) -> bytes:
    """Pillow 现造一张简单花图（PNG 字节）。"""
    import math

    img = Image.new("RGB", (220, 220), "#FBF6EC")
    d = ImageDraw.Draw(img)
    cx, cy = 110, 105
    d.line([cx, cy + 30, cx, 200], fill="#4E8A3C", width=6)  # 茎
    for k in range(8):  # 8 瓣
        a = math.radians(k * 45)
        px, py = cx + 52 * math.cos(a), cy + 52 * math.sin(a)
        d.ellipse([px - 26, py - 26, px + 26, py + 26], fill=petal_hex)
    d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=center_hex)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def get_garden(client: httpx.Client) -> dict:
    return must(client.get("/api/v1/gardens/1"), "1.3 花园聚合视图")


def get_house(client: httpx.Client) -> dict:
    return must(client.get("/api/v1/flower-house"), "1.6 花房库存")


def house_qty(house: dict) -> dict[tuple[str, str], int]:
    """{(species, color): quantity}，含 quantity=0 灰态项。"""
    return {(i["species"], i["color"]): i["quantity"] for i in house["items"]}


def interact(client: httpx.Client, kind: str) -> dict:
    return must(client.post("/api/v1/demo/interactions", json={"kind": kind}), f"1.11 互动 {kind}")


def check_static(client: httpx.Client, url: str, what: str) -> None:
    resp = client.get(url)
    check(resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/")
          and len(resp.content) > 500, f"{what} 可经 /static 访问（{url}）")


def main() -> int:
    started = time.monotonic()
    try:
        with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
            # ---------- 健康检查 ----------
            step("健康检查：GET /api/v1/badge（1.12）")
            badge = must(client.get("/api/v1/badge"), "badge")
            check("has_update" in badge and "message" in badge, f"badge 字段齐全：{badge}")

            # ---------- 识花 ----------
            step("识花：POST /api/v1/recognitions（1.1，Pillow 现造花图）")
            resp = client.post("/api/v1/recognitions",
                               files={"image": ("e2e_flower.png", make_flower_png("#D2364C", "#F2C230"), "image/png")})
            rec = must(resp, "1.1 识花")
            check(bool(rec["recognition_id"]) and bool(rec["species"]),
                  f"识别结果 #{rec['recognition_id']}：{rec['species']}（{rec['main_color']}）置信度 {rec['confidence']}")
            check(set(rec["stage_images"]) == {"seed", "sprout", "seedling", "bud", "bloom"},
                  "预生成 5 阶段资产齐全")
            check_static(client, rec["image_url"], "上传图")
            check_static(client, rec["stage_images"]["bloom"], "盛放阶段图")

            # ---------- 种植（含选择花园语义：固定进入共同花园 garden 1） ----------
            step("种植：POST /api/v1/gardens/1/plants（1.2，识花种植，进入共同花园）")
            plant = must(client.post("/api/v1/gardens/1/plants",
                                     json={"recognition_id": rec["recognition_id"]}), "1.2 种植")
            pid = plant["plant_id"]
            check(plant["stage"] == "seed" and plant["stage_name"] == "种子" and plant["stage_order"] == 0,
                  f"植株 #{pid} 已种进共同花园（{plant['species']}·{plant['main_color']}，stage=seed）")
            check(plant["me"]["done"] is False and plant["ta"]["done"] is False
                  and plant["needs"] == STAGE_NEEDS["seed"],
                  "初始双方均未照料，needs=种子阶段需求（水2/光0/养0）")
            free = must(client.post("/api/v1/gardens/1/plants",
                                    json={"species": "绣球", "main_color": "蓝"}), "1.2 图鉴外品种复种")
            check(free["stage"] == "seed" and free["species"] == "绣球" and free["main_color"] == "蓝",
                  f"图鉴外品种复种成功（品种限制已放开）：{free['species']}·{free['main_color']}，从种子阶段开始")
            view = get_garden(client)
            check(any(p["plant_id"] == pid for p in view["plants"]),
                  "聚合视图 plants[] 可见新植株（选择花园后落位 garden 1）")

            # ---------- 缺口 409 负向 ----------
            step("照料负向：资源缺口 409（1.4）")
            resp = client.post(f"/api/v1/gardens/1/plants/{pid}/care", json={})
            check(resp.status_code == 409 and "还差 2 滴水" in resp.json().get("detail", ""),
                  f"零资源照料被拒：409 {resp.json()['detail']}")

            # ---------- 互动双人入账语义 ----------
            step("模拟互动：POST /api/v1/demo/interactions（1.11，验证双人入账语义）")
            r = interact(client, "mutual_message")
            check(r["resources"]["me"]["water"] == 1 and r["resources"]["ta"]["water"] == 1
                  and r["event"]["delta"] == {"water": 1},
                  "互发消息：me/ta 各 水滴+1（双人账户同时入账）")
            resp = client.post(f"/api/v1/gardens/1/plants/{pid}/care", json={})
            check(resp.status_code == 409 and "还差 1 滴水" in resp.json().get("detail", ""),
                  f"半缺口照料被拒：409 {resp.json()['detail']}")
            r = interact(client, "mutual_message")  # 此刻 ta 储备达标（水2），TA 计时从此开始
            t_ta_ready = time.monotonic()
            check(r["resources"]["me"]["water"] == 2 and r["resources"]["ta"]["water"] == 2,
                  "再次互发消息：双方水=2，me 达标、ta 亦达标（TA 自动照料开始计时）")
            r1 = interact(client, "share_video")
            check(r1["resources"]["me"]["sunlight"] == 1 and r1["resources"]["ta"]["sunlight"] == 0
                  and "你分享了" in r1["event"]["description"],
                  f"分享视频（第 1 次）：仅我 阳光+1（{r1['event']['description']}）")
            r2 = interact(client, "share_video")
            check(r2["resources"]["me"]["sunlight"] == 1 and r2["resources"]["ta"]["sunlight"] == 1
                  and "TA 分享了" in r2["event"]["description"],
                  f"分享视频（第 2 次）：轮流至 TA 单方 阳光+1（{r2['event']['description']}）")
            r = interact(client, "streak")
            check(r["resources"]["me"]["nutrient"] == 1 and r["resources"]["ta"]["nutrient"] == 1
                  and r["event"]["delta"] == {"nutrient": 1},
                  "连续互动：me/ta 各 养料+1")

            # ---------- 完整一级真实双人照料 ----------
            step("双人照料（一级真实链路）：我 care → 整组扣除 + 已完成 409（1.4）")
            care = must(client.post(f"/api/v1/gardens/1/plants/{pid}/care", json={}), "1.4 照料")
            check(care["applied"] == STAGE_NEEDS["seed"] and care["me_done"] is True
                  and care["ta_done"] is False and care["stage_changed"] is False,
                  f"整组扣除 applied={care['applied']}，me_done=True / ta_done=False，暂未升级")
            check(care["resources"]["me"] == {"water": 0, "sunlight": 1, "nutrient": 1}
                  and care["resources"]["ta"]["water"] == 2,
                  "我的账户按需求整组扣除（水2→0，光/养不动），TA 账户不受影响")
            resp = client.post(f"/api/v1/gardens/1/plants/{pid}/care", json={})
            check(resp.status_code == 409 and "已完成本阶段照料" in resp.json().get("detail", ""),
                  f"重复照料被拒：409 {resp.json()['detail']}")

            step("双人照料（续）：等 TA 8s 自动照料 → 双方齐升级（1.3 惰性评估 + 1.12 badge）")
            wait_s = TA_DELAY_S + 1.0 - (time.monotonic() - t_ta_ready)
            if wait_s > 0:
                log(f"等待 TA 自动照料计时（{wait_s:.1f}s）…")
                time.sleep(wait_s)
            interact(client, "mutual_message")  # 触发一次惰性评估（互动不清除 badge）
            badge = must(client.get("/api/v1/badge"), "badge")
            check(badge["has_update"] is True, "升级已置 badge：花园有新的变化")
            view = get_garden(client)
            grown = next(p for p in view["plants"] if p["plant_id"] == pid)
            check(grown["stage"] == "sprout" and grown["stage_order"] == 1
                  and grown["stage_name"] == "萌芽",
                  f"双方齐 → 升级：seed → sprout（TA 8s 延迟自动照料生效）")
            check(grown["stage_advanced_at"] is not None,
                  f"stage_advanced_at 已写入（{grown['stage_advanced_at']}）")
            check(grown["me"]["done"] is False and grown["ta"]["done"] is False
                  and grown["needs"] == STAGE_NEEDS["sprout"],
                  "新阶段双方标记已重置，needs=萌芽阶段需求（水3/光1/养0）")
            badge = must(client.get("/api/v1/badge"), "badge")
            check(badge["has_update"] is False, "查看花园后 badge 已清除")

            # ---------- fast-forward 查看完整成长旅程 ----------
            step("演示快进：POST /api/v1/demo/fast-forward（1.14，直升盛放）")
            ff = must(client.post("/api/v1/demo/fast-forward", json={"plant_id": pid}), "1.14 快进")
            check(ff["stage"] == "bloom" and ff["stage_name"] == "盛放",
                  f"植株 #{pid} 直升盛放（查看完整成长旅程）")
            view = get_garden(client)
            bloomed = next(p for p in view["plants"] if p["plant_id"] == pid)
            check(bloomed["is_bloom"] is True and bloomed["needs"] == {"water": 0, "sunlight": 0, "nutrient": 0}
                  and bloomed["next_stage_name"] is None and bloomed["me"]["can_care"] is False,
                  "bloom 终态：needs 全 0、无下一阶段、不可再照料")
            resp = client.post("/api/v1/demo/fast-forward", json={"plant_id": pid})
            check(resp.status_code == 409, f"重复快进被拒：409 {resp.json().get('detail', '')}")

            # ---------- 压花收藏 → 花房 +1 ----------
            step("压花收藏：POST /api/v1/gardens/1/plants/{id}/press（1.5）")
            pre_qty = house_qty(get_house(client))
            key = (bloomed["species"], bloomed["main_color"])
            pressed = must(client.post(f"/api/v1/gardens/1/plants/{pid}/press", json={}), "1.5 压花")
            check(pressed["quantity"] == pre_qty.get(key, 0) + 1,
                  f"花房「{pressed['species']}（{pressed['color']}）」数量 {pre_qty.get(key, 0)} → {pressed['quantity']}（+1）")
            resp = client.post(f"/api/v1/gardens/1/plants/{pid}/press", json={})
            check(resp.status_code == 409, f"重复压花被拒：409 {resp.json().get('detail', '')}")
            view = get_garden(client)
            check(next(p for p in view["plants"] if p["plant_id"] == pid)["pressed"] is True,
                  "聚合视图中植株 pressed=true（仍返回，前端不入场景）")

            # ---------- 自由搭配预览（不扣库存 / 库存不足 409 / suggestion） ----------
            step("花束预览：POST /api/v1/bouquets/preview（1.7 自由搭配，三色触发 suggestion）")
            cur = house_qty(get_house(client))
            zero_have = cur[ZERO_TARGET]
            items = [
                {"species": "玫瑰", "color": "红", "count": 1},
                {"species": "洋甘菊", "color": "白", "count": 1},
                {"species": ZERO_TARGET[0], "color": ZERO_TARGET[1], "count": zero_have},
            ]
            over = {"species": ZERO_TARGET[0], "color": ZERO_TARGET[1], "count": zero_have + 1}
            resp = client.post("/api/v1/bouquets/preview", json={"items": [over]})
            check(resp.status_code == 409 and "库存不足" in resp.json().get("detail", ""),
                  f"自由搭配超量被拒：409 {resp.json()['detail']}")
            pre_qty = house_qty(get_house(client))
            bq1 = must(client.post("/api/v1/bouquets/preview", json={"items": items}), "1.7 预览")
            check(bq1["status"] == "draft" and bq1["bouquet_id"] > 0,
                  f"方案 #{bq1['bouquet_id']} 已保存（draft），花材 {bq1['material_list']}")
            check(bq1["suggestion"] is not None, f"主色 >2 种给出轻量建议：{bq1['suggestion']}")
            check(bq1["arrangement_note"] and bq1["packaging"],
                  "搭配说明与包装建议均已生成")
            check_static(client, bq1["preview_url"], "花束预览图")
            check(house_qty(get_house(client)) == pre_qty, "预览未扣减库存（前后一致）")

            # ---------- 下单消耗到 ×0 灰态 ----------
            step("发送花店：POST /api/v1/bouquets/{id}/orders（1.8，消耗至 ×0 灰态）")
            order1 = must(client.post(f"/api/v1/bouquets/{bq1['bouquet_id']}/orders", json={}), "1.8 下单")
            check(order1["status"] == "accepted" and "春风花店" in order1["shop_name"],
                  f"订单 #{order1['order_id']} 已创建（{order1['shop_name']}，accepted）")
            house = get_house(client)
            cur = house_qty(house)
            check(cur[ZERO_TARGET] == 0, f"「{ZERO_TARGET[0]}（{ZERO_TARGET[1]}）」已消耗到 ×0")
            gray = next(i for i in house["items"]
                        if i["species"] == ZERO_TARGET[0] and i["color"] == ZERO_TARGET[1])
            check(gray["quantity"] == 0 and gray["flower_image"],
                  "花房仍返回 quantity=0 灰态项（含 flower_image，可重新种植）")
            check(cur[("玫瑰", "红")] == pre_qty[("玫瑰", "红")] - 1
                  and cur[("洋甘菊", "白")] == pre_qty[("洋甘菊", "白")] - 1,
                  "其余花材各扣 1（玫瑰红 / 洋甘菊白）")
            resp = client.post(f"/api/v1/bouquets/{bq1['bouquet_id']}/orders", json={})
            check(resp.status_code == 409, "重复下单被拒：409（方案已 sent）")

            # ---------- 复种 ----------
            step("复种：POST /api/v1/gardens/1/plants（1.2，×0 灰卡「重新种植」语义）")
            replant = must(client.post("/api/v1/gardens/1/plants",
                                       json={"species": ZERO_TARGET[0], "main_color": ZERO_TARGET[1]}), "1.2 复种")
            check(replant["stage"] == "seed" and replant["stage_name"] == "种子"
                  and replant["species"] == ZERO_TARGET[0] and replant["main_color"] == ZERO_TARGET[1],
                  f"复种成功：新植株 #{replant['plant_id']} 从花种阶段开始（{ZERO_TARGET[0]}·{ZERO_TARGET[1]}）")

            # ---------- AI 推荐搭配 ----------
            step("AI 推荐搭配：POST /api/v1/bouquets/recommend（1.13，含 422 负向）")
            rec_bq = must(client.post("/api/v1/bouquets/recommend", json={"occasion": "情侣约会"}), "1.13 推荐")
            bonus = rec_bq["bonus_flower"]
            check(1 <= len(rec_bq["items"]) <= 2 and bonus.get("gifted") is True
                  and (bonus["species"], bonus["color"]) not in
                  {(i["species"], i["color"]) for i in rec_bq["items"]},
                  f"意图「情侣约会」→ 组合 {rec_bq['items']} + 赠送 {bonus['color']}{bonus['species']}×{bonus['count']}")
            check(bool(rec_bq["reason"]), f"推荐理由：{rec_bq['reason']}")
            resp = client.post("/api/v1/bouquets/recommend", json={"occasion": "随便送送"})
            check(resp.status_code == 422, "未知送花意图被拒：422")

            # ---------- 预览（bonus 赠送 + occasion，不扣库存） ----------
            step("花束预览：1.7 推荐链路（bonus 赠送花材 + occasion）")
            pre_qty = house_qty(get_house(client))
            bq2 = must(client.post("/api/v1/bouquets/preview", json={
                "items": rec_bq["items"],
                "bonus": {"species": bonus["species"], "color": bonus["color"], "count": bonus["count"]},
                "occasion": "情侣约会",
            }), "1.7 预览（含 bonus）")
            gifted = [m for m in bq2["material_list"] if m.get("gifted")]
            check(len(gifted) == 1 and gifted[0]["species"] == bonus["species"],
                  f"material_list 含赠送标记项：{gifted}")
            check(bq2["arrangement_note"] and "情侣约会" in bq2["arrangement_note"],
                  f"搭配说明贴合意图：{bq2['arrangement_note']}")
            check(bool(bq2["packaging"]), f"包装建议：{bq2['packaging']}")
            check(house_qty(get_house(client)) == pre_qty, "预览未扣减库存（含赠送项，前后一致）")

            # ---------- 下单（note/accept_substitute，gifted 不扣库存） ----------
            step("发送花店：1.8 下单（note + accept_substitute，gifted 不扣库存）")
            order2 = must(client.post(f"/api/v1/bouquets/{bq2['bouquet_id']}/orders",
                                      json={"note": "请下午 5 点后送达", "accept_substitute": False}), "1.8 下单")
            check(order2["status"] == "accepted", f"订单 #{order2['order_id']} 已创建（含备注/不接受替代）")
            post_qty = house_qty(get_house(client))
            charged = {(i["species"], i["color"]): i["count"] for i in rec_bq["items"]}
            mismatches = [
                f"{k}: {pre_qty.get(k, 0)} → {post_qty.get(k, 0)}（应扣 {charged.get(k, 0)}）"
                for k in set(pre_qty) | set(post_qty)
                if post_qty.get(k, 0) != pre_qty.get(k, 0) - charged.get(k, 0)
            ]
            check(not mismatches, f"库存扣减精确：收费花材各扣对应数量、赠送花材不动（{charged}）")

            # ---------- 订单惰性推进 ----------
            step("订单流转：轮询 GET /api/v1/orders/{id}（1.9）直到两单均 done")
            seen: dict[int, list[str]] = {order1["order_id"]: [], order2["order_id"]: []}
            deadline = time.monotonic() + ORDER_DEADLINE_S
            while True:
                details = {}
                for oid in seen:
                    detail = must(client.get(f"/api/v1/orders/{oid}"), "1.9 订单详情")
                    details[oid] = detail
                    if detail["status"] not in seen[oid]:
                        seen[oid].append(detail["status"])
                        log(f"订单 #{oid} 状态推进：{' → '.join(seen[oid])}（{detail['status_name']}）")
                if all(d["status"] == "done" for d in details.values()):
                    break
                if time.monotonic() > deadline:
                    raise AssertionError(f"订单超时（>{ORDER_DEADLINE_S}s）未到 done：{seen}")
                time.sleep(4)
            d2 = details[order2["order_id"]]
            check([n["status"] for n in d2["timeline"]] == ["accepted", "making", "delivering", "done"]
                  and all(n["reached"] for n in d2["timeline"]), "timeline 四节点全部 reached=true")
            check(d2["note"] == "请下午 5 点后送达" and d2["accept_substitute"] is False,
                  "订单备注与替代选项已落库并随详情返回")
            check(any(m.get("gifted") for m in d2["material_list"]),
                  "订单 material_list 保留 gifted 赠送标记")
            check(seen[order1["order_id"]][0] == "accepted" and seen[order2["order_id"]][0] == "accepted",
                  "两单均从 accepted 起步，惰性流转完整")
            orders = must(client.get("/api/v1/orders"), "1.10 订单列表")
            check({o["order_id"] for o in orders["orders"]} >= set(seen),
                  f"订单列表包含两单（共 {len(orders['orders'])} 单）")

            # ---------- 演示重置（幂等） ----------
            step("演示重置：POST /api/v1/demo/reset（1.15，连调两次验证幂等）")
            r1 = must(client.post("/api/v1/demo/reset", json={}), "1.15 重置 #1")
            r2 = must(client.post("/api/v1/demo/reset", json={}), "1.15 重置 #2")
            snap = lambda r: (sorted((i["species"], i["color"], i["quantity"]) for i in r["house"]),
                              r["resources"])
            check(snap(r1) == snap(r2), "两次重置结果一致（幂等）")
            check({(i["species"], i["color"]): i["quantity"] for i in r2["house"]} == PRESTOCK,
                  f"预置花材已重播种：{PRESTOCK}")
            check(r2["resources"]["me"] == {"water": 0, "sunlight": 0, "nutrient": 0}
                  and r2["resources"]["ta"] == {"water": 0, "sunlight": 0, "nutrient": 0},
                  "双方资源账户归零")
            view = get_garden(client)
            check(view["plants"] == [] and view["events"] == [],
                  "plants/events 已清空（accounts 重播种、花园干净）")
            badge = must(client.get("/api/v1/badge"), "badge")
            check(badge["has_update"] is False, "badge 复位")

            if time.monotonic() - started > TOTAL_DEADLINE_S:
                raise AssertionError(f"全程超时（>{TOTAL_DEADLINE_S}s）")

        elapsed = time.monotonic() - started
        print(f"\n===== E2E PASS：全部 {_step} 步通过，耗时 {elapsed:.1f}s =====")
        return 0
    except (AssertionError, httpx.HTTPError) as exc:
        print(f"\n[FAIL] STEP {_step:02d} 失败：{exc}", file=sys.stderr)
        print(f"===== E2E FAIL（耗时 {time.monotonic() - started:.1f}s）=====", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
