from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    sqlite3_db_fn: str = "/sqlite3-data/data.db"

settings = Settings()
