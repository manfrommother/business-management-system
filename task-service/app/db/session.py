# task-service/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional

from app.core.config import settings

engine = create_engine(settings.DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db(user_id: Optional[int] = None) -> Generator[Session, None, None]:
    db = SessionLocal()
    if user_id:
        db.info['user_id'] = user_id
    try:
        yield db
    finally:
        db.close() 