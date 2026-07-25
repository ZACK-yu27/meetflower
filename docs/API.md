# 抖音花园 MVP — 接口文档（API & 内部契约）

> 版本：v0.2（2026-07-25）｜ 与 `docs/PRD.md`（v0.3）配套，为前后端与 AI Gateway 的唯一开发契约。
> 变更摘要（v0.1 → v0.2）：资源账户加用户维度（me/ta）；照料改为整组扣除 + 双人各完成一次，删除缓冲期与渐进进度；阶段数值按向日葵示例；新增仿聊天页互动语义、TA 自动照料、复种、AI 推荐搭配、赠送花材、包装建议/备注/替代选项、demo fast-forward 与 reset；花房返回 ×0 灰态项。
> 未标注说明时，所有响应 `Content-Type: application/json`；时间均为 ISO 8601 字符串。

## 0. 通用约定

- 后端：FastAPI，监听 `http://localhost:8000`；开发期 CORS 全开。
- 前端：Vite dev server `http://localhost:5173`，代理 `/api` → `http://localhost:8000`；前端一律使用相对路径请求。
- **多用户隔离（v0.3）**：前端在 localStorage 保存匿名 UUID，所有请求带 `X-Session-Id` 头；后端按 Session 映射独立花园（首次访问自动创建并播种，`GET /api/v1/me/garden` 返回当前会话花园）。未带头的请求回落到启动播种的默认花园 `garden_id = 1`。
- 图片访问：上传原图与花束预览图存 Postgres `images` 表，经 `GET /api/v1/images/{id}` 读取；阶段图/花朵特写为确定性 Pillow 资产，经 `GET /api/v1/art/stage/{species}/{color}/{stage}.png` 与 `GET /api/v1/art/flower/{species}/{color}.png` 动态渲染（不落盘不入库）。
- 错误响应统一：`{ "detail": "人类可读的中文错误信息" }`；库存/状态冲突 409，不存在 404，参数错误 422。
- Demo 固定：每个花园内 user_a「我」= me，user_b「小葵」= ta。`user` 字段取值仅 `"me" | "ta"`。
- 成长阶段：`seed(种子) → sprout(萌芽) → seedling(幼苗) → bud(花苞) → bloom(盛放)`；`stage_order`：0–4。
- **生长节律（GROWTH_RHYTHM，向日葵示例值，每阶段"每个人"所需资源，无缓冲期）**：
  | 阶段 | 水滴 | 阳光 | 养料 |
  |---|---|---|---|
  | seed | 2 | 0 | 0 |
  | sprout | 3 | 1 | 0 |
  | seedling | 4 | 2 | 2 |
  | bud | 5 | 3 | 3 |
  | bloom | — | — | — |

## 1. REST API

### 1.1 识花 `POST /api/v1/recognitions`
- 请求：`multipart/form-data`，字段 `image`（jpg/png，≤10MB）。
- 响应 200：`{ recognition_id, image_url, species, main_color, secondary_color, confidence, science_text, flower_image, stage_images: {seed, sprout, seedling, bud, bloom}, resemble: null }`。
- **科普文案异步补齐**（ark 模式）：首响只做 VLM 识别 + 资产生成，`science_text` 为 `""`；科普由后台任务撰写（约 15–20s）并回写，前端经 `GET /api/v1/recognitions/{id}` 轮询（建议 2s 间隔），`science_text` 非空即就绪。mock 模式科普瞬时生成、同步返回。
- 识花结果查询 `GET /api/v1/recognitions/{id}`：响应同 POST；未知 id 404「识花记录不存在」。

### 1.1c 广义的"花"（视频识花） `POST /api/v1/recognitions/video`（v0.4 新增）
- 规则文档：`docs/flower_resemble.md`（两段式：VLM 抽视频主体属性 → LLM 检索最相似花卉）。
- 请求：`multipart/form-data`，字段 `video`（mp4/mov/webm，≤30MB）。抽帧规则：每 3 秒 1 帧、最多 4 帧、宽 320px JPEG（首帧入库作封面 `image_url`；mock 路径无封面、为空串）。同一花园重复上传同字节视频直接复用上次结果。
- 响应 200：schema 同 1.1，其中 `resemble` 非空：`{ subject, shape, color, texture, reason }`（视频主体形态/颜色/质感 + 相似理由；拍照识别该字段为 `null`，前端不渲染）。
- 422：「仅支持 mp4/mov/webm 格式的视频」「视频内容为空」「视频大小不能超过 30MB」「视频无法解析，换一个试试」。
- 后续流程与 1.1 完全一致：同一 Recognition 表、同一种植/轮询/科普异步补齐。


### 1.2 种植 / 复种 `POST /api/v1/gardens/1/plants`
- 请求（二选一）：
  - 识花种植：`{ "recognition_id": 1 }`
  - 复种（×0 灰卡「重新种植」）：`{ "species": "玫瑰", "main_color": "红" }`（品种/颜色不限于图鉴，图鉴外品种由通用画法 + 颜色表/哈希兜底生成视觉资产；视觉资产走 catalog + ensure_stage_images 复用）
- 处理：创建植株（stage=seed），品种与颜色自此锁定。
- 响应 200：Plant 对象（结构同 1.3 `plants[]` 元素，此时双方均未照料）。

### 1.3 花园聚合视图 `GET /api/v1/gardens/1`
- 处理：先执行 **TA 自动照料评估**（见 §3）与升级检查；随后返回并清除 badge。
- 响应 200：
```json
{
  "garden": { "garden_id": 1, "user_a": "我", "user_b": "小葵" },
  "resources": {
    "me": { "water": 5, "sunlight": 2, "nutrient": 1 },
    "ta": { "water": 4, "sunlight": 0, "nutrient": 1 }
  },
  "plants": [
    {
      "plant_id": 1,
      "species": "向日葵",
      "main_color": "黄",
      "stage": "sprout",
      "stage_name": "萌芽",
      "stage_image": "/api/v1/art/stage/%E5%90%91%E6%97%A5%E8%91%B5/%E9%BB%84/sprout.png",
      "stage_order": 1,
      "is_bloom": false,
      "pressed": false,
      "needs": { "water": 3, "sunlight": 1, "nutrient": 0 },
      "me":  { "done": false, "sufficient": { "water": true,  "sunlight": true,  "nutrient": true }, "can_care": true },
      "ta":  { "done": false, "sufficient": { "water": true,  "sunlight": false, "nutrient": true } },
      "next_stage_name": "幼苗",
      "stage_advanced_at": "2026-07-25T10:00:00"
    }
  ],
  "events": [
    { "id": 8, "type": "mutual_message", "description": "你们今天互相说过话，各获得 1 滴水", "delta": { "water": 1 }, "occurred_at": "2026-07-25T09:58:11" }
  ]
}
```
- `needs` = 当前阶段"每个人"所需资源（bloom 植株为全 0）；`sufficient` = 对应用户的储备是否 ≥ 单项需求（nutrient 需求为 0 时该项恒 true）；`can_care` = 我未完成 且 我全部 sufficient 且 非 bloom 且 未 pressed。
- `events` 按时间倒序 ≤20 条；`pressed=true` 植株仍返回（前端不入场景）。

### 1.4 照料 `POST /api/v1/gardens/1/plants/1/care`
- 请求：`{}`
- 处理（单事务）：校验（bloom/pressed → 409；我已完成本阶段 → 409「你已完成本阶段照料，等 TA 完成后花朵就会成长」；资源不足 → 409「还差 2 滴水、1 缕阳光，去聊天获取吧」按实际缺口拼接）→ **整组扣除**我的当前阶段需求资源 → 记录 `plant_cares(plant_id, stage, "me")` → 若 TA 也已完成 → 升阶段（重置本阶段双方标记、写 `stage_advanced_at`、置 badge）。
- 响应 200：
```json
{
  "applied": { "water": 3, "sunlight": 1, "nutrient": 0 },
  "me_done": true,
  "ta_done": false,
  "stage": "sprout",
  "stage_changed": false,
  "resources": { "me": { "water": 2, "sunlight": 1, "nutrient": 1 }, "ta": { "water": 4, "sunlight": 0, "nutrient": 1 } }
}
```

### 1.5 压花收藏 `POST /api/v1/gardens/1/plants/1/press`（同 v0.1）
- 前置：stage=bloom 且未 pressed，否则 409。house_items 按 (garden_id, species, color) upsert 数量 +1；植株标记 pressed。
- 响应 200：`{ "item_id": 1, "species": "玫瑰", "color": "红", "quantity": 2 }`

### 1.6 花房库存 `GET /api/v1/flower-house`
- 响应 200（**含 quantity=0 的灰态项**，按 quantity 降序、再按品种排序）：
```json
{
  "items": [
    { "item_id": 1, "species": "玫瑰", "color": "红", "quantity": 2, "flower_image": "/api/v1/art/flower/%E7%8E%AB%E7%91%B0/%E7%BA%A2.png" },
    { "item_id": 3, "species": "向日葵", "color": "黄", "quantity": 0, "flower_image": "/api/v1/art/flower/%E5%90%91%E6%97%A5%E8%91%B5/%E9%BB%84.png" }
  ]
}
```

### 1.7 花束预览 `POST /api/v1/bouquets/preview`
- 请求：
```json
{
  "items": [ { "species": "玫瑰", "color": "红", "count": 2 } ],
  "bonus": { "species": "满天星", "color": "白", "count": 1 },
  "occasion": "情侣约会"
}
```
- `bonus`（可空）= 推荐链路赠送的花材（来自 1.13 的 bonus_flower）；`occasion`（可空）用于生成搭配说明与包装建议。
- 处理：items 库存快照校验（不足 409「玫瑰(红) 库存不足：需要 3，现有 2」；bonus 不校验）→ 生图（bonus 参与合成）→ 保存方案（draft，items_json 中 bonus 项标 `gifted: true`）。**不扣减库存。**
- **预览图异步补齐**（ark 模式）：首响只并行生成搭配说明/包装建议（约 10–30s），`preview_url` 为 `null`；预览图由后台任务生成（Seedream 约 45–60s，超时自动降级 Pillow 合成）并回写，前端经 `GET /api/v1/bouquets/{id}` 轮询（建议 3s 间隔），`preview_url` 非空即就绪。mock 模式生图瞬时、同步返回。
- 花束方案查询 `GET /api/v1/bouquets/{id}`：响应同 POST；未知 id 404「花束方案不存在」。
- 响应 200：
```json
{
  "bouquet_id": 1,
  "preview_url": "/api/v1/images/2",
  "material_list": [
    { "species": "玫瑰", "color": "红", "count": 2 },
    { "species": "满天星", "color": "白", "count": 1, "gifted": true }
  ],
  "arrangement_note": "红玫瑰象征热烈的爱意，满天星作点缀增添浪漫层次，适合情侣约会。",
  "packaging": "建议奶白色雾面纸包裹，配浅粉丝带，突出红玫瑰的热烈。",
  "suggestion": null,
  "status": "draft"
}
```
- `suggestion`：轻量建议（组合主色 >2 种时给出，如「主色较多，可减少一种主色，花束会更柔和」；否则 null）。

### 1.8 发送花店 `POST /api/v1/bouquets/1/orders`
- 请求：`{ "note": "请下午 5 点后送达", "accept_substitute": true }`（note 可空，accept_substitute 默认 true）
- 处理（单事务）：校验库存（跳过 gifted 项）→ 扣减 → bouquet→sent → 创建订单（shop_name、status=accepted，落 note/accept_substitute）。已 sent 重复提交 409。
- 响应 200：`{ "order_id": 1, "bouquet_id": 1, "status": "accepted", "shop_name": "春风花店·抖音本地生活（模拟）" }`

### 1.9 订单详情 `GET /api/v1/orders/1`
- 惰性推进状态（0–15s accepted / 15–40s making / 40–70s delivering / ≥70s done）。
- 响应 200：`{ order_id, status, status_name, shop_name, created_at, preview_url, material_list（含 gifted 标记）, note, accept_substitute, timeline: [{status, name, reached}] }`

### 1.10 订单列表 `GET /api/v1/orders`（同 v0.1，含 timeline，读取时惰性推进）

### 1.11 模拟互动（Demo 专用，P-chat 模拟器） `POST /api/v1/demo/interactions`
- 请求：`{ "kind": "mutual_message" | "share_video" | "streak" }`
- 语义（双人账户入账，随后执行 TA 自动照料评估）：
  | kind | 入账 | 事件文案 |
  |---|---|---|
  | mutual_message | me 与 ta 各 水滴+1 | 「你们今天互相说过话，各获得 1 滴水」 |
  | share_video | **轮流** me/ta 单方 阳光+1 | 「你分享了一条视频，获得 1 缕阳光」/「TA 分享了一条视频，TA 获得 1 缕阳光」 |
  | streak | me 与 ta 各 养料+1 | 「你们已连续互动 3 天，各获得 1 份养料」 |
- 响应 200：`{ "resources": { "me": {...}, "ta": {...} }, "event": { "id", "type", "description", "delta", "occurred_at" } }`（delta 为单资源增量；share_video 的归属可从 description 区分）

### 1.12 花园新变化提示 `GET /api/v1/badge`（同 v0.1）
- 响应 200：`{ "has_update": true, "message": "花园有新的变化，去看看吧" }`（查看花园 1.3 后清除）

### 1.13 AI 推荐搭配 `POST /api/v1/bouquets/recommend`（新增）
- 请求：`{ "occasion": "情侣约会" }`（occasion 枚举：`情侣约会 / 毕业季 / 生日祝福 / 探望问候 / 日常惊喜`，不在枚举内 422）
- 处理：mock LLM（ai_gateway/llm.py `recommend_bouquet`）：按意图从**当前库存可用花材**中选 1–2 种组合（库存为空时仍给出赠送花材 + 空 items），并给出 1 种**赠送花材**（品种不限，不要求用户种植）；生成理由文案。
- 响应 200：
```json
{
  "occasion": "情侣约会",
  "items": [ { "species": "玫瑰", "color": "红", "count": 2 } ],
  "bonus_flower": { "species": "满天星", "color": "白", "count": 1, "gifted": true },
  "reason": "红玫瑰象征热烈的爱意，搭配满天星增添浪漫层次，是情侣约会的经典之选。"
}
```

### 1.14 演示快进 `POST /api/v1/demo/fast-forward`（新增，「查看完整成长旅程」）
- 请求：`{ "plant_id": 1 }`
- 处理：对该植株逐级结算（视为双方均已照料）直升至 bloom，写 `stage_advanced_at` 并置 badge；bloom/pressed 时 409。
- 响应 200：`{ "plant_id": 1, "stage": "bloom", "stage_name": "盛放" }`

### 1.15 演示重置 `POST /api/v1/demo/reset`（新增，「重新体验」）
- 请求：`{}`
- 处理（单事务）：清空**当前会话花园**的 plants/plant_cares/resource_accounts/resource_events/badges/bouquets/orders/house_items/recognitions → 重新播种该花园（双方资源账户归零 + **预置花材** `PRESTOCK_HOUSE`：玫瑰·红×2、洋甘菊·白×2、向日葵·黄×1）。其他访客的花园不受影响。
- 响应 200：`{ "ok": true, "resources": { "me": {...}, "ta": {...} }, "house": [ 同 1.6 items ] }`
- 启动播种（main.py lifespan）为默认花园 1 预置花材，幂等。

### 1.16 当前会话花园 `GET /api/v1/me/garden`（v0.3 新增）
- 按 `X-Session-Id` 解析花园（首次访问自动创建并播种），响应同 1.3 聚合视图。
- 前端用 `garden.garden_id` 拼 1.2/1.4/1.5 的路径；无头时回落花园 1。

### 1.17 图片访问（v0.3 新增）
- `GET /api/v1/images/{id}`：Image 表二进制（上传原图、花束预览图），`Cache-Control: immutable`。
- `GET /api/v1/art/stage/{species}/{color}/{stage}.png`、`GET /api/v1/art/flower/{species}/{color}.png`：确定性 Pillow 资产动态渲染（品种/颜色需 URL 编码）。

## 2. 数据模型（SQLAlchemy；生产 Postgres/Neon，本地默认 SQLite `server/flowers.db`）

| 表 | 字段 |
|---|---|
| `images`（v0.3 新） | id PK, name Unique（内容哈希/业务名去重）, data LargeBinary, mime, created_at |
| `session_gardens`（v0.3 新） | session_id PK, garden_id FK, created_at |
| `recognitions` | 同 v0.1 + **garden_id FK 可空**、**image_id FK 可空**（v0.3） |
| `gardens` | id PK, user_a, user_b, created_at |
| `plants` | id PK, garden_id FK, recognition_id FK **可空**（复种无）, species, main_color, secondary_color, stage, **ta_ready_since 可空**, **stage_advanced_at 可空**, pressed Bool, pressed_at 可空, created_at（删除 progress_* 与 buffered_until） |
| `plant_cares`（新） | id PK, plant_id FK, stage, user(me/ta), completed_at；Unique(plant_id, stage, user) |
| `resource_accounts` | **(garden_id, user) 复合 PK**, water/sunlight/nutrient Int 默认0 |
| `resource_events` | id PK, garden_id, type, description, delta_json, occurred_at |
| `house_items` | id PK, garden_id, species, color, quantity Int, flower_image；Unique(garden_id, species, color)（quantity=0 行保留） |
| `bouquets` | id PK, **garden_id FK 可空（v0.3）**, items_json（bonus 项含 gifted:true）, preview_url, occasion 可空, arrangement_note/packaging 可空, status(draft/sent), created_at |
| `orders` | id PK, bouquet_id FK, shop_name, status, **note 可空**, **accept_substitute Bool 默认 true**, created_at, status_updated_at |
| `badges` | garden_id PK, has_update Bool, message |

## 3. 成长与 TA 自动照料（服务层语义）

- **升级条件**：当前阶段 `plant_cares` 同时存在 (me) 与 (ta) 记录 → 升级到下一阶段，删除该阶段两条 care 记录、`ta_ready_since` 置空、写 `stage_advanced_at`、置 badge。bloom 为终态。
- **TA 自动照料**（garden GET 与 demo/interactions 后惰性评估，对每株非 bloom/pressed 植株）：
  1. ta 未完成本阶段 且 ta 储备 ≥ needs：`ta_ready_since` 为空则置为当前时间；非空且距今 ≥ `TA_CARE_DELAY_SECONDS`（默认 8s）→ 扣 ta 整组资源、记 (ta) care、再做升级检查。
  2. ta 储备 < needs：`ta_ready_since` 重置为空。

## 4. ai_gateway 包契约（vlm/art/imagegen 不变；llm.py 新增两个 mock）

```python
# llm.py 新增：
def recommend_bouquet(occasion: str, available: list[dict]) -> dict:
    """available = [{species, color, quantity}]（quantity>0 的库存）；
    返回 {items: [{species, color, count}], bonus_flower: {species, color, count, gifted: True}, reason: str}"""

def packaging_suggestion(items: list[dict], occasion: str | None) -> str:
    """按主色/意图给包装建议一句话，如 '建议奶白色雾面纸包裹，配浅粉丝带。'"""
```

- 意图→赠送花材映射建议（可在实现中微调，品种不限，建议取自图鉴 6 品种）：情侣约会→玫瑰·红；毕业季→向日葵·黄；生日祝福→郁金香·粉(无粉则红)；探望问候→百合·白；日常惊喜→洋甘菊·白；赠送与 items 不重复时优先（重复则换满天星·白）。
- `arrangement_note`（预览时生成）：基于 items+bonus 与 occasion 的一句话搭配说明（模板化）。
- 其余契约（identify_flower / flower_profile / ensure_stage_images / generate_bouquet）不变；catalog `GROWTH_RHYTHM` 更新为 §0 表格值并删除 `buffer_seconds` 字段（StageSpec 同步去字段，config.py 从 catalog import）。

### 4.1 真实模型接入（2026-07-25，火山方舟）

ai_gateway 对外契约全部不变，内部按 `AI_PROVIDER` 双实现分发（ark 真实调用失败时逐次降级对应 mock，Demo 不中断）：

| 函数 | ark 实现 | mock 降级 |
|---|---|---|
| `identify_flower` | chat/completions 多模态（base64 图 + `response_format=json_object` + `detail=low`），自由识别——品种/颜色不限于图鉴，仅校验非空；模型取 `ARK_VLM_MODEL`（缺省同 chat） | 字节哈希命中图鉴 |
| `flower_profile` | chat/completions 纯文本科普（2 句）；生长节律恒取 catalog；识花链路 ark 模式下经 BackgroundTasks 异步回写 | 图鉴模板（图鉴外品种用通用模板） |
| `recommend_bouquet` | chat/completions JSON 模式，items 校验必须 ⊆ 库存且不超量，bonus 品种非空即可 | 意图映射规则 |
| `arrangement_note` / `packaging_suggestion` | chat/completions 一句话 | 模板 |
| `generate_bouquet` | images/generations（Seedream，size=2K、b64_json、无水印），返回 (字节, mime)，调用方存 `images` 表 | Pillow 合成（同返回字节） |
| `ensure_stage_images` 等 art.py | — | 恒为 Pillow（阶段资产需确定性 + 透明底，不走生图）；URL 指向 /api/v1/art/... 动态渲染端点 |

- 配置（`ai_gateway/settings.py`，独立加载避免与 app.config 循环导入）：`AI_PROVIDER=ark|mock`（未配置 `ARK_API_KEY` 自动 mock）、`ARK_BASE_URL`、`ARK_CHAT_MODEL=doubao-seed-2-0-lite-260215`、`ARK_VLM_MODEL`（识花专用，缺省同 chat）、`ARK_IMAGE_MODEL=doubao-seedream-5-0-260128`、`ARK_CHAT_TIMEOUT=90`、`ARK_IMAGE_TIMEOUT=120`；chat 调用固定 `reasoning_effort=low` 控制时延。时延优化（2026-07-25 二轮）：VLM 图片 `detail=low`、科普文案 2 句且 max_tokens=200、识花首响与科普解耦（首响≈VLM 耗时，科普后台异步补齐）。时延优化（2026-07-25 三轮，花束链路）：搭配说明/包装建议 ThreadPoolExecutor 并行、预览首响与生图解耦（预览图后台生成，超时自动降级 Pillow 保底出图）。生图 size 用 2K（seedream-5-0 最小档位，1K 不被接受；实测约 25s）。
- 密钥经环境变量或 `server/.env`（本地，勿提交；`server/.env.example` 为模板）。
- pytest 经 `tests/conftest.py` 强制 `AI_PROVIDER=mock`（离线、确定性）；真实链路烟测：`scripts/ark_smoke.py`。

## 5. 前端约定（web/）—— 仅接口相关

- `src/api/client.js`：按本文档更新全部封装（响应结构破坏处同步改：1.3 resources/plants、1.4、1.11；新增 1.13/1.14/1.15、复种入参 1.2、preview/order 扩展）。
- P3 资源 HUD 展示 `resources.me`；P3a 余额条同；明细列表数据仍取 `events`。
- 其余页面与交互以《前端设计规范》v2.2 为准。

## 6. 验证要求

- 后端：`cd server && pytest` 全绿（双人入账与归属、整组扣除、已完成/缺口 409、双方齐升级、TA 自动照料、复种、×0 返回、推荐与赠送不扣库存、备注/替代落库、fast-forward、reset 幂等）。
- 前端：`cd web && npm run build` 通过。
- 集成：`scripts/e2e_check.py`（httpx 顺序调用全链路）退出码 0。
