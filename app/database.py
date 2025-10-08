from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .settings import get_settings
from .models import Base

_settings = get_settings()

# SQLite ise check_same_thread bayrağı lazım
connect_args = {"check_same_thread": False} if _settings.DATABASE_URL.startswith(
    "sqlite") else {}

engine = create_engine(_settings.DATABASE_URL,
                       connect_args=connect_args, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
