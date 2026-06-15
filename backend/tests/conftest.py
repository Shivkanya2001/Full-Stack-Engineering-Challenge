import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import hash_password
from app.database import get_db
from app.main import app
from app.models.base import Base
from app.models.user import UserModel

settings = get_settings()


class FakeRedis:
    def __init__(self):
        self._data: dict[str, int] = {}

    async def get(self, key: str):
        return str(self._data.get(key)) if key in self._data else None

    async def delete(self, key: str):
        self._data.pop(key, None)

    def pipeline(self):
        return self

    async def incr(self, key: str):
        self._data[key] = self._data.get(key, 0) + 1

    async def expire(self, key: str, ttl: int):
        pass

    async def execute(self):
        pass

    async def ping(self):
        return True


@pytest_asyncio.fixture(autouse=True)
async def mock_redis(monkeypatch):
    fake = FakeRedis()

    async def _get_redis():
        return fake

    monkeypatch.setattr("app.integrations.redis_client.get_redis", _get_redis)
    monkeypatch.setattr("app.services.auth_service.get_redis", _get_redis)
    return fake


@pytest_asyncio.fixture
async def engine():
    test_engine = create_async_engine(settings.database_url, echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client, session):
    user = UserModel(
        email="test@example.com",
        password_hash=hash_password("password123"),
        full_name="Test User",
        default_currency="USD",
    )
    session.add(user)
    await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user
