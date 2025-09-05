# from sqlalchemy import create_engine
# from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from core.config import settings
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Create database engine
# def _sanitize_database_url(raw_url: str) -> str:
#     """Remove unsupported query params (e.g., pgbouncer=true) for psycopg2."""
#     try:
#         parsed = urlparse(raw_url)
#         query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
#         # psycopg2 rejects unknown options; remove Supabase's pgbouncer flag
#         query_params.pop("pgbouncer", None)
#         # Ensure sslmode=require when using postgres
#         if parsed.scheme.startswith("postgresql"):
#             # respect existing sslmode if provided; otherwise set require
#             query_params.setdefault("sslmode", "require")
#         sanitized_query = urlencode(query_params)
#         sanitized = urlunparse((
#             parsed.scheme,
#             parsed.netloc,
#             parsed.path,
#             parsed.params,
#             sanitized_query,
#             parsed.fragment,
#         ))
#         return sanitized
#     except Exception:
#         return raw_url

# database_url = _sanitize_database_url(settings.DATABASE_URL)

# connect_args = {}
# if database_url.startswith("postgresql"):
#     # Supabase Postgres typically requires SSL
#     connect_args = {"sslmode": "require"}
# elif database_url.startswith("sqlite"):
#     # Needed for SQLite when using multiple threads (FastAPI + SQLAlchemy)
#     connect_args = {"check_same_thread": False}

# engine = create_engine(
#     database_url,
#     pool_pre_ping=True,
#     pool_recycle=300,
#     echo=False,  # Set to True for SQL query logging
#     connect_args=connect_args,
# )

# # Create session factory
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Create base class for models
# Base = declarative_base()

# def get_db():
#     """Dependency to get database session"""
#     db = SessionLocal()
#     try:
#         yield db
#     except Exception as e:
#         logger.error(f"Database session error: {e}")
#         db.rollback()
#         raise
#     finally:
#         db.close()

# def init_db():
#     """Initialize database tables"""
#     try:
#         # Import all models here to ensure they are registered
#         from models.file import File
#         from models.report import Report
#         from models.user import User
        
#         # Create all tables
#         Base.metadata.create_all(bind=engine)
#         logger.info("Database tables created successfully")
#     except Exception as e:
#         logger.error(f"Database initialization error: {e}")
#         raise
print("--- Loading core/database.py ---")
from sqlalchemy import create_engine
print("create engine loaded")
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional
from core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- LAZY INITIALIZATION ---
# Declare these as None at the module level. They will be populated by init_db().
engine = None
SessionLocal: Optional[sessionmaker[Session]] = None
Base = declarative_base()


def _sanitize_database_url(raw_url: str) -> str:
    """Remove unsupported query params (e.g., pgbouncer=true) for psycopg2."""
    try:
        parsed = urlparse(raw_url)
        query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query_params.pop("pgbouncer", None)
        if parsed.scheme.startswith("postgresql"):
            query_params.setdefault("sslmode", "require")
        sanitized_query = urlencode(query_params)
        sanitized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            sanitized_query,
            parsed.fragment,
        ))
        return sanitized
    except Exception:
        return raw_url


def get_db():
    """Dependency to get database session"""
    # First, check if the SessionLocal has been created.
    if SessionLocal is None:
        raise RuntimeError("Database is not initialized. Call init_db() on startup.")
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """
    Initialize the database engine, session, and tables.
    This function should be called ONCE during application startup.
    """
    global engine, SessionLocal
    
    # Provide a safe default if DATABASE_URL is not set
    raw_url = settings.DATABASE_URL or "sqlite:///./app.db"
    database_url = _sanitize_database_url(raw_url)

    connect_args = {}
    try:
        if database_url.startswith("postgresql"):
            connect_args = {"sslmode": "require"}
        elif database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
    except Exception:
        # As an extreme fallback, ensure we have a valid SQLite URL
        database_url = "sqlite:///./app.db"
        connect_args = {"check_same_thread": False}

    # Create the engine and session maker here, inside the function
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False,
        connect_args=connect_args,
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info("Database engine and session created.")

    try:
        # Import all models here to ensure they are registered
        from models.file import File
        from models.report import Report
        from models.user import User
        from models.announcement import Announcement
        from models.company_financial import CompanyFinancial
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables checked/created successfully.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise
