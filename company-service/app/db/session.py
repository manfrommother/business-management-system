from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Создаем движок SQLAlchemy
# pool_pre_ping=True проверяет соединение перед каждым запросом
engine = create_engine(
    settings.DATABASE_URI,
    pool_pre_ping=True
    # Можно добавить другие параметры, например, pool_size, max_overflow
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Функция-зависимость для получения сессии БД в эндпоинтах FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()