from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from jose import jwt

from src.api.auth import create_access_token, verify_password, get_password_hash, User, get_current_active_user
from src.config import settings


router = APIRouter(tags=["authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    email: Optional[str] = None


# Mock user database (in production, use a real database)
mock_users_db = {}


@router.get("/")
async def auth_info():
    """Authentication service information."""
    return {
        "service": "Authentication Service",
        "endpoints": {
            "register": "POST /register",
            "login": "POST /login", 
            "demo_token": "POST /demo-token",
            "verify": "GET /verify"
        },
        "token_info": {
            "type": "Bearer JWT",
            "expires_in": f"{settings.access_token_expire_minutes} minutes",
            "algorithm": settings.algorithm
        }
    }


@router.post("/register", response_model=dict)
async def register_user(user_data: UserRegistration):
    """Register a new user."""
    
    # Check if user already exists
    if user_data.email in mock_users_db:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Store user (in production, save to database)
    user_id = f"user_{len(mock_users_db) + 1}"
    mock_users_db[user_data.email] = {
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    return {
        "message": "User registered successfully",
        "user_id": user_id,
        "email": user_data.email
    }


@router.post("/login", response_model=Token)
async def login_user(login_data: UserLogin):
    """Authenticate user and return access token."""
    
    # Get user from database
    user = mock_users_db.get(login_data.email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user["is_active"]:
        raise HTTPException(
            status_code=401,
            detail="Account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60  # in seconds
    }


@router.post("/demo-token", response_model=Token)
async def get_demo_token():
    """Get a demo token for testing (no registration required)."""
    
    # Create a demo user
    demo_user_email = "demo@example.com"
    demo_user_id = "demo_user"
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": demo_user_email, "user_id": demo_user_id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60  # in seconds
    }


@router.get("/verify")
async def verify_token_endpoint(current_user: User = Depends(get_current_active_user)):
    """Verify the current JWT token and return user info."""
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "is_active": current_user.is_active
        }
    }


# Add some demo users for testing
demo_users = [
    {
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Admin User"
    },
    {
        "email": "user@example.com", 
        "password": "user123",
        "full_name": "Test User"
    }
]

# Pre-populate with demo users
for demo_user in demo_users:
    user_id = f"user_{len(mock_users_db) + 1}"
    mock_users_db[demo_user["email"]] = {
        "id": user_id,
        "email": demo_user["email"],
        "full_name": demo_user["full_name"],
        "hashed_password": get_password_hash(demo_user["password"]),
        "is_active": True,
        "created_at": datetime.utcnow()
    }