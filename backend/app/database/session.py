from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

from pathlib import Path

if settings.DATABASE_URL.startswith("sqlite:///"):
    sqlite_file = settings.DATABASE_URL.replace("sqlite:///", "")
    Path(sqlite_file).parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from backend.app.models import entities  # ensure models are imported
    Base.metadata.create_all(bind=engine)
