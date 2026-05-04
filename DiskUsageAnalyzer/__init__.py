import os

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra="allow")
    DEBUG: bool = True

    DB_USER: str = 'postgres'
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "db_diagrams"

    SECRET_KEY: str = "ufufhgfugf"

    def sqlite_dsn(self) -> str:
        return f"sqlite+aiosqlite:///./{self.DB_NAME}.db"


settings_app = Settings()

# Створення асинхронного движка бази даних
DATABASE_URL = settings_app.sqlite_dsn()
engine = create_async_engine(DATABASE_URL, echo=True)

# Сесія для асинхронної роботи з базою даних
async_session = async_sessionmaker(bind=engine, class_=AsyncSession)

# Створюємо базовий клас для моделей
class Base(AsyncAttrs, DeclarativeBase):
    pass
