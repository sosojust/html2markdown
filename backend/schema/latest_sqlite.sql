-- latest.sql
-- Compatible with SQLite
-- 用户表与API密钥表结构定义

-- 表名: users
-- 描述: 存储系统的注册用户信息，用于鉴权和配额管理
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,                       -- 用户唯一标识 (UUID)
    email TEXT NOT NULL UNIQUE,                -- 用户邮箱，用于登录和唯一标识
    password_hash TEXT,                        -- 加密后的密码哈希值
    tier TEXT DEFAULT 'free',                  -- 用户等级 (free/pro/admin)，决定API限流配额
    preferences TEXT,                          -- 用户偏好设置 (JSON String)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 账户创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- 账户最后更新时间
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 表名: api_keys
-- 描述: 存储用户的 API 访问密钥，用于无需登录的接口调用鉴权
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,                       -- 密钥唯一标识 (UUID)
    user_id TEXT NOT NULL,                     -- 关联的用户ID，外键
    key_hash TEXT NOT NULL UNIQUE,             -- API Key 的安全哈希值（不存明文）
    prefix TEXT NOT NULL,                      -- Key 的前缀（如 sk_live_abc...），用于前端展示
    name TEXT,                                 -- 用户给 Key 起的别名/备注
    is_active BOOLEAN DEFAULT 1,               -- 密钥状态：1=启用，0=禁用
    expires_at DATETIME,                       -- 密钥过期时间（可选，NULL表示永不过期）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 密钥创建时间
    last_used_at DATETIME,                     -- 密钥最后一次被使用的时间
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
