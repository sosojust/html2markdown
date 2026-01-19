from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import os

class ApiConfig(BaseModel):
    MAX_HTML_LENGTH: int = 5_000_000
    PROCESS_TIMEOUT_MS: int = 3000
    AUTH_ENABLED: bool = False
    AUTH_TOKEN: str = ""
    RL_ENABLED: bool = False
    RL_WINDOW_MS: int = 60_000
    RL_MAX: int = 60
    MAX_FETCH_LENGTH: int = 3_000_000
    HTTP_USER_AGENT: str = "html-to-md/0.1 (+https://example.local)"
    MAX_REDIRECTS: int = 5
    DATABASE_URL: str = "postgresql+asyncpg://md_user:md_password@localhost:5432/md_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    @classmethod
    def from_env(cls):
        load_dotenv(find_dotenv(), override=False)
        def _env_str(key: str, default: str) -> str:
            v = os.getenv(key)
            return v if v is not None else default
        def _env_bool(key: str, default: bool) -> bool:
            v = os.getenv(key)
            if v is None:
                return default
            return v.strip() in ("1", "true", "TRUE", "yes", "on")
        def _env_int(key: str, default: int) -> int:
            v = os.getenv(key)
            try:
                return int(v) if v is not None else default
            except Exception:
                return default
        return cls(
            MAX_HTML_LENGTH=_env_int("MAX_HTML_LENGTH", cls.model_fields["MAX_HTML_LENGTH"].default),
            PROCESS_TIMEOUT_MS=_env_int("PROCESS_TIMEOUT_MS", cls.model_fields["PROCESS_TIMEOUT_MS"].default),
            AUTH_ENABLED=_env_bool("AUTH_ENABLED", cls.model_fields["AUTH_ENABLED"].default),
            AUTH_TOKEN=_env_str("AUTH_TOKEN", cls.model_fields["AUTH_TOKEN"].default),
            RL_ENABLED=_env_bool("RL_ENABLED", cls.model_fields["RL_ENABLED"].default),
            RL_WINDOW_MS=_env_int("RL_WINDOW_MS", cls.model_fields["RL_WINDOW_MS"].default),
            RL_MAX=_env_int("RL_MAX", cls.model_fields["RL_MAX"].default),
            MAX_FETCH_LENGTH=_env_int("MAX_FETCH_LENGTH", cls.model_fields["MAX_FETCH_LENGTH"].default),
            HTTP_USER_AGENT=_env_str("HTTP_USER_AGENT", cls.model_fields["HTTP_USER_AGENT"].default),
            MAX_REDIRECTS=_env_int("MAX_REDIRECTS", cls.model_fields["MAX_REDIRECTS"].default),
            DATABASE_URL=_env_str("DATABASE_URL", cls.model_fields["DATABASE_URL"].default),
            REDIS_URL=_env_str("REDIS_URL", cls.model_fields["REDIS_URL"].default),
            SECRET_KEY=_env_str("SECRET_KEY", cls.model_fields["SECRET_KEY"].default),
            ALGORITHM=_env_str("ALGORITHM", cls.model_fields["ALGORITHM"].default),
            ACCESS_TOKEN_EXPIRE_MINUTES=_env_int("ACCESS_TOKEN_EXPIRE_MINUTES", cls.model_fields["ACCESS_TOKEN_EXPIRE_MINUTES"].default),
        )
