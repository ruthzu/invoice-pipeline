from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str
    # llm_model: str = "gemini-3.6-flash"
    llm_model: str = "gemini-2.5-flash"
    llm_provider: str = "gemini"
    storage_dir: str = "/app/storage"
    max_upload_size_mb: int = 10

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env without validation errors


settings = Settings()