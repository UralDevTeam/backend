from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings
from src.infrastructure.db.models.base import Base

engine = create_async_engine(
    settings.postgres.db_url,
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def init_models() -> None:
    """Ensure all database tables are created."""
    # Import models so that they are registered on the SQLAlchemy metadata
    import src.infrastructure.db.models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)