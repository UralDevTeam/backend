import pathlib
from typing import Optional

from pydantic import AmqpDsn, Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = pathlib.Path(__file__).parent.parent.parent / ".env"


class PostgresSettings(BaseSettings):
    host: str
    port: int
    db_name: str
    user: SecretStr
    password: SecretStr

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
            ),
        )


class ActiveDirectorySettings(BaseSettings):
    host: str = "10.51.4.16"
    port: int = 389
    use_ssl: bool = False
    user: Optional[str] = None
    password: Optional[SecretStr] = None
    base_dn: str = "DC=stud,DC=local"
    page_size: int = 1000

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__", env_file=ENV_FILE)
    postgres: PostgresSettings
    ad: ActiveDirectorySettings = Field(default_factory=ActiveDirectorySettings)


settings = Settings()
