import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

logger = logging.getLogger("hiringbuddy.database")

# For development, we'll use SQLite. In production, change DATABASE_URL to PostgreSQL
engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added after the initial schema. For SQLite dev DBs, create_all() will
# not ALTER existing tables, so we add any missing columns idempotently here.
_ADDITIVE_COLUMNS = {
    "candidates": {
        "role_applied": "VARCHAR",
        "education": "JSON",
        "languages": "JSON",
        "email_status": "VARCHAR DEFAULT 'none'",
        "notes": "TEXT",
        "interview_token_expiry": "VARCHAR",
        "interview_score": "FLOAT DEFAULT 0.0",
        "proctoring_warnings": "JSON",
        "interview_report": "JSON",
        "organization_id": "INTEGER",
    },
    "interviews": {
        "score": "FLOAT DEFAULT 0.0",
        "integrity_score": "FLOAT DEFAULT 100.0",
        "warnings": "JSON",
        "transcript": "JSON",
        "created_at": "VARCHAR",
    },
}


def ensure_schema():
    """Idempotently add newly-introduced columns to existing tables."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _ADDITIVE_COLUMNS.items():
            if table not in existing_tables:
                continue  # create_all() will build it fresh with all columns
            present = {c["name"] for c in inspector.get_columns(table)}
            for col, ddl in columns.items():
                if col not in present:
                    logger.info("Migrating: adding %s.%s", table, col)
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {ddl}'))
