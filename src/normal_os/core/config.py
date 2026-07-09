"""Configuration management using Pydantic Settings (March 2026 style)."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Application settings."""

    # LLM Configuration
    default_llm_provider: Literal["openai", "anthropic", "grok", "ollama"] = "grok"
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    grok_api_key: str | None = Field(default=None, validation_alias="GROK_API_KEY")
    ollama_base_url: str = "http://localhost:11434"

    # QUBO / Optimization
    qubo_solver_timeout: float = 5.0
    max_qubo_variables: int = 1000

    # Dashboard
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8000

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()