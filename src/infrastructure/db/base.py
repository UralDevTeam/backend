from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings

engine = create_async_engine(
    settings.postgres.db_url,
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
