from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# A FastAPI dependency: FastAPI calls this per-request, hands the route the
# yielded session, and runs the code after `yield` once the request is done -
# so the connection is always closed even if the route raises.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
