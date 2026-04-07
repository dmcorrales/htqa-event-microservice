import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.database import get_session
from src.config.dependencies import get_event_service
from src.infrastructure.persistence.models import Base
from src.infrastructure.cache.memory_idempotency_store import MemoryIdempotencyStore
from src.infrastructure.notifications.log_notifier import LogNotifier
from src.infrastructure.persistence.event_repository_impl import SqlAlchemyEventRepository
from src.domain.rules.severity_classifier import SeverityClassifier
from src.application.services.event_service import EventService

TEST_DB_URL = "sqlite+aiosqlite:///./test_events.db"

engine = create_async_engine(TEST_DB_URL, echo=False)
test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def idempotency_store():
    return MemoryIdempotencyStore()


@pytest_asyncio.fixture
async def event_service(db_session, idempotency_store):
    repository = SqlAlchemyEventRepository(db_session)
    notifier = LogNotifier()
    classifier = SeverityClassifier()
    return EventService(
        repository=repository,
        idempotency_store=idempotency_store,
        notifier=notifier,
        classifier=classifier,
    )


@pytest_asyncio.fixture
async def client(db_session, idempotency_store) -> AsyncGenerator[AsyncClient, None]:
    from main import create_app

    app = create_app()

    async def _override_session():
        yield db_session

    async def _override_service():
        repository = SqlAlchemyEventRepository(db_session)
        notifier = LogNotifier()
        classifier = SeverityClassifier()
        return EventService(
            repository=repository,
            idempotency_store=idempotency_store,
            notifier=notifier,
            classifier=classifier,
        )

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_event_service] = _override_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
