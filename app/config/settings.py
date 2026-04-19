from functools import lru_cache
from typing import List

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Smart Multi-User Chatbot with Data Analytics"
    app_version: str = "1.0.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    debug: bool = False
    cors_origins_raw: str = "http://localhost:3000,http://localhost:5173"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/smart_chatbot"
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    google_api_key: str = ""
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_chat_fallback_models_raw: str = "gemini-2.0-flash-lite,gemini-1.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_fallback_models_raw: str = "models/text-embedding-004,models/embedding-001"
    llm_temperature: float = 0.2
    llm_max_output_tokens: int = 1024
    gemini_timeout_seconds: int = 30
    gemini_max_retries: int = 3

    faiss_index_dir: str = "storage/faiss"
    upload_dir: str = "storage/uploads"
    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_top_k: int = 4
    batch_embedding_size: int = 32

    socket_cors_origins_raw: str = "*"
    redis_url: str = "redis://localhost:6379/0"
    enable_cache: bool = True
    cache_ttl_seconds: int = 300

    default_latency_threshold_ms: int = 2000

    @computed_field
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @computed_field
    @property
    def socket_cors_origins(self) -> List[str]:
        if self.socket_cors_origins_raw.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.socket_cors_origins_raw.split(",") if origin.strip()]

    @computed_field
    @property
    def gemini_embedding_candidate_models(self) -> List[str]:
        candidates = [self.gemini_embedding_model]
        candidates.extend(
            [item.strip() for item in self.gemini_embedding_fallback_models_raw.split(",") if item.strip()]
        )
        seen: set[str] = set()
        deduped: list[str] = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                deduped.append(candidate)
        return deduped

    @computed_field
    @property
    def gemini_chat_candidate_models(self) -> List[str]:
        candidates = [self.gemini_chat_model]
        candidates.extend(
            [item.strip() for item in self.gemini_chat_fallback_models_raw.split(",") if item.strip()]
        )
        seen: set[str] = set()
        deduped: list[str] = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                deduped.append(candidate)
        return deduped


@lru_cache
def get_settings() -> Settings:
    return Settings()
