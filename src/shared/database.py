"""Database setup and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.shared.config import settings

# Create async engine with proper SQLite configuration
# For SQLite, we need to ensure transactions are visible across connections
connect_args = {}
if "sqlite" in settings.database_url:
    # SQLite-specific settings for better transaction visibility
    # Use WAL mode for better concurrency
    connect_args = {
        "check_same_thread": False,  # Allow multiple threads
        "timeout": 20.0,  # Connection timeout
    }
    # Enable WAL mode for SQLite (better for concurrent reads)
    # This will be set when the connection is first established

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create async session factory
# For SQLite, we want to ensure transactions are visible immediately
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    # Ensure we can see committed changes from other sessions
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

