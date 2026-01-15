# HTML to Markdown

## 项目初衷
在 AI 辅助工作流中，高质量的**上下文（Context）**是关键。我们常遇到这样的场景：从网页、技术文档或 ChatGPT 等工具中获取了有价值的富文本内容，需要将其作为输入“喂”给 AI 进行二次处理或存入知识库（如 Obsidian/Notion）。

然而，直接复制的富文本往往携带大量 HTML 噪声，既浪费 Token，又容易干扰 AI 的语义理解。

**HTML to Markdown** 正是为此打造的“清洗转换器”。它能一键将复杂的网页内容转化为**干净、结构化、Token 友好**的标准 Markdown。无论是为了构建个人知识库，还是为了让 AI 更精准地理解你的输入，它都能让信息流转变得无比丝滑。

## 概览
- 后端：FastAPI + mdcore 转换器（conda 虚拟环境 md）
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
- 加载本地扩展：
  - 打开 chrome://extensions，开启开发者模式
  - 选择“加载已解压的扩展”，指向 ext/chrome
- 选项：
  - 后端地址 endpoint 与 Token
  - 核心转换样式：strong/emphasis 分隔符、code_fence、unordered_marker、list_indent_spaces、unknown_tag_strategy、expand_to_block_boundaries
- 使用：
  - 右键菜单选择“转为 Markdown（整页/选区）”
  - 转换结果自动保存并打开 result.html 预览页
