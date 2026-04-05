from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from data_layer_manager.core.config import get_settings

settings = get_settings()

if not settings.database.url:
    # Fallback to absolute default if env/yaml is missing
    DATABASE_URL = "postgresql://dlm_user:password@localhost:5432/dlm_db"
else:
    DATABASE_URL = settings.database.url

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=True,  # Critical for debugging the'Limited Mode' integration
    connect_args={"options": "-c timezone=utc"},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
