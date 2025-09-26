"""
Replay schemas for request/response validation.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ReplayUpload(BaseModel):
    """Schema for Ballchasing.com replay import."""
    ballchasing_id: str


class ReplayResponse(BaseModel):
    """Schema for replay response."""
    id: str
    filename: Optional[str] = None
    ballchasing_id: Optional[str] = None
    status: str  # processing, processed, failed
    message: Optional[str] = None
    playlist: Optional[str] = None
    result: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    task_id: Optional[str] = None

    class Config:
        from_attributes = True


class PlayerStats(BaseModel):
    """Schema for player statistics in replay."""
    goals: Optional[int] = None
    assists: Optional[int] = None
    saves: Optional[int] = None
    shots: Optional[int] = None
    score: Optional[int] = None
    boost_usage: Optional[float] = None
    average_speed: Optional[float] = None
    time_supersonic: Optional[float] = None
    time_on_ground: Optional[float] = None
    time_low_air: Optional[float] = None
    time_high_air: Optional[float] = None


class ReplayAnalysis(BaseModel):
    """Schema for detailed replay analysis."""
    id: str
    filename: Optional[str] = None
    ballchasing_id: Optional[str] = None
    playlist: str
    duration: int
    match_date: Optional[datetime] = None
    result: str
    score: str
    player_stats: PlayerStats
    weakness_analysis: Optional[Dict[str, Any]] = None
    processed: bool
    processed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReplaySearchRequest(BaseModel):
    """Schema for searching Ballchasing.com replays."""
    player_name: Optional[str] = None
    playlist: Optional[str] = Field(None, description="Playlist filter (e.g., 'ranked-duels')")
    season: Optional[str] = Field(None, description="Season filter")
    count: int = Field(10, ge=1, le=200, description="Number of replays to return")
    sort_by: str = Field("replay-date", description="Sort field")
    sort_dir: str = Field("desc", description="Sort direction (asc/desc)")


class BallchasingReplayInfo(BaseModel):
    """Schema for Ballchasing.com replay information."""
    id: str
    title: str
    playlist: str
    duration: int
    date: str
    blue_score: int
    orange_score: int
    uploader: str


class ReplaySearchResponse(BaseModel):
    """Schema for Ballchasing.com search results."""
    replays: List[BallchasingReplayInfo]
    count: int
    message: str
