import io
import csv
import json
import datetime

from sqlalchemy import text
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from app.models.user import User
from app.db.database import get_db
from app.core.security import get_current_user
from app.schemas.book import BookOut, BookCreate, BookUpdate, BookFilter

router = APIRouter()


@router.post("/create", response_model=BookOut, summary="Create a new book")
async def create_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CREATE A NEW BOOK"""
    if len(book.title) == 0 or book.title is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book title can't be empty",
        )

    now = datetime.datetime.now()
    if book.published_year < 1800 or book.published_year > now.year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided book year is incorrect",
        )

    new_book_query = text(
        """
        INSERT INTO books (title, genre, published_year, user_id)
        VALUES (:title, :genre, :published_year, :user_id)
        RETURNING id
    """
    )
    book_raw = await db.execute(
        new_book_query,
        {
            "title": book.title,
            "genre": book.genre,
            "published_year": book.published_year,
            "user_id": current_user.id,
        },
    )
    await db.commit()
    new_book_id = book_raw.scalar_one()

    book_query = text(
        """
        SELECT
            books.id,
            books.title,
            books.genre,
            books.published_year,
            users.id AS author_id,
            users.username AS author_username,
            users.first_name AS author_first_name,
            users.last_name AS author_last_name,
            users.email AS author_email
        FROM books
        JOIN users ON books.user_id = users.id
        WHERE books.id = :book_id
    """
    )
    book_raw = await db.execute(book_query, {"book_id": new_book_id})
    book = book_raw.one()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No book was found",
        )

    book_out = {
        "id": book.id,
        "title": book.title,
        "genre": book.genre,
        "published_year": book.published_year,
        "author": {
            "id": book.author_id,
            "username": book.author_username,
            "first_name": book.author_first_name,
            "last_name": book.author_last_name,
            "email": book.author_email,
        },
    }

    return book_out


@router.post("/get", summary="Retrieve all available books")
async def retrieve_books(
    filters: BookFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RETRIEVE ALL FILTERED BOOKS"""
    book_query = """
        SELECT
            books.id,
            books.title,
            books.genre,
            books.published_year,
            users.id AS author_id,
            users.username AS author_username,
            users.first_name AS author_first_name,
            users.last_name AS author_last_name,
            users.email AS author_email
        FROM books
        JOIN users ON books.user_id = users.id
        WHERE 1=1
    """
    params = {}

    # Filtering
    if filters.title:
        book_query += " AND books.title ILIKE :title"
        params["title"] = f"%{filters.title}%"

    if filters.author:
        book_query += """
            AND (
                users.username ILIKE :author OR
                users.first_name ILIKE :author OR
                users.last_name ILIKE :author
            )
            """
        params["author"] = f"%{filters.author}%"

    if filters.genre:
        book_query += " AND books.genre ILIKE :genre"
        params["genre"] = f"%{filters.genre}%"

    if filters.year_from:
        book_query += " AND books.published_year >= :year_from"
        params["year_from"] = filters.year_from

    if filters.year_to:
        book_query += " AND books.published_year <= :year_to"
        params["year_to"] = filters.year_to

    # Sorting
    sort_columns = {
        "title": "books.title",
        "published_year": "books.published_year",
        "author": "users.username",
    }
    book_query += (
        f" ORDER BY {sort_columns[filters.sort_by]} {filters.sort_order.upper()}"
    )

    # Pagination
    book_query += " LIMIT :limit OFFSET :offset"
    params["limit"] = filters.limit
    params["offset"] = filters.offset

    books_raw = await db.execute(text(book_query), params)
    books = books_raw.fetchall()
    if not books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No books were found",
        )

    list_of_books = [
        {
            "id": book.id,
            "title": book.title,
            "genre": book.genre,
            "published_year": book.published_year,
            "author": {
                "id": book.author_id,
                "username": book.author_username,
                "first_name": book.author_first_name,
                "last_name": book.author_last_name,
                "email": book.author_email,
            },
        }
        for book in books
    ]

    return list_of_books


@router.get("/get/my", summary="Retrieve all books created by user")
async def retrieve_my_books(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RETRIEVE ALL FILTERED BOOKS WHICH BELONG TO CURRENT USER"""
    book_query = text(
        """
            SELECT
                books.id,
                books.title,
                books.genre,
                books.published_year,
                users.id AS author_id,
                users.username AS author_username,
                users.first_name AS author_first_name,
                users.last_name AS author_last_name,
                users.email AS author_email
            FROM books
            JOIN users ON books.user_id = users.id
            WHERE books.user_id = :user_id
        """
    )

    books_raw = await db.execute(book_query, {"user_id": current_user.id})
    books = books_raw.fetchall()
    if not books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No books were found",
        )

    list_of_books = [
        {
            "id": book.id,
            "title": book.title,
            "genre": book.genre,
            "published_year": book.published_year,
            "author": {
                "id": book.author_id,
                "username": book.author_username,
                "first_name": book.author_first_name,
                "last_name": book.author_last_name,
                "email": book.author_email,
            },
        }
        for book in books
    ]

    return list_of_books


@router.get("/get/{book_id}", summary="Retrieve one book by id")
async def retrieve_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RETRIEVE ONE BOOK BY ID"""
    if not book_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Book ID has not been entered",
        )

    book_query = text(
        """
        SELECT id, title, genre, published_year, user_id
        FROM books
        WHERE id = :book_id
        """
    )
    book_raw = await db.execute(book_query, {"book_id": book_id})
    book = book_raw.first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book with such ID was not found",
        )

    user_query = text(
        """
        SELECT id, username, first_name, last_name, email
        FROM users
        WHERE id = :user_id
        """
    )
    user_raw = await db.execute(user_query, {"user_id": current_user.id})
    user = user_raw.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with such ID was not found",
        )

    book_out = {
        "id": book.id,
        "title": book.title,
        "genre": book.genre,
        "published_year": book.published_year,
        "author": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        },
    }

    return book_out


@router.put("/update/{book_id}", summary="Update one book by id")
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """UPDATE ONE BOOK"""
    if len(book_update.title) == 0 or book_update.title is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book title can't be empty",
        )

    now = datetime.datetime.now()
    if book_update.published_year < 1800 or book_update.published_year > now.year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided book year is incorrect",
        )

    book_query = text("SELECT * FROM books WHERE id = :book_id")
    book_raw = await db.execute(book_query, {"book_id": book_id})
    book = book_raw.first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book with such ID was not found",
        )

    if book.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to update this book",
        )

    update_fields = []
    params = {"book_id": book_id}

    if book_update.title is not None:
        update_fields.append("title = :title")
        params["title"] = book_update.title
    if book_update.genre is not None:
        update_fields.append("genre = :genre")
        params["genre"] = book_update.genre
    if book_update.published_year is not None:
        update_fields.append("published_year = :published_year")
        params["published_year"] = book_update.published_year

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    book_update_query = text(
        f"""
        UPDATE books
        SET {', '.join(update_fields)}
        WHERE id = :book_id
        RETURNING id, title, genre, published_year, user_id
    """
    )
    result = await db.execute(book_update_query, params)
    await db.commit()

    updated_book = result.first()
    if not updated_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book with such ID was not found",
        )

    user_query = text(
        """
        SELECT id, username, first_name, last_name, email
        FROM users
        WHERE id = :user_id
        """
    )
    user_raw = await db.execute(user_query, {"user_id": current_user.id})
    user = user_raw.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with such ID was not found",
        )

    book_out = {
        "id": updated_book.id,
        "title": updated_book.title,
        "genre": updated_book.genre,
        "published_year": updated_book.published_year,
        "author": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        },
    }

    return book_out


@router.delete(
    "/delete/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete one book by id",
)
async def delete_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """DELETE ONE BOOK"""
    book_query = text("SELECT user_id FROM books WHERE id = :book_id")
    book_raw = await db.execute(book_query, {"book_id": book_id})
    book = book_raw.first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book with such ID was not found",
        )
    if book.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to update this book",
        )

    delete_query = text("DELETE FROM books WHERE id = :book_id")
    await db.execute(delete_query, {"book_id": book_id})
    await db.commit()


@router.post("/import", summary="Bulk import books from file")
async def import_books(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """BULK IMPORT BOOKS FROM FILE"""
    if file.content_type not in ["text/csv", "application/json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be CSV or JSON"
        )

    books_to_insert = []

    if file.content_type == "text/csv":
        content = await file.read()
        decoded = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))

        for row in reader:
            try:
                if len(row["title"]) == 0 or row["title"] is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Title can't be empty",
                    )
                if (
                    int(row["published_year"]) < 1800
                    or int(row["published_year"]) > datetime.datetime.now().year
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Published year provided is incorrect",
                    )

                book_data = BookCreate(
                    title=row["title"],
                    genre=row["genre"],
                    published_year=int(row["published_year"]),
                )
                books_to_insert.append(book_data)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CSV missing required fields",
                )
            except ValidationError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Data provided is incorrect",
                )

    elif file.content_type == "application/json":
        content = await file.read()
        try:
            data = json.loads(content)
            for item in data:
                if len(item["title"]) == 0 or item["title"] is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Title can't be empty",
                    )
                if (
                    int(item["published_year"]) < 1800
                    or int(item["published_year"]) > datetime.datetime.now().year
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Published year provided is incorrect",
                    )
                book_data = BookCreate(
                    title=item["title"],
                    genre=item["genre"],
                    published_year=int(item["published_year"]),
                )
                books_to_insert.append(book_data)
        except (json.JSONDecodeError, KeyError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON structure"
            )
        except ValidationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data provided is incorrect",
            )

    if not books_to_insert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No valid books to import"
        )

    for book in books_to_insert:
        book_query = text(
            """
            INSERT INTO books (title, genre, published_year, user_id)
            VALUES (:title, :genre, :published_year, :user_id)
        """
        )
        await db.execute(
            book_query,
            {
                "title": book.title,
                "genre": book.genre,
                "published_year": book.published_year,
                "user_id": current_user.id,
            },
        )

    await db.commit()

    return {"message": f"{len(books_to_insert)} books imported successfully."}
