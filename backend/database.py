"""
Database configuration and session management
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    """
    import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
    _run_schema_migrations()


def _run_schema_migrations():
    """
    Lightweight schema migrations for existing installations.
    Currently ensures the sessions table has the requirements column,
    the messages table has target_listing_id, and the listings table has description.
    """
    inspector = inspect(engine)

    try:
        session_columns = [col["name"] for col in inspector.get_columns("sessions")]
    except Exception:
        return

    if "requirements" not in session_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE sessions ADD COLUMN requirements TEXT"))

    try:
        message_columns = [col["name"] for col in inspector.get_columns("messages")]
    except Exception:
        return

    if "target_listing_id" not in message_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE messages ADD COLUMN target_listing_id TEXT"))

    try:
        listing_columns = [col["name"] for col in inspector.get_columns("listings")]
    except Exception:
        return

    if "description" not in listing_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE listings ADD COLUMN description TEXT"))
