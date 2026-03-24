from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from src.config import settings


security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    user_id: Optional[str] = None


class User(BaseModel):
    id: str
    email: str
    is_active: bool = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify JWT token and extract user data."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(user_id=user_id)
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user."""
    token_data = verify_token(credentials.credentials)
    
    # Import here to avoid circular import
    try:
        from src.api.routes.auth import mock_users_db
    except ImportError:
        mock_users_db = {}
    
    # Try to find user in mock database by user_id or email
    user_data = None
    
    # Check if token contains email (sub field)
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        if email and email in mock_users_db:
            user_data = mock_users_db[email]
        elif user_id == "demo_user":  # Handle demo token
            user_data = {
                "id": "demo_user",
                "email": "demo@example.com",
                "is_active": True
            }
    except:
        pass
    
    if not user_data:
        # Fallback: create a basic user from token data
        user_data = {
            "id": token_data.user_id or "unknown",
            "email": f"{token_data.user_id}@example.com",
            "is_active": True
        }
    
    user = User(
        id=user_data["id"],
        email=user_data["email"],
        is_active=user_data["is_active"]
    )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class APIKeyAuth:
    """Simple API key authentication for service-to-service communication."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
        if credentials.credentials != self.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return True


# Create API key dependency
api_key_auth = APIKeyAuth(settings.secret_key)  # In production, use a separate API key