from enum import Enum
from pydantic import BaseModel, Field
from typing import Literal

from app.schemas.user import UserOut


class GenreEnum(str, Enum):
    fiction = "Fiction"
    non_fiction = "Non-Fiction"
    science = "Science"
    history = "History"


class BookBase(BaseModel):
    title: str
    genre: GenreEnum
    published_year: int


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = None
    genre: GenreEnum | None = None
    published_year: int | None = None


class BookOut(BookBase):
    id: int
    title: str
    genre: str
    published_year: int
    author: UserOut

    class Config:
        from_attributes = True


class BookFilter(BaseModel):
    title: str | None = None
    author: str | None = None
    genre: str | None = None
    year_from: int | None = None
    year_to: int | None = None

    limit: int = Field(10, ge=1, le=100, description="Limit number of results")
    offset: int = Field(0, ge=0, description="Skip number of results")

    sort_by: Literal["title", "published_year", "author"] = Field("title")
    sort_order: Literal["asc", "desc"] = Field("asc")
