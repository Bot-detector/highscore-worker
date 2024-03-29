from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class SessionContextManager:
    async def __aenter__(self):
        self.session = await get_session()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()


# Create an async SQLAlchemy engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_timeout=settings.POOL_TIMEOUT,
    pool_recycle=settings.POOL_RECYCLE,
    echo=(settings.ENV != "PRD"),
)

# Create a session factory
SessionFactory = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,  # Use AsyncSession for asynchronous operations
)


# async def get_session() -> AsyncSession:
#     async with SessionFactory() as session:
#         yield session
async def get_session():
    yield SessionFactory()


Base = declarative_base()
