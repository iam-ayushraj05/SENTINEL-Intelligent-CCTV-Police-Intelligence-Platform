import logging

logger = logging.getLogger("sentinel.database")

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.core.config import settings

    db_url = settings.database_url
    if "sqlite" in db_url:
        engine = create_async_engine(db_url, connect_args={"check_same_thread": False})
    else:
        engine = create_async_engine(db_url, pool_pre_ping=True)

    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def get_db():
        async with AsyncSessionLocal() as session:
            yield session

except ImportError as err:
    logger.warning(f"SQLAlchemy not found ({err}). Using in-memory fallback session manager.")

    def select(*args, **kwargs):
        return None

    class DummyConnection:
        async def run_sync(self, fn, *args, **kwargs):
            pass

    class DummyEngine:
        def begin(self):
            class AsyncContext:
                async def __aenter__(self):
                    return DummyConnection()
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return AsyncContext()

    class DummySession:
        async def execute(self, stmt, *args, **kwargs):
            class DummyResult:
                def scalars(self):
                    return self
                def first(self):
                    return None
                def all(self):
                    return []
                def scalar(self):
                    return 0
            return DummyResult()

        def add(self, instance):
            pass

        async def flush(self):
            pass

        async def commit(self):
            pass

        async def refresh(self, instance):
            pass

        async def get(self, model, id):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    engine = DummyEngine()
    AsyncSessionLocal = DummySession
    AsyncSession = DummySession

    async def get_db():
        yield DummySession()
