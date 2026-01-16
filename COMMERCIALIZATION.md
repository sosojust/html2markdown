# 商业化路线图 (Commercialization Roadmap)

为了将 HTML to Markdown 项目转化为商业产品，我们需要从单纯的工具升级为完整的 SaaS 服务。以下是关键的建设领域：

## 1. 用户与鉴权体系 (User & Auth)
目前仅支持单点静态 Token，无法支撑多用户商业场景。

- [ ] **多用户架构**：引入关系型数据库（PostgreSQL/MySQL），设计 `users` 表。
- [ ] **鉴权机制升级**：
    - 支持 API Key 管理（创建/删除/重置）。
    - 支持 OAuth2（Google/GitHub 登录）。
- [ ] **配额管理**：基于用户等级（Free/Pro）设置不同的 Rate Limit 和每日/每月调用次数限制。

## 2. 支付与订阅 (Billing & Subscription)
- [ ] **支付网关集成**：接入 Stripe 或类似服务。
- [ ] **订阅模型**：
    - **Free Tier**: 每日有限次数，基础转换功能。
    - **Pro Tier**: 无限次数，优先处理，高级排版选项，批量转换接口。
    - **API Tier**: 按量计费，面向开发者集成。
- [ ] **Webhook 处理**：处理支付成功、续费失败、退款等事件，自动更新用户权益。

## 3. 架构高可用与扩展 (Reliability & Scalability)
目前 Rate Limit 是内存式的，无法横向扩展。

- [ ] **分布式限流**：引入 Redis 实现分布式的 Token Bucket 或 Fixed Window 限流。
- [ ] **异步任务队列**：对于大页面或批量转换，引入 Celery/Redis Queue，避免阻塞 API 主线程。
- [ ] **数据持久化**：
    - 保存用户转换历史（可选，需考虑隐私）。
    - 保存用户偏好配置（云端同步）。

## 4. 增强功能 (Premium Features)
为付费用户提供差异化价值。

- [ ] **云端存储集成**：一键保存到 Notion, Obsidian (Sync), Google Drive。
- [ ] **自定义模板**：允许用户定义 Markdown 转换模板（如 Frontmatter 格式、自定义 CSS 类名映射）。
- [ ] **批量处理**：上传 HTML 文件包或 Sitemap URL，批量导出 Markdown。
- [ ] **API Access**：开放 REST API 给开发者使用。

## 5. 运营与合规 (Operations & Compliance)
- [ ] **官网与文档**：建立 Landing Page，提供详细 API 文档。
- [ ] **法律合规**：
    - 服务条款 (TOS)
    - 隐私政策 (Privacy Policy) - 特别说明数据处理方式（是否存储 HTML 内容）。
    - GDPR/CCPA 合规。
- [ ] **可观测性**：接入 Sentry (错误追踪) 和 Prometheus/Grafana (性能监控)。

## 6. 推广 (Growth)
- [ ] **Chrome Store 优化**：精美截图、视频演示、SEO 关键词。
- [ ] **Product Hunt 发布**。
- [ ] **SEO 内容营销**：发布关于 "HTML to Markdown", "Web Scraper", "Content Migration" 的技术博客。

## 阶段规划建议

### Phase 1: MVP Commercial (基础商业化)
- 引入数据库和 API Key。
- 实现 Redis 限流。
- 简单的 Stripe Checkout 集成（仅 Pro 月付）。
- 插件端增加 "Login / Enter API Key" 选项。

### Phase 2: Ecosystem (生态集成)
- Notion/Obsidian 集成。
- 开放开发者 API。
- 完善的后台管理面板。
