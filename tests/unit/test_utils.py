from jose import jwt

from app.core.config import SECRET_KEY, ALGORITHM
from app.core.security import verify_password, get_password_hash, create_access_token


def test_password_hashing_and_verification():
    """FUNCTION TO TEST PASSWORD HASHING"""
    password = "secure_password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)


def test_create_access_token():
    """FUNCTION TO TEST JWT"""
    token = create_access_token({"sub": "testuser"})
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "testuser"
