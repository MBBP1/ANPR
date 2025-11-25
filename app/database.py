from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import SQLALCHEMY_DATABASE_URL

# sync engine (simple for student project)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Helper dependency for FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
