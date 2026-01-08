"""
User Authentication Module for ChatDocAI.
Provides JWT-based authentication with file-based user storage.
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from multi_doc_chat.logger import GLOBAL_LOGGER as log
from .db import SessionLocal
from .models import User


# ----------------------------
# Configuration
# ----------------------------
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


# ----------------------------
# Password Hashing
# ----------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ----------------------------
# JWT Token Handling
# ----------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ----------------------------
# Pydantic Models
# ----------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ----------------------------
# User Storage (File-based)
# ----------------------------
class UserStore:
    """PostgreSQL-based user storage."""
    
    def __init__(self):
        log.info("UserStore initialized (PostgreSQL)")
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.email == email.lower()).first()
        finally:
            db.close()
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
    
    def create(self, email: str, password: str, name: str) -> User:
        """Create a new user."""
        email = email.lower()
        db = SessionLocal()
        try:
            if db.query(User).filter(User.email == email).first():
                raise ValueError("User with this email already exists")
            
            user = User(
                email=email,
                name=name,
                password_hash=hash_password(password)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            log.info("User created (DB)", user_id=user.id, email=email)
            return user
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user


# Singleton instance
user_store = UserStore()


# ----------------------------
# FastAPI Security Dependencies
# ----------------------------
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Dependency to get current authenticated user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = user_store.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Dependency to optionally get current user (doesn't require auth)."""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def user_to_response(user) -> UserResponse:
    """Convert user model/object to response model."""
    created_at = user.created_at
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=str(created_at)
    )
