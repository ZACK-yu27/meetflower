# HANDOFF · 抖音花园项目交接文档

> 生成时间：2026-07-25 ｜ 生成背景：「按 0725-产品细化调整」任务执行中途，用户主动中止，交接后续负责人/会话。
>
> **✅ 已结案（2026-07-25）**：本交接所述调整已全部执行完毕——后端按 API v0.2、前端按设计规范 v2.2 落地，e2e 重写并通过。新基线：pytest 23 passed ｜ e2e 17 步 ~87s 退出码 0 ｜ npm run build 通过。README 已同步 v0.3 口径。本文以下内容为历史快照，仅供追溯。

## 1. 项目一句话

抖音生态闭环 Demo：两位好友把现实中拍到的花种进共同花园，聊天互动积累**各自的**照料资源，**双方分别完成照料**后花朵逐阶段盛放、压花收入花房，组合生成 AI 花束并发送抖音本地花店（实体履约）。技术栈：FastAPI + SQLite（后端）、Vue3 + Vite 移动端 H5（前端）、Pillow mock 视觉资产、mock VLM/LLM/生图（ai_gateway 包，可整体替换真实模型）。

## 2. 当前状态快照（最重要）

**文档领先于代码。** 仓库处于一次大调整的中间态：

| 层 | 状态 | 版本 |
|---|---|---|
| `docs/PRD.md` | ✅ 已更新 | **v0.3**（双人资源/双人照料/仿聊天页/推荐搭配/复种/重置） |
| `docs/API.md` | ✅ 已更新 | **v0.2**（破坏式契约变更，见 §5） |
| `docs/前端设计规范.md` | ✅ 已更新 | **v2.2**（P-chat 新页、双人进度、提醒TA、双入口等） |
| `server/` 后端代码 | ⏸ 仍是旧版 | 实现 **API v0.1**（单人共享资源、渐进照料+缓冲期），pytest 9 项上次验证通过（对旧契约） |
| `web/` 前端代码 | ⏸ 仍是旧版 | 实现设计规范 **v2.1.2**（续火花花园页、资源/花房半屏卡） |
| `scripts/e2e_check.py` | ⏸ 旧版 | 按 API v0.1 链路编写 |

- 调整任务的完整执行方案在计划文件：`C:/Users/zackt/.kimi-code/sessions/wd_flowers_56d420a568d3/session_b195b723-0a7b-4592-a282-c9a22fa52bc4/agents/main/plans/fantomex-winter-soldier-blue-devil.md`（含 13 项差距分析、分阶段任务、接口变更要点）。
- 执行进度：**Phase 0（三份契约文档）已完成**；Phase 1（后端+前端并行实施）刚启动即被用户中止，**两个实施子代理未产生任何代码改动**；Phase 2（e2e 重写与集成验证）、Phase 3（README 同步）未开始。
- 后台服务（uvicorn :8000 / vite :5173）已全部停止，端口已释放。

## 3. 仓库结构与文档地图

```
flowers/
├── HANDOFF.md                 # 本文
├── README.md                  # 运行指南（当前对应旧版代码，v0.2 落地后需同步）
├── docs/
│   ├── PRD.md                 # 业务权威 v0.3
│   ├── API.md                 # 接口权威 v0.2
│   └── 前端设计规范.md         # 设计权威 v2.2（含 changelog 全历史）
├── server/                    # FastAPI 后端（旧 v0.1 实现）
│   ├── app/{main,config,db,models,schemas}.py
│   ├── app/services/          # garden/resource/house/bouquet/order/recognition
│   ├── app/api/               # 路由
│   ├── app/ai_gateway/        # mock VLM/LLM/生图 + Pillow 地栽资产（catalog/vlm/llm/art/imagegen/smoke）
│   ├── app/assets/{gen,uploads}/
│   ├── tests/                 # pytest（旧契约 9 项）
│   └── .venv/                 # 已装全部依赖（requirements.txt 锁定）
├── web/                       # Vue3 前端（旧 v2.1.2 实现）
│   └── src/{views,components,stores,api,demo,assets,utils}
├── scripts/e2e_check.py       # 端到端验证脚本（旧链路）
├── resources/UIUX_references/ # 全部设计参考图
└── 0725-*.md / .pdf           # 上游设计文档（产品细化为最新业务输入）
```

## 4. 如何继续未完成的调整（推荐路径）

按序执行（详细任务描述见计划文件 §1–§5）：

1. **后端改造**：按 `docs/API.md` v0.2 实施。要点：resource_accounts 复合 PK(garden_id,user)；新表 plant_cares；plants 删 progress_*/buffered_until、加 ta_ready_since/stage_advanced_at；照料=整组扣除+双人各完成一次（无缓冲期）；阶段数值=向日葵示例（水2/3/4/5、光0/1/2/3、养0/0/2/3）；TA 自动照料（储备达标延迟 8s）；互动语义（水滴/养料双方各得、阳光仅分享者轮流）；复种入参；推荐/赠送/包装 mock（llm.py）；订单 note/accept_substitute；demo fast-forward/reset + 预置花材（玫瑰红×2、洋甘菊白×2、向日葵黄×1）。**完成后删除 `server/flowers.db` 重启重建**（破坏式变更）。pytest 按 API.md §6 清单更新并全绿。
2. **前端改造**：按 `docs/前端设计规范.md` v2.2 实施。要点：P2 CTA「进入花园」+ 选择花园卡 → 种植后跳 `/chat`；新增 P-chat 仿抖音聊天页（模拟消息流 + 花园入口条 + 三模拟器按钮 + 「重新体验」）；P3 工具列加「聊天」、植株卡「我/TA」并列进度、提醒TA弹窗、成长动画、「查看完整成长旅程」；P3a 删演示工具区；P4「AI插花」动作面板双入口（AI 推荐搭配=意图 chips+赠送标记 / 自由搭配）、×0 灰卡「重新种植」；P5 搭配说明/包装/备注/替代选项/赠送标记；P6 同步静态展示；api/client.js 按 v0.2 同步。`npm run build` 通过。
3. **集成验证**：重写 `scripts/e2e_check.py`（双人照料链路：互动→我照料→等 TA 自动→升级；fast-forward 旅程；复种；推荐+赠送不扣库；下单含备注/替代；reset 幂等），退出码 0；三项验证（pytest / build / e2e）全绿。
4. **收尾**：README 同步 v0.3 口径。

**可用子代理（resume 即保留其上下文）**：`agent-1`（前端 web/）、`agent-2`（后端 server/ 含 ai_gateway 契约）、`agent-3`（集成/QA）、`agent-0`（ai_gateway 资产）。中止前的 Phase 1 即计划 resume agent-1 + agent-2 并行。

## 5. 运行手册

```bash
# 后端（Windows Git Bash）
cd server && source .venv/Scripts/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000
# 前端（另开终端）
cd web && npm run dev        # :5173，代理 /api 与 /static → :8000
# 验证
cd server && pytest                                   # 单元/服务层
server/.venv/Scripts/python scripts/e2e_check.py      # 端到端（需 uvicorn 已启动）
cd web && npm run build
```

**已知坑**：
- 停止 vite dev 后其子进程常残留占用 5173：`netstat -ano | grep 5173` 查 PID → `taskkill //PID <pid> //F`。
- 改模型结构后直接删 `server/flowers.db` 重启（若 8000 被占用先杀进程再删）；启动自动播种 garden 1。
- 生成的 `assets/gen/*.png` 有缓存：改 art.py 绘制逻辑后需删 gen 下 PNG 让其重新生成（保留 .gitkeep）。
- Python 输出中文到 Windows 控制台需 `PYTHONIOENCODING=utf-8`；PDF 中文提取含康熙部首需 `unicodedata.normalize('NFKC', ...)`。

## 6. 产品/设计口径备忘

- **程序形态**：抖音内程序、页面栈导航、**禁止全局底部 TabBar**（用户明确否决过旧版 3-tab 形态，勿回退）。
- **术语**：花房（原"仓库"，v2.1.2 起全局统一）、压花收藏（禁"采摘"）、照料这朵花（禁三个独立消耗按钮）。
- **文档效力**：业务=PRD、接口=API.md、设计=前端设计规范；改设计先改规范并记 changelog。
- **本期不做**（上游未定项）：「广义的花」（feed 浮标识别）、资源每日上限、花束配方规则库、多花园管理 UI、真实交易。
- Demo 固定：garden_id=1、「我」(me) 与「小葵」(ta)；TA 为虚拟人（资源与照料由系统模拟，8s 延迟参数在 config）。

## 7. 验证基线（旧版代码最后已知状态）

- `pytest`：9 passed（API v0.1 契约）。
- `scripts/e2e_check.py`：退出码 0（229.8s，v0.1 链路 9 步）。
- `npm run build`：通过。
- 若继续调整前想先确认仓库健康，可直接运行上述三项（对旧代码应全绿）。

## 8. 花卉线稿（flower-lineart skill，2026-07-25）

- **任何线稿/花头渲染/花色/花型改动必须先调用 `flower-lineart` skill**（用户级 skills 目录），
  规则单一事实来源是 `server/app/ai_gateway/catalog.py` 模块 docstring，改规则需两边同步。
- 颜色规则：图鉴精确 hex > GENERIC_COLORS > 哈希派生；色名经 `normalize_color()`；
  **渲染路由必须剥 `.png` 后缀**（曾致生产"红玫瑰画成紫色"事故，tests/test_art.py 常驻回归）。
- 花型规则：7 枚举（rosette/daisy/disk/cup/lily/ball/cluster），VLM 输出 form →
  Recognition.form → Plant.form → HouseItem.form → URL 传递；图鉴品种恒取图鉴画法。
- 验收：pytest 全绿（test_art.py 像素级颜色断言）+ render_preview.py 拼图亲眼检查 +
  art 端点缓存 max-age=300 不得调大。
