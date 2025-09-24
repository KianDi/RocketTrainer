"""
User schemas for request/response validation.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """Schema for user profile response."""
    id: str
    username: str
    steam_id: Optional[str] = None
    epic_id: Optional[str] = None
    email: Optional[EmailStr] = None
    current_rank: Optional[str] = None
    mmr: Optional[int] = None
    platform: Optional[str] = None
    is_premium: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    current_rank: Optional[str] = None
    mmr: Optional[int] = None


class MatchSummary(BaseModel):
    """Schema for match summary in user stats."""
    id: str
    playlist: str
    result: str
    score: str
    duration: int
    match_date: datetime


class UserStats(BaseModel):
    """Schema for user statistics response."""
    total_matches: int
    wins: int
    losses: int
    win_rate: float
    current_rank: Optional[str] = None
    mmr: Optional[int] = None
    stats_by_category: Dict[str, Dict[str, Any]]
    recent_matches: List[MatchSummary]

    class Config:
        from_attributes = True
