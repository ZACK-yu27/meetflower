# 抖音花园 MVP · 部署指南

> 部署方案：**混合部署**（Cloudflare Pages 前端 + Render 后端）  
> 目标域名：**meetflower.org**

---

## 一、架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户访问                                  │
│                     meetflower.org                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Cloudflare Pages（前端静态托管）                     │
│         ┌─────────────────────────────────────┐                 │
│         │  Vue 3 SPA 构建产物 (web/dist/)     │                 │
│         │  全球 CDN + 自动 HTTPS              │                 │
│         │  自定义域名: meetflower.org         │                 │
│         └─────────────────────────────────────┘                 │
│                        │                                        │
│         CORS API 请求  │  VITE_API_BASE_URL                     │
│                        ▼                                        │
│         ┌─────────────────────────────────────┐                 │
│         │  https://flowers-api.onrender.com   │                 │
│         └─────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Render（后端 API 服务）                             │
│         ┌─────────────────────────────────────┐                 │
│         │  FastAPI + Pillow                   │                 │
│         │  火山方舟 AI API (可选 mock)         │                 │
│         │  图片存 Postgres，经 API 读取        │                 │
│         └─────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Neon（Serverless Postgres，新加坡）                  │
│         ┌─────────────────────────────────────┐                 │
│         │  花园/植株/花束/订单 + 图片二进制     │                 │
│         │  免费档 0.5GB，重启部署不丢数据       │                 │
│         └─────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

| 层级 | 平台 | 费用 | 域名 |
|------|------|------|------|
| 前端 | Cloudflare Pages | **¥0/月** | `meetflower.org` |
| 后端 | Render (Free) | **$0/月** | `flowers-api.onrender.com` |
| 域名 | 任意域名商 | **~¥35-80/年** | `meetflower.org` |

---

## 二、前置准备

### 2.1 账号注册

| 平台 | 注册链接 | 用途 |
|------|---------|------|
| GitHub | https://github.com/join | 代码仓库（已用） |
| Render | https://render.com | 后端托管 |
| Cloudflare | https://dash.cloudflare.com/sign-up | 前端托管 + DNS |

### 2.2 域名准备

在任意域名商（如阿里云、腾讯云、Namecheap、Cloudflare Registrar）购买 `meetflower.org`：

- `.org` 域名年费约 **¥60-100**
- 购买后需将 DNS 服务器指向 Cloudflare（见步骤四）

---

## 三、后端部署（Render）

### 3.1 推送代码到 GitHub

确保项目已推送到 GitHub 仓库（如 `yourname/flowers`），且包含本指南创建的文件：

```bash
git add .
git commit -m "chore: add deployment config for Render + Cloudflare Pages"
git push origin main
```

需包含的关键文件：
- `render.yaml` — Render Blueprint 自动部署配置
- `server/requirements.txt` — Python 依赖
- `server/app/` — 后端源码

### 3.2 在 Render 创建服务

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击 **New +** → **Blueprint**
3. 连接你的 GitHub 仓库 `yourname/flowers`
4. Render 会自动识别根目录的 `render.yaml` 并预填充配置
5. 确认以下配置：
   - **Name**: `flowers-api`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `server`
6. 在 **Environment** 标签页添加敏感变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `AI_PROVIDER` | `mock` → 改 `ark` | 先用 mock 验证部署，确认正常后改为 `ark` |
| `ARK_API_KEY` | `your-real-api-key` | 火山方舟 API Key（仅在 Dashboard 设置，**勿提交到 git**） |
| `ARK_BASE_URL` | `https://ark.cn-beijing.volces.com/api/v3` | |
| `ARK_CHAT_MODEL` | `doubao-seed-2-0-lite-260215` | |
| `ARK_IMAGE_MODEL` | `doubao-seedream-5-0-260128` | |
| `ARK_VLM_MODEL` | 可选 | 拍照识花专用，缺省同 chat |
| `ARK_VIDEO_MODEL` | 可选 | 视频识花（广义的花）属性抽取专用，缺省同 VLM；视频链路对速度敏感可换极速模型 |
| `FLOWERS_DATABASE_URL` | `postgresql://...neon.tech/neondb?sslmode=require` | Neon 连接串（含密码，**勿提交到 git**），见 3.2a |
| `PUBLIC_BASE_URL` | `https://<你的 Render 实际域名>` | 静态资源 URL 前缀，**必填**，见下方说明 |

### 3.2a 准备 Neon Postgres（多用户 + 数据持久化）

1. 打开 [neon.tech](https://neon.tech)，用 GitHub 登录
2. **Create project**：名称随意（如 `flowers`），Region 选 **AWS Asia Pacific 1 (Singapore)**（与 Render 服务同区域，延迟最低），其余默认
3. 创建后在 Dashboard 复制 **Connection string**（形如 `postgresql://neondb_owner:****@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`）
4. 把它填到 Render 环境变量 `FLOWERS_DATABASE_URL`

后端启动时自动建表并播种默认花园；每位访客（按浏览器匿名 Session）自动获得独立花园，数据互不干扰，重新部署不丢数据。

> **⚠️ Render 域名说明**：`onrender.com` 子域名全局唯一。若 `flowers-api` 已被他人占用，Render 会分配带随机后缀的域名（如 `flowers-api-ab12.onrender.com`）。**以 Render Dashboard 服务页顶部显示的实际 URL 为准**，把它同时填到 `PUBLIC_BASE_URL` 和前端 `VITE_API_BASE_URL`。`PUBLIC_BASE_URL` 缺失时，生成图/上传图的 URL 是相对路径，会被浏览器解析到前端域名（Pages）下而 404。

7. 点击 **Apply**
8. 等待构建完成（约 2-3 分钟）

### 3.3 验证后端

部署完成后，Render 会分配域名如 `https://flowers-api.onrender.com`。

打开浏览器访问：
```
https://flowers-api.onrender.com/api/v1/gardens/1
```

应返回 JSON 格式的花园数据（含 `resources` 和 `plants`）。

**⚠️ 已知限制（Free Plan）**：
- 服务 15 分钟无访问会休眠，下次请求需等待约 1 分钟唤醒
- 数据存 Neon Postgres，部署/重启不再丢失（图片也存库中）

---

## 四、前端部署（Cloudflare Pages）

### 4.1 创建 Pages 项目

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 进入 **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**
3. 授权并选择 GitHub 仓库 `yourname/flowers`
4. 配置构建：

| 配置项 | 值 |
|--------|-----|
| **Project name** | `flowers` |
| **Production branch** | `main` |
| **Build command** | `cd web && npm install && npm run build` |
| **Build output directory** | `web/dist` |

5. 在 **Environment variables (advanced)** 中添加：

| 变量名 | 值 | 环境 |
|--------|-----|------|
| `VITE_API_BASE_URL` | `https://flowers-api.onrender.com` | Production |
| `NODE_VERSION` | `20` | Production |

> **注意**：`VITE_API_BASE_URL` 必须与 Render 后端的实际域名一致。

6. 点击 **Save and Deploy**
7. 等待构建完成（约 1-2 分钟）

### 4.2 验证前端

构建完成后，Cloudflare 会分配一个临时域名如：
```
https://flowers.pages.dev
```

打开该链接，确认页面正常加载，且 API 调用无跨域错误。

---

## 五、绑定自定义域名（meetflower.org）

### 5.1 在 Cloudflare 添加域名

1. 在 Cloudflare Dashboard 左侧菜单 → **Websites** → **Add a Site**
2. 输入域名 `meetflower.org`，选择 **Free plan**
3. Cloudflare 会扫描现有 DNS 记录，点击 **Continue**
4. 复制 Cloudflare 提供的两个 **Nameserver** 地址（如 `dana.ns.cloudflare.com` 和 `greg.ns.cloudflare.com`）

### 5.2 在域名商修改 DNS 服务器

1. 登录你的域名购买平台（如阿里云、腾讯云、Namecheap）
2. 找到域名管理 → DNS 设置 → 修改 DNS 服务器
3. 将原有 DNS 服务器替换为 Cloudflare 提供的两个地址
4. 保存并等待生效（通常 **5 分钟 - 2 小时**）

### 5.3 在 Pages 项目绑定域名

1. 回到 Cloudflare Dashboard → **Workers & Pages** → 选择 `flowers` 项目
2. 进入 **Custom domains** 标签页
3. 点击 **Set up a custom domain**
4. 输入 `meetflower.org`
5. Cloudflare 会自动创建 DNS 记录并配置 SSL 证书
6. 等待几分钟，状态变为 **Active** 即绑定成功

### 5.4 验证

浏览器访问 `https://meetflower.org`，确认：
- ✅ 页面正常加载（HTTPS 锁标志）
- ✅ 拍照识花、花园、花房等功能正常
- ✅ API 调用无 CORS 错误

---

## 六、部署后配置调整

### 6.1 切换 AI 为真实模型（ark 模式）

确认后端部署正常后，在 Render Dashboard 修改环境变量：

```
AI_PROVIDER=ark
ARK_API_KEY=你的真实火山方舟 API Key
```

然后点击 **Manual Deploy** → **Deploy latest commit** 重新部署。

### 6.2 更新前端 API 地址（如果后端域名变了）

如果 Render 项目名不同导致域名变化（如 `https://flowers-api-xxxx.onrender.com`）：

1. Cloudflare Dashboard → Pages 项目 → **Settings** → **Environment variables**
2. 更新 `VITE_API_BASE_URL` 为新的 Render 域名
3. 重新部署前端

---

## 七、完整部署流程速查

```bash
# 1. 确认代码已推送（含 render.yaml 和修改后的 client.js）
git push origin main

# 2. Render 后端（通过 Dashboard 自动部署）
#    → 验证: https://flowers-api.onrender.com/api/v1/gardens/1

# 3. Cloudflare Pages 前端（通过 Dashboard 自动部署）
#    → 验证: https://flowers.pages.dev

# 4. 绑定域名
#    → Cloudflare 添加站点 → 修改 DNS 服务器 → Pages 绑定域名
#    → 验证: https://meetflower.org

# 5. 切换真实 AI（可选）
#    → Render Dashboard 修改 AI_PROVIDER=ark + ARK_API_KEY
```

---

## 八、常见问题

### Q1: Render Free 服务休眠后首次访问慢？

Render Free 实例 15 分钟无访问会休眠。首次请求需要约 1 分钟唤醒。

**解决方案**：
- 使用 [UptimeRobot](https://uptimerobot.com) 免费计划每 5 分钟 ping 一次后端，保持活跃
- 或升级到 Render Starter ($7/月) 永不停机

### Q2: 数据库每次部署后丢失？

已解决：数据库改为 Neon Postgres（Serverless，免费档），数据与图片均存于 Render 之外，部署/重启/休眠都不再丢失。早期版本的 SQLite 方案已废弃。

### Q3: 跨域错误（CORS）？

后端 `main.py` 已配置 `allow_origins=["*"]`，正常情况下不会出现 CORS 问题。如果出现：

1. 确认 `VITE_API_BASE_URL` 指向的是 Render 后端域名（不是相对路径 `/`）
2. 确认后端服务正常运行（直接访问 API 链接看是否返回数据）
3. 检查浏览器 DevTools Network 面板查看具体错误信息

### Q4: 图片上传/生成后无法显示？

后端 `/static` 挂载了 `app/assets/` 目录，生成图和上传图保存在此处。Render Free 上这些文件在部署后会丢失。

**解决方案**：
- 演示阶段可接受
- 长期方案：使用 Cloudflare R2 或 AWS S3 存储图片

### Q5: 域名绑定后无法访问？

1. 确认 DNS 服务器已修改为 Cloudflare 的（在域名商后台检查）
2. 在 Cloudflare Dashboard → DNS 页面，确认有 A/AAAA 记录或 CNAME 记录
3. 使用 `dig meetflower.org` 或在线 DNS 检测工具确认解析已生效
4. 清除浏览器缓存或尝试无痕模式

### Q6: API 全部 404，响应是 `Cannot GET /api/v1/...`？

`Cannot GET` 是 **Express（Node.js）** 的错误格式，不是本项目 FastAPI 的——说明 `VITE_API_BASE_URL` 指向了**别人的 Render 服务**（`onrender.com` 子域名全局唯一，`flowers-api` 这类通用名很可能已被占用）。

**解决方案**：

1. 打开 Render Dashboard 你的服务页面，复制顶部显示的**实际 URL**（可能带随机后缀，如 `flowers-api-ab12.onrender.com`）
2. 直接访问 `<实际URL>/api/v1/gardens/1`，应返回 JSON（含 `resources`/`plants`）；返回 JSON 格式的 `{"detail": ...}` 错误才是本项目的响应
3. Cloudflare Pages → Settings → Environment variables：把 `VITE_API_BASE_URL` 改为实际 URL，重新部署前端
4. Render → Environment：把 `PUBLIC_BASE_URL` 也设为同一个实际 URL（静态资源前缀），重新部署后端

---

## 九、费用总结

| 项目 | 月费用 | 年费 |
|------|--------|------|
| Cloudflare Pages（前端） | **¥0** | ¥0 |
| Render Free（后端） | **$0** (~¥0) | ¥0 |
| 域名 `meetflower.org` | — | **~¥60-100** |
| 火山方舟 AI（按量） | **~¥0-20**（视用量） | — |
| **总计** | **¥0-20/月** | **~¥60-100** |

---

*文档版本: 2026-07-25*  
*对应代码版本: MVP v0.2*
