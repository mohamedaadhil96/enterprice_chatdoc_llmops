import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Default to the info provided by user, password defaults to 'postgres' for now
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1234@localhost:5432/doc_chat")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import multi_doc_chat.utils.models # Import models to register them
    Base.metadata.create_all(bind=engine)
