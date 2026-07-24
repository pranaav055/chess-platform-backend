from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.config import settings

pwd_manager = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_manager.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_manager.verify(password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expiration_time = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expiration_time})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)

    return encoded_jwt


