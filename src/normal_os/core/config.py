from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "NormalOS"
    environment: Literal["development", "production"] = "development"
    debug: bool = True

    # Persistence
    database_url: str = "sqlite+aiosqlite:///./data/normalos.db"

    # LLM Routing
    default_llm_provider: str = "groq"
    groq_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # QUBO / Optimization
    qubo_default_solver: Literal["neal", "gpu", "auto"] = "auto"
    qubo_num_reads: int = 1000
    qubo_cache_enabled: bool = True

    # Execution
    max_concurrent_tasks: int = 8
    task_timeout_seconds: int = 300

    # Resource
    enable_gpu: bool = False
    gpu_memory_fraction: float = 0.8


settings = Settings()