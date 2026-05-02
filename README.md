# OfferLens
试用网址：https://offerlens-67je.vercel.app/
OfferLens 是一个 AI 求职提效工具。用户输入简历与岗位描述（JD），系统输出：
- 匹配度分数
- 优势项
- 薄弱项
- 缺失关键词
- 简历改写建议
- 高频面试题推荐
- 总结建议

当前项目定位为可上线展示的 MVP（无数据库、无登录、无支付）。

## 技术栈

- 前端：Vue 3 + Vite + TypeScript + Element Plus + Axios
- 后端：FastAPI + Pydantic + Uvicorn + httpx
- 本地运行：Docker Compose
- 线上部署：Vercel（前端） + Render（后端）

## 目录结构

```text
offerlens/
  .env.example
  docker-compose.yml
  render.yaml
  backend/
    Dockerfile
    requirements.txt
    app/
      main.py
      core/config.py
      api/routes.py
      services/
        analyzer_service.py
        llm_service.py
      prompts/resume_analysis_prompt.txt
  frontend/
    Dockerfile
    package.json
    vite.config.ts
    src/
      api/analyze.ts
      views/HomeView.vue
```

## 环境变量说明

根目录 `.env.example` 已给出默认示例。常用变量如下。

### 后端

- `APP_NAME`：FastAPI 应用名（示例：`OfferLens Backend`）
- `APP_ENV`：运行环境（`dev` / `prod`）
- `CORS_ORIGINS`：允许跨域来源，逗号分隔  
  示例：`http://localhost:5173,https://your-frontend.vercel.app`
- `LLM_BASE_URL`：OpenAI-compatible 中转接口地址
- `LLM_API_KEY`：模型 API Key
- `LLM_MODEL`：模型名
- `LLM_TIMEOUT`：总超时（秒）
- `LLM_CONNECT_TIMEOUT` / `LLM_READ_TIMEOUT` / `LLM_WRITE_TIMEOUT` / `LLM_POOL_TIMEOUT`：细粒度超时
- `LLM_MAX_RETRIES`：可重试错误重试次数（额外重试次数）
- `LLM_RETRY_BACKOFF`：重试退避基数

### 前端

- `VITE_API_BASE_URL`：后端 API 基地址  
  本地示例：`http://localhost:8000`  
  线上示例：`https://offerlens-backend.onrender.com`

## 本地开发

### 方式一：Docker（推荐）

在项目根目录执行：

```bash
docker compose up --build
```

访问：
- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- 健康检查：`http://localhost:8000/api/health`

### 方式二：分别启动

后端：

```bash
cd backend
python -m venv .venv
# Windows
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## 部署到 Vercel（前端）

### 1) 导入 GitHub 仓库

在 Vercel 里点击 `Add New -> Project`，选择你的 GitHub 仓库。

### 2) 关键配置

- Framework Preset：`Vite`（通常会自动识别）
- Root Directory：`frontend`
- Build Command：默认即可（`npm run build`）
- Output Directory：默认即可（`dist`）
- Install Command：默认即可（`npm install`）

### 3) 环境变量

至少配置：

- `VITE_API_BASE_URL` = Render 后端地址（例如 `https://offerlens-backend.onrender.com`）

### 4) 获取前端域名

部署完成后，Vercel 会给出域名，如：
`https://offerlens-demo.vercel.app`

这个域名后续要填到后端 `CORS_ORIGINS`。

## 部署到 Render（后端）

你有两种方式：手动创建，或使用仓库里的 `render.yaml`。

### 方式 A：手动创建 Web Service

1. Render -> `New +` -> `Web Service`
2. 选择 GitHub 仓库
3. 填写配置：
- Root Directory：`backend`
- Runtime：`Python`
- Build Command：`pip install -r requirements.txt`
- Start Command：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. 设置环境变量（至少）：
- `APP_NAME=OfferLens Backend`
- `APP_ENV=prod`
- `CORS_ORIGINS=https://你的-vercel-域名.vercel.app`
- `LLM_BASE_URL=...`
- `LLM_API_KEY=...`
- `LLM_MODEL=MiniMax-M2.7-highspeed`（按你的模型填写）
- `LLM_TIMEOUT=30`

建议同时设置：
- `LLM_CONNECT_TIMEOUT=5`
- `LLM_READ_TIMEOUT=45`
- `LLM_WRITE_TIMEOUT=20`
- `LLM_POOL_TIMEOUT=10`
- `LLM_MAX_RETRIES=1`
- `LLM_RETRY_BACKOFF=1.0`

5. 部署完成后，记录 Render 地址，例如：
`https://offerlens-backend.onrender.com`

### 方式 B：使用 render.yaml（可选）

仓库根目录已提供 `render.yaml`。在 Render 里用 Blueprint 导入仓库即可自动带入：
- `rootDir`
- `build/start command`
- `healthCheckPath=/api/health`

其中 `CORS_ORIGINS`、`LLM_BASE_URL`、`LLM_API_KEY` 仍需你在 Render 控制台手动填真实值。

## 跨域配置（重点）

前后端分域名部署时，后端必须正确设置 `CORS_ORIGINS`。

示例：

```env
CORS_ORIGINS=https://offerlens-demo.vercel.app
```

多个来源（逗号分隔）：

```env
CORS_ORIGINS=http://localhost:5173,https://offerlens-demo.vercel.app
```

## 上线后联调验证

### 1) 后端探活

访问：

```text
https://你的-render-域名/api/health
```

预期返回：

```json
{
  "status": "ok",
  "llm_configured": true
}
```

### 2) 前端到后端连通

在浏览器打开 Vercel 前端，提交简历 + JD：
- 若成功：页面展示分析结果
- 若失败：检查 Vercel 环境变量 `VITE_API_BASE_URL` 是否为 Render 的 HTTPS 地址

### 3) `/api/analyze` 线上可用性

可直接调用：

```bash
curl -X POST "https://你的-render-域名/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"resume_text":"你的简历文本","job_description":"你的JD文本"}'
```

预期：HTTP `200` 且返回完整 JSON 字段（`score/strengths/weaknesses/...`）。

## 常见问题

1. 前端请求失败但后端健康检查正常  
通常是 `VITE_API_BASE_URL` 或 `CORS_ORIGINS` 配置错误。

2. `llm_configured=false`  
说明 `LLM_BASE_URL` 或 `LLM_API_KEY` 缺失。

3. Render 首次冷启动慢  
免费实例可能冷启动，首次请求慢属于平台特性。

4. 本地 Docker 是否还能用  
可以，`docker compose up --build` 保持不变。
