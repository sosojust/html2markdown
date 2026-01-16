# Frontend Web App

HTML to Markdown 服务的用户管理前端，提供用户注册、登录及 API Key 管理功能。

## 架构
- **框架**: React 18 + Vite
- **UI 库**: Tailwind CSS + DaisyUI
- **路由**: React Router v6
- **状态管理**: React Context (AuthContext)
- **HTTP 客户端**: Axios

## 依赖
- Node.js 18+
- npm / yarn / pnpm

## 项目结构
- `src/context`: 全局状态（鉴权）
- `src/pages`: 页面组件 (Login, Register, Dashboard)
- `src/main.jsx`: 入口文件与路由配置

## 运行说明

1. 安装依赖:
   ```bash
   npm install
   ```

2. 启动开发服务器:
   ```bash
   npm run dev
   ```
   默认运行在 http://localhost:5173

3. 构建生产版本:
   ```bash
   npm run build
   ```

## 配置
默认连接后端 API 地址为 `http://localhost:8000`。
如需修改，请在 `src/context/AuthContext.jsx` 中更改 `baseURL`。
