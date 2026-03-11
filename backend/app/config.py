from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.5-flash"
    openrouter_vision_model: str = "google/gemini-2.5-flash"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Paths
    upload_dir: str = "/app/uploads"
    output_dir: str = "/app/outputs"

    # Security
    cors_origins: str = "*"  # comma-separated, e.g. "https://app.example.com,http://localhost:3000"

    # Limits
    max_upload_size_mb: int = 50

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
