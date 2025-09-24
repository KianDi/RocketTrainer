"""
Training schemas for request/response validation.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class TrainingPackResponse(BaseModel):
    """Schema for training pack response."""
    id: str
    name: str
    code: str
    description: Optional[str] = None
    creator: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    difficulty: int
    skill_level: str
    tags: List[str] = []
    shots_count: Optional[int] = None
    estimated_duration: Optional[int] = None
    rating: Optional[float] = None
    rating_count: int = 0
    usage_count: int = 0
    is_official: bool = False
    is_featured: bool = False

    class Config:
        from_attributes = True


class TrainingSessionCreate(BaseModel):
    """Schema for creating a training session."""
    training_pack_id: str
    session_type: str = "practice"
    duration: int  # seconds
    attempts: int
    successes: int
    started_at: datetime
    notes: Optional[str] = None


class TrainingSessionResponse(BaseModel):
    """Schema for training session response."""
    id: str
    training_pack_id: str
    training_pack_name: str
    training_pack_code: str
    session_type: str
    duration: int
    attempts: int
    successes: int
    accuracy: float
    personal_best: bool = False
    notes: Optional[str] = None
    started_at: datetime
    completed_at: datetime

    class Config:
        from_attributes = True


class TrainingRecommendation(BaseModel):
    """Schema for training pack recommendation."""
    training_pack: TrainingPackResponse
    reason: str
    confidence: float
    priority: int
    weakness_addressed: Optional[str] = None
    expected_improvement: Optional[float] = None


class TrainingProgress(BaseModel):
    """Schema for training progress response."""
    total_sessions: int
    total_duration: int  # seconds
    average_accuracy: float
    improvement_rate: float
    favorite_categories: List[str]
    recent_sessions: List[TrainingSessionResponse]
    progress_by_category: Dict[str, Dict[str, Any]]
