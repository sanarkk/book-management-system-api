import pytest
import random

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(async_client: AsyncClient):
    """FUNCTION TO TEST REGISTRATION AND AUTHENTICATION"""

    # User registration
    random_username = random.randint(0, 9999999999)
    response = await async_client.post(
        "/auth/register",
        json={
            "username": f"{random_username}",
            "first_name": "Test",
            "last_name": "Test",
            "email": f"{random_username}@test.com",
            "password": "test_password",
        },
    )
    assert response.status_code == 200

    # User authentication
    response = await async_client.post(
        "/auth/login",
        json={"username": f"{random_username}", "password": "test_password"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
