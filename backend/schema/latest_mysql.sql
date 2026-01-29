-- latest.sql
-- Compatible with MySQL
-- 用户表与API密钥表结构定义

-- 表名: users
-- 描述: 存储系统的注册用户信息，用于鉴权和配额管理
CREATE TABLE IF NOT EXISTS users (
    id CHAR(36) PRIMARY KEY COMMENT '用户唯一标识 (UUID)',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT '用户邮箱，用于登录和唯一标识',
    password_hash VARCHAR(255) COMMENT '加密后的密码哈希值',
    tier VARCHAR(50) DEFAULT 'free' COMMENT '用户等级 (free/pro/admin)，决定API限流配额',
    preferences TEXT COMMENT '用户偏好设置 (JSON String)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '账户创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '账户最后更新时间',
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储系统的注册用户信息';

-- 表名: api_keys
-- 描述: 存储用户的 API 访问密钥，用于无需登录的接口调用鉴权
CREATE TABLE IF NOT EXISTS api_keys (
    id CHAR(36) PRIMARY KEY COMMENT '密钥唯一标识 (UUID)',
    user_id CHAR(36) NOT NULL COMMENT '关联的用户ID，外键',
    key_hash VARCHAR(255) NOT NULL UNIQUE COMMENT 'API Key 的安全哈希值（不存明文）',
    prefix VARCHAR(50) NOT NULL COMMENT 'Key 的前缀（如 sk_live_abc...），用于前端展示',
    name VARCHAR(100) COMMENT '用户给 Key 起的别名/备注',
    is_active BOOLEAN DEFAULT TRUE COMMENT '密钥状态：TRUE=启用，FALSE=禁用',
    expires_at TIMESTAMP NULL COMMENT '密钥过期时间（可选，NULL表示永不过期）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '密钥创建时间',
    last_used_at TIMESTAMP NULL COMMENT '密钥最后一次被使用的时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_api_keys_key_hash (key_hash),
    INDEX idx_api_keys_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储用户的 API 访问密钥';
