from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

load_dotenv()


class BotSettings(BaseSettings):
    SECRET_KEY: SecretStr = Field(..., env="SECRET_KEY")
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: SecretStr = Field(..., env="ADMIN_PASSWORD")
    TOKEN: SecretStr = Field(..., env="TOKEN")
    WEBHOOK_HOST: str
    WEBHOOK_PATH: str
    WEBHOOK_URL: str
    IS_POLLING: bool = False
    WEBAPP_HOST: str
    WEBAPP_PORT: int
    LOG_QUERY: bool = False

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


class SQLAlchemyOrmSettings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


class RedisSettings(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


bot_settings = BotSettings()
sqlalchemy_orm_settings = SQLAlchemyOrmSettings()
redis_settings = RedisSettings()

SQLALCHEMY_ORM_CONFIG = {
    "url": f"postgresql+asyncpg://{sqlalchemy_orm_settings.POSTGRES_USER}:"
    f"{sqlalchemy_orm_settings.POSTGRES_PASSWORD}@"
    f"{sqlalchemy_orm_settings.POSTGRES_HOST}:"
    f"{sqlalchemy_orm_settings.POSTGRES_PORT}/"
    f"{sqlalchemy_orm_settings.POSTGRES_DB}",
    "echo": bot_settings.LOG_QUERY,
}
