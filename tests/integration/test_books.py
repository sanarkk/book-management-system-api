# import pytest

# from httpx import AsyncClient

"""ASYNC FIXTURE ERROR"""

# @pytest.mark.asyncio
# async def test_create_and_get_book(async_client: AsyncClient, token: str):
#     headers = {"Authorization": f"Bearer {token}"}
#
#     # Book creation
#     response = await async_client.post(
#         "/api/books/create",
#         headers=headers,
#         json={"title": "New Test Book", "genre": "Science", "published_year": 2025},
#     )
#     assert response.status_code == 200
#     data = response.json()
#     assert data["title"] == "New Test Book"
#
#     # Retrieving all books
#     response = await async_client.post(
#         "/api/books/get", headers=headers, json={"title": "New Test Book"}
#     )
#     assert response.status_code == 200, response.text
#     assert any(book["title"] == "New Test Book" for book in response.json())
