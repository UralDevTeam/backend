import pathlib
from typing import Optional

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = pathlib.Path(__file__).parent.parent.parent / ".env"


class PostgresSettings(BaseSettings):
    host: str
    port: int
    db_name: str
    user: SecretStr
    password: SecretStr

    model_config = SettingsConfigDict(extra="forbid")

    @property
    def db_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.user.get_secret_value(),
                password=self.password.get_secret_value(),
                host=self.host,
                port=self.port,
                path=self.db_name,
            )
        )


class ActiveDirectorySettings(BaseSettings):
    host: str
    base_dn: str

    port: int = 389
    use_ssl: bool = False
    user: Optional[str] = None
    password: Optional[SecretStr] = None
    page_size: int = 1000

    model_config = SettingsConfigDict(extra="forbid")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_nested_delimiter="__",  # <-- FIX: безопасный разделитель для вложенных моделей
        extra="forbid",
    )

    postgres: PostgresSettings

    ad: Optional[ActiveDirectorySettings] = None


settings = Settings()
