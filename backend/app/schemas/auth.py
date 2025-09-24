"""
Authentication schemas for request/response validation.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    """Schema for user login request."""
    steam_id: Optional[str] = None
    epic_id: Optional[str] = None
    username: Optional[str] = None


class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str
    email: Optional[EmailStr] = None
    steam_id: Optional[str] = None
    epic_id: Optional[str] = None
    platform: Optional[str] = None


class UserInToken(BaseModel):
    """User data included in token response."""
    id: str
    username: str
    steam_id: Optional[str] = None
    epic_id: Optional[str] = None
    current_rank: Optional[str] = None


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str
    expires_in: int
    user: UserInToken


class TokenData(BaseModel):
    """Token payload data."""
    sub: Optional[str] = None
    username: Optional[str] = None
    exp: Optional[datetime] = None
