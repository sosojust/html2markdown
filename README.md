# HTML to Markdown

## 项目初衷
在 AI 辅助工作流中，高质量的**上下文（Context）**是关键。我们常遇到这样的场景：从网页、技术文档或 ChatGPT 等工具中获取了有价值的富文本内容，需要将其作为输入“喂”给 AI 进行二次处理或存入知识库（如 Obsidian/Notion）。

然而，直接复制的富文本往往携带大量 HTML 噪声，既浪费 Token，又容易干扰 AI 的语义理解。

**HTML to Markdown** 正是为此打造的“清洗转换器”。它能一键将复杂的网页内容转化为**干净、结构化、Token 友好**的标准 Markdown。无论是为了构建个人知识库，还是为了让 AI 更精准地理解你的输入，它都能让信息流转变得无比丝滑。

## 概览
- 后端：FastAPI + mdcore 转换器（conda 虚拟环境 md）
- 前端：React + Vite（用户管理与 API Key 控制台）
- 前端插件：Chrome MV3 扩展，支持整页/选区转换与结果页预览
- 规格：openspec 目录管理 API/转换/插件的规范与变更

## 开发与运行
- 激活虚拟环境：
  - conda activate md
- 安装依赖并运行测试：
  - cd backend
  - python -m pip install -r requirements.txt
  - python -m pytest -q
- 启动后端：
  - ./backend/run_server.sh
  - 默认端口 http://localhost:8000
- 启动前端：
  - cd frontend
  - npm install && npm run dev
  - 默认端口 http://localhost:5173

## 配置
- 使用 backend/.env 文件覆盖默认配置（优先于环境变量）：
  - AUTH_ENABLED/AUTH_TOKEN：鉴权开关与令牌
  - RL_ENABLED/RL_MAX/RL_WINDOW_MS：速率限制
  - PROCESS_TIMEOUT_MS：转换超时（毫秒）
  - MAX_HTML_LENGTH：请求体大小上限（字节）
  - MAX_FETCH_LENGTH：by_url 抓取体积上限（字节）
  - HTTP_USER_AGENT：by_url 抓取的 UA
  - MAX_REDIRECTS：by_url 最大重定向次数（默认 5）
- 配置加载模块：
  - backend/api/config.py

## API
- POST /v1/convert：HTML→Markdown
- POST /v1/convert/by_url：服务端抓取→Markdown（限制体积与超时，非 text/html 返回 415）
- GET /v1/health、GET /v1/version：健康与版本
- 鉴权与限流：
  - Authorization: Bearer <token>
  - X-RateLimit-Limit、X-RateLimit-Remaining、X-RateLimit-Reset（毫秒；reset_ms = max(bucket.ts + RL_WINDOW_MS - now_ms, 0)）

## Chrome 扩展
- 加载本地开发扩展：
  - 打开 chrome://extensions，开启开发者模式
  - 选择“加载已解压的扩展”，指向 ext/chrome
- 打包上线扩展（替换API地址）：
  - 复制 `ext/chrome/.env.example` 为 `ext/chrome/.env`，并配置你的线上域名
    ```env
    API_URL=https://api.yourdomain.com
    DASHBOARD_URL=https://yourdomain.com
    ```
  - 运行 `cd ext/chrome && npm run build`
  - 将生成的 `ext/dist_chrome` 文件夹加载到 Chrome 或打包发布
- 选项：
  - 后端地址 endpoint
  - API Key：需先在前端控制台（Frontend Dashboard）注册并创建 Key，复制后填入
  - 核心转换样式：strong/emphasis 分隔符、code_fence、unordered_marker、list_indent_spaces、unknown_tag_strategy、expand_to_block_boundaries
- 使用：
  - 右键菜单选择“转为 Markdown（整页/选区）”
  - 转换结果自动保存并打开 result.html 预览页

## 前端 Web 应用
- 环境变量配置：
  - 本地开发：使用 `frontend/.env.development`，默认 API 为 `http://localhost:8000/v1`
  - 生产上线：修改 `frontend/.env.production`，将 `VITE_API_BASE_URL` 指向你的线上 API 域名
  - Vite 会在运行 `npm run dev` 或 `npm run build` 时自动加载对应的环境变量

## 生产部署
本项目提供基于 Docker Compose 的一键生产部署方案，包含后端、前端（Nginx）、PostgreSQL 数据库；可选：Redis（用于开启限流时使用）。

### 1. 准备工作
确保服务器已安装 Docker 和 Docker Compose。

### 2. 启动服务
使用 `docker-compose.prod.yml` 启动所有服务：
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 3. 初始化数据库
首次部署需导入数据库结构：
```bash
# 等待数据库容器启动完成后执行
docker compose -f docker-compose.prod.yml exec -T db psql -U md_user -d md_db < backend/schema/latest_postgres.sql
```

### 4. 访问服务
- 前端页面：http://localhost (或服务器 IP)
- 后端 API：http://localhost/v1 (通过 Nginx 代理)

### 5. 环境变量配置
在 `docker-compose.prod.yml` 中可调整以下关键环境变量：
- `SECRET_KEY`: 用于 JWT 签名的密钥（生产环境务必修改）
- `AUTH_ENABLED`: 是否开启鉴权（默认为 true）
- `DATABASE_URL`: 数据库连接串
- 可选 `REDIS_URL`: 仅在启用限流（`RL_ENABLED=1`）时需要配置的 Redis 连接串
- `ALLOWED_ORIGINS`: 允许跨域访问的域名，生产环境建议设置为前端域名（如 `https://example.com`），多个域名用逗号分隔

### 4. 域名配置（可选）
如果您拥有真实域名（例如 `example.com`），请执行以下调整：

1. **修改 Nginx 配置**：
   编辑 `frontend/nginx.conf`，将 `server_name` 修改为您的域名：
   ```nginx
   server_name example.com www.example.com;
   ```

2. **配置跨域许可**：
   修改 `docker-compose.prod.yml` 中的 `ALLOWED_ORIGINS`：
   - **插件使用场景（推荐）**：设置为 `*`。因为插件会在任意网页运行，请求来源（Origin）是动态的。
     ```yaml
     - ALLOWED_ORIGINS=*
     ```
   - **仅Web端使用**：如果您只通过网页版前端使用，可设置为您的域名以提高安全性：
     ```yaml
     - ALLOWED_ORIGINS=http://example.com,https://example.com
     ```

3. **HTTPS 支持**（建议）：
   生产环境强烈建议开启 HTTPS。您可以在宿主机使用另一层 Nginx/Caffeine 进行 SSL 卸载，并将流量转发到本服务的 80 端口；或者直接挂载证书到容器内并修改 `frontend/nginx.conf` 开启 443 监听。

## 变更记录
- 2026-03-16:
  - 工程：前端 Web 应用增加 `.env.development` 和 `.env.production` 环境变量支持
  - 工程：Chrome 插件增加 `build.js` 打包脚本，支持根据 `.env` 环境变量自动替换 API 和 Dashboard 的生产域名
- 2026-01-28:
  - 安全：增加登录/注册接口的独立限流策略（5次/分钟）
  - 安全：增强用户注册密码强度校验（至少8位）
  - 安全：支持通过 `ALLOWED_ORIGINS` 配置 CORS 策略
  - 文档：添加生产环境部署指引 (Docker Compose)
  - 工程：添加 Dockerfile 和 docker-compose.prod.yml 支持一键部署
- 2026-01-19:
  - 后端：引入 Refresh Token 机制（Access Token 30分钟，Refresh Token 30天），解决用户频繁登录问题
  - 前端：实现自动 Token 刷新逻辑，当 Access Token 过期时无感刷新并同步至扩展
  - 扩展：优化鉴权体验，当未配置 API Key 且未登录时，点击转换自动弹出登录窗口（promptLogin）
  - 扩展：移除登出时的自动页面跳转，仅清除本地状态
  - 修复：增强 Refresh Token 机制的健壮性，自动清理无 Refresh Token 的遗留会话，防止前端与扩展状态不一致
  - 配置：默认开启鉴权 (AUTH_ENABLED=1)
- 2026-01-16:
  - 后端：实现 JWT 鉴权与 API Key 系统，支持多种密码哈希方案 (Argon2/Bcrypt/PBKDF2)
  - 前端：新增 Login/Register/Dashboard 页面，支持用户注册与 API Key 管理
  - 扩展：更新 Chrome 扩展选项页，支持配置 API Key 进行鉴权
  - 修复：解决 UUID 类型错误、Tailwind v4 配置冲突等问题
  - 修复：解决 html-to-markdown 库在转换特定内容时出现的 RefCell panic 问题（增加 fallback 机制）
  - 修复：解决选中内容包含 textarea 标签时转换结果为空的问题
  - 扩展：实现扩展与前端登录态同步，支持无 API Key 时的自动登录鉴权（需在 Dashboard 登录）
  - 扩展：优化登录态显示，扩展可显示当前登录用户的邮箱（支持 Token 解析与 localStorage 同步）
  - 扩展：实现登出同步，扩展登出时自动触发前端登出
  - 后端：API Token Payload 增加 email 字段，方便客户端展示用户信息
