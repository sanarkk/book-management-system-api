import random
import pytest
import pytest_asyncio

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db.database import async_session


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with async_session() as session:
        yield session


"""ASYNC FIXTURE ERROR"""
# @pytest_asyncio.fixture
# async def token(async_client: AsyncClient):
#     # User registration
#     random_username = random.randint(0, 9999999999)
#     response = await async_client.post(
#         "/auth/register",
#         json={
#             "username": f"{random_username}",
#             "first_name": "Test",
#             "last_name": "Test",
#             "email": f"{random_username}@test.com",
#             "password": "test_password",
#         },
#     )
#     assert response.status_code == 200
#
#     # Login to get token
#     response = await async_client.post(
#         "/auth/login",
#         json={"username": random_username, "password": "test_password"},
#     )
#     assert response.status_code == 200, response.text
#
#     return response.json()["access_token"]
