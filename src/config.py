import os
from functools import lru_cache

from fastapi_mail import ConnectionConfig
from pydantic import SecretStr, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # broker settings
    BROKER_URL: str
    BROKER_MAIL_TOPIC: str
    BROKER_MAIL_CALLBACK_TOPIC: str
    BROKER_GROUP_ID: str

    # email settings
    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool

    @property
    def MAIL_CONFIG(self) -> ConnectionConfig:
        return ConnectionConfig(
            MAIL_USERNAME=self.MAIL_USERNAME,
            MAIL_PASSWORD=self.MAIL_PASSWORD,
            MAIL_FROM=self.MAIL_FROM,
            MAIL_PORT=self.MAIL_PORT,
            MAIL_SERVER=self.MAIL_SERVER,
            MAIL_FROM_NAME=self.MAIL_FROM_NAME,
            MAIL_STARTTLS=self.MAIL_STARTTLS,
            MAIL_SSL_TLS=self.MAIL_SSL_TLS,
        )

    model_config = SettingsConfigDict(extra="allow")


@lru_cache
def get_settings() -> Settings:
    environment = os.environ.get("ENVIRONMENT", "dev")
    env_file = f".{environment.lower()}.env"
    return Settings(_env_file=env_file)
