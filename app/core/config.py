from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str
    llm_model: str = "gemini-1.5-flash"
    llm_provider: str = "gemini"

    class Config:
        env_file = ".env"


settings = Settings()
