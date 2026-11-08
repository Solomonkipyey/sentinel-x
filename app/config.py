from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/sentinel.db"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    NEWS_FEEDS: str = (
        "https://www.bleepingcomputer.com/feed/,"
        "https://thehackernews.com/feeds/posts/default,"
        "https://krebsonsecurity.com/feed/"
    )
    POLL_INTERVAL_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()