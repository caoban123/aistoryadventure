from __future__ import annotations
from pydantic import computed_field
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Story Adventure"
    app_env: str = "local"
    strict_startup_checks: bool = False
    api_prefix: str = ""
    cors_origins: str = "*"
    kaggle_backend_url: str = "https://onion-vertical-squash.ngrok-free.dev"

    text_provider: str = "openai"
    openai_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    ollama_model: str = "qwen3.5:9b"

# text_model: str = "gemini-2.5-flash"  # deprecated, use active_model

    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"
    groq_api_key: str | None = None

    openai_api_keys: str = ""
    gemini_api_keys: str = ""
    groq_api_keys: str = ""
    
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
    qdrant_https: bool = False
    embedding_provider: str = "simple"  # simple first; upgrade later to openai
    max_recent_messages: int = 8
    max_relevant_memories: int = 6
    admin_token: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.app_env.lower().strip() in {"prod", "production"}

    @computed_field
    @property
    def gemini_key_list(self) -> list[str]:
        return [
            k.strip()
            for k in self.gemini_api_keys.split(",")
            if k.strip()
        ]

    @computed_field
    @property
    def groq_key_list(self) -> list[str]:
        return [
            k.strip()
            for k in self.groq_api_keys.split(",")
            if k.strip()
        ]

    @computed_field
    @property
    def openai_key_list(self) -> list[str]:
        return [
            k.strip()
            for k in self.openai_api_keys.split(",")
            if k.strip()
        ]
        
    @computed_field
    @property
    def text_model(self) -> str:
        prov = self.text_provider.lower().strip()
        if prov == "round_robin":
            return (
                f"round_robin(gemini:{self.gemini_model},"
                f"groq:{self.groq_model},"
                f"ollama:{self.ollama_model})"
            )
        if prov == "openai":
            return self.openai_model
        if prov == "gemini":
            return self.gemini_model
        if prov == "groq":
            return self.groq_model
        if prov == "ollama":
            return self.ollama_model
        return "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
