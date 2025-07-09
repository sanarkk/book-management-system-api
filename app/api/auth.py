from sqlalchemy import text
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user import User
from app.db.database import get_db
from app.schemas.user import UserCreate, UserOut, UserLogin, Token
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, summary="Register a new user")
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """REGISTER A NEW USER"""
    user_query = text("SELECT id FROM users WHERE username = :username")
    user_raw = await db.execute(user_query, {"username": user_in.username})
    user = user_raw.scalar()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already in use",
        )

    insert_user_query = text(
        """
        INSERT INTO users (username, first_name, last_name, email, hashed_password)
        VALUES (:username, :first_name, :last_name, :email, :hashed_password)
        RETURNING id, username, first_name, last_name, email, hashed_password, created_at
        """
    )
    hashed_pw = get_password_hash(user_in.password)

    try:
        new_user_raw = await db.execute(
            insert_user_query,
            {
                "username": user_in.username,
                "first_name": user_in.first_name,
                "last_name": user_in.last_name,
                "email": user_in.email,
                "hashed_password": hashed_pw,
            },
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already in use",
        )
    await db.commit()
    new_user = new_user_raw.fetchone()

    user_out = User(
        id=new_user.id,
        username=new_user.username,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        email=new_user.email,
        hashed_password=new_user.hashed_password,
        created_at=new_user.created_at,
    )

    return user_out


@router.post("/login", response_model=Token, summary="Authenticate a user")
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """AUTHENTICATE A USER"""
    user_query = text("SELECT * FROM users WHERE username = :username")
    user_raw = await db.execute(user_query, {"username": user_in.username})
    user = user_raw.first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}
