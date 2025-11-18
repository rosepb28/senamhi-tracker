"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.settings import settings

# Use effective database URL (PostgreSQL if configured, SQLite otherwise)
engine = create_engine(
    settings.get_effective_database_url(),
    echo=settings.db_echo,
    # SQLite specific: allow same thread access
    connect_args={"check_same_thread": False} if not settings.is_postgresql else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
