from typing import Generator

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


class Settings(BaseSettings):
    postgres_db: str = "calidad_aire_db"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "db"
    postgres_port: int = 5432
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@db:5432/calidad_aire_db"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
