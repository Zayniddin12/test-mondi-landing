from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    yolda_base_url: str = ""
    yolda_key: str = ""
    yolda_webhook_secret: str = ""
    default_delivery_fee: int = 15000
    cors_origins: str = "http://localhost:3000"


settings = Settings()
