from fastapi import FastAPI

from app.api import book, auth


def application_factory(openapi_url: str = "/openapi.json") -> FastAPI:
    app = FastAPI(openapi_url=openapi_url)

    app.include_router(auth.router)
    app.include_router(book.router, prefix="/api/books", tags=["books"])

    return app


app = application_factory()
