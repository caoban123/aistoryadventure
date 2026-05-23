from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Story Adventure"
    app_env: str = "local"
    strict_startup_checks: bool = False
    api_prefix: str = ""
    cors_origins: str = "*"

    text_provider: str = "openai"  
    text_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"
    groq_api_key: str | None = None
    
    firebase_project_id: str | None = None
    firebase_credentials_path: str | None = None
    firebase_service_account_json: str | None = None
    firestore_timeout_seconds: float = 5.0
    use_local_store_if_firebase_missing: bool = True
    local_data_dir: str = "data"

    chroma_persist_dir: str = "chroma_db"
    vector_db: str = "chroma"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    embedding_provider: str = "simple"  # simple first; upgrade later to openai
    max_recent_messages: int = 8
    max_relevant_memories: int = 6
    admin_token: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower().strip() in {"prod", "production"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
