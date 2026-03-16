from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from authlib.jose import JoseError, jwt
from authlib.jose.errors import ExpiredTokenError

from core.config import settings


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_expire_minutes
        )

    to_encode.update({"exp": expire})
    header = {"alg": settings.jwt_algorithm}
    encoded_jwt = jwt.encode(header, to_encode, settings.jwt_secret_key)
    return encoded_jwt.decode("utf-8")


def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key)
        payload.validate()
        return dict(payload)
    except (JoseError, ExpiredTokenError):
        return None
