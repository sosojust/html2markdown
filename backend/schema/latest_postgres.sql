-- latest.sql
-- Compatible with PostgreSQL
-- 用户表与API密钥表结构定义

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 表名: users
-- 描述: 存储系统的注册用户信息，用于鉴权和配额管理
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),          -- 用户唯一标识 (UUID)
    email VARCHAR(255) NOT NULL UNIQUE,                      -- 用户邮箱，用于登录和唯一标识
    password_hash VARCHAR(255),                              -- 加密后的密码哈希值
    tier VARCHAR(50) DEFAULT 'free',                         -- 用户等级 (free/pro/admin)，决定API限流配额
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- 账户创建时间
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP  -- 账户最后更新时间
);

COMMENT ON TABLE users IS '存储系统的注册用户信息';
COMMENT ON COLUMN users.id IS '用户唯一标识 (UUID)';
COMMENT ON COLUMN users.email IS '用户邮箱，用于登录和唯一标识';
COMMENT ON COLUMN users.password_hash IS '加密后的密码哈希值';
COMMENT ON COLUMN users.tier IS '用户等级 (free/pro/admin)，决定API限流配额';
COMMENT ON COLUMN users.created_at IS '账户创建时间';
COMMENT ON COLUMN users.updated_at IS '账户最后更新时间';

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 表名: api_keys
-- 描述: 存储用户的 API 访问密钥，用于无需登录的接口调用鉴权
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),          -- 密钥唯一标识 (UUID)
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- 关联的用户ID，外键
    key_hash VARCHAR(255) NOT NULL UNIQUE,                   -- API Key 的安全哈希值（不存明文）
    prefix VARCHAR(50) NOT NULL,                             -- Key 的前缀（如 sk_live_abc...），用于前端展示
    name VARCHAR(100),                                       -- 用户给 Key 起的别名/备注
    is_active BOOLEAN DEFAULT TRUE,                          -- 密钥状态：TRUE=启用，FALSE=禁用
    expires_at TIMESTAMP WITH TIME ZONE,                     -- 密钥过期时间（可选，NULL表示永不过期）
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- 密钥创建时间
    last_used_at TIMESTAMP WITH TIME ZONE                    -- 密钥最后一次被使用的时间
);

COMMENT ON TABLE api_keys IS '存储用户的 API 访问密钥';
COMMENT ON COLUMN api_keys.id IS '密钥唯一标识 (UUID)';
COMMENT ON COLUMN api_keys.user_id IS '关联的用户ID';
COMMENT ON COLUMN api_keys.key_hash IS 'API Key 的安全哈希值';
COMMENT ON COLUMN api_keys.prefix IS 'Key 的前缀用于展示';
COMMENT ON COLUMN api_keys.name IS '密钥别名';
COMMENT ON COLUMN api_keys.is_active IS '密钥是否启用';
COMMENT ON COLUMN api_keys.expires_at IS '密钥过期时间';
COMMENT ON COLUMN api_keys.created_at IS '密钥创建时间';
COMMENT ON COLUMN api_keys.last_used_at IS '密钥最后使用时间';

CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
