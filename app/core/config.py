"""
Configuration management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = "BackBone-AI"
    app_version: str = "0.1.0"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "INFO"

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_workers: int = 1

    # LLM Provider Settings
    default_llm_provider: Literal["openai", "anthropic", "google"] = "openai"

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = "gpt-4-turbo-preview"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 4096

    # Anthropic
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_temperature: float = 0.1
    anthropic_max_tokens: int = 4096

    # Google
    google_api_key: str = Field(default="", description="Google API key")
    google_model: str = "gemini-1.5-pro"
    google_temperature: float = 0.1

    # Agent Configuration
    orchestrator_llm_provider: str = "anthropic"
    orchestrator_model: str = "claude-3-5-sonnet-20241022"
    orchestrator_max_iterations: int = 10

    schema_validator_llm_provider: str = "openai"
    schema_validator_model: str = "gpt-4-turbo-preview"

    architect_llm_provider: str = "openai"
    architect_model: str = "gpt-4-turbo-preview"

    code_generator_llm_provider: str = "openai"
    code_generator_model: str = "gpt-4"

    validator_llm_provider: str = "openai"
    validator_model: str = "gpt-3.5-turbo"

    # Database Settings
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/backbone_generated"
    database_echo: bool = False
    internal_db_url: str = (
        "postgresql+asyncpg://user:password@localhost:5432/backbone_internal"
    )

    # LangChain & LangSmith
    langchain_tracing_v2: bool = False
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: str = Field(default="", description="LangSmith API key")
    langchain_project: str = "BackBone-AI"

    # Code Generation
    output_dir: str = "./generated_projects"
    template_dir: str = "./templates"
    auto_format: bool = True
    auto_lint: bool = True

    # Retry & Timeout
    agent_max_retries: int = 3
    agent_retry_delay: int = 1
    agent_timeout: int = 300

    llm_max_retries: int = 3
    llm_retry_delay: int = 2

    # Monitoring
    enable_metrics: bool = False
    metrics_port: int = 9090

    # Security & Authentication
    api_key: str = Field(default="", description="API authentication key")
    enable_auth: bool = False

    # JWT Settings
    jwt_secret_key: str = Field(default="", description="JWT secret key")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Input Validation Limits
    max_json_size: int = 10 * 1024 * 1024  # 10 MB
    max_tables: int = 50
    max_columns_per_table: int = 100
    max_relationships_per_table: int = 50

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Feature Flags
    enable_streaming: bool = True
    enable_human_feedback: bool = False
    enable_tests_generation: bool = False

    # Development
    test_mode: bool = False
    mock_llm: bool = False

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    def get_llm_config(self, provider: str | None = None) -> dict:
        """Get LLM configuration for a specific provider."""
        provider = provider or self.default_llm_provider

        if provider == "openai":
            return {
                "api_key": self.openai_api_key,
                "model": self.openai_model,
                "temperature": self.openai_temperature,
                "max_tokens": self.openai_max_tokens,
            }
        elif provider == "anthropic":
            return {
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
                "temperature": self.anthropic_temperature,
                "max_tokens": self.anthropic_max_tokens,
            }
        elif provider == "google":
            return {
                "api_key": self.google_api_key,
                "model": self.google_model,
                "temperature": self.google_temperature,
            }
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Export settings instance
settings = get_settings()
