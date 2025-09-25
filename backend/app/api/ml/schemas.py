"""
Pydantic schemas for ML API requests and responses.

Defines comprehensive validation schemas for all ML endpoints including:
- Weakness analysis requests and responses
- Training recommendation requests and responses  
- Model status responses

All schemas include proper validation, documentation, and examples
for OpenAPI documentation generation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


class SkillLevel(str, Enum):
    """Rocket League skill levels."""
    BRONZE = "bronze"
    SILVER = "silver" 
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"
    CHAMPION = "champion"
    GRAND_CHAMPION = "grand_champion"


class WeaknessAnalysisRequest(BaseModel):
    """Request schema for weakness analysis."""

    user_id: UUID = Field(
        ...,
        description="User ID for weakness analysis",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    match_ids: Optional[List[UUID]] = Field(
        None,
        description="Optional list of specific match IDs to analyze. If None, uses recent matches.",
        example=["123e4567-e89b-12d3-a456-426614174001", "123e4567-e89b-12d3-a456-426614174002"]
    )
    include_confidence: bool = Field(
        True,
        description="Whether to include confidence scores in the response"
    )
    analysis_depth: str = Field(
        "standard",
        description="Analysis depth level",
        pattern="^(quick|standard|detailed)$"
    )

    @validator('match_ids')
    def validate_match_ids(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError('Cannot analyze more than 50 matches at once')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "match_ids": None,
                "include_confidence": True,
                "analysis_depth": "standard"
            }
        }


class SkillCategoryScore(BaseModel):
    """Skill category score with details."""
    
    category: str = Field(..., description="Skill category name")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized skill score (0-1)")
    percentile: Optional[float] = Field(None, ge=0.0, le=100.0, description="Percentile ranking")
    trend: Optional[str] = Field(None, description="Performance trend (improving/declining/stable)")


class WeaknessAnalysisResponse(BaseModel):
    """Response schema for weakness analysis."""
    
    user_id: UUID = Field(..., description="User ID that was analyzed")
    analysis_date: datetime = Field(..., description="When the analysis was performed")
    primary_weakness: str = Field(..., description="Primary identified weakness")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for primary weakness")
    skill_categories: List[SkillCategoryScore] = Field(
        ..., 
        description="Detailed scores for all skill categories"
    )
    matches_analyzed: int = Field(..., ge=1, description="Number of matches analyzed")
    recommendations_available: bool = Field(
        ..., 
        description="Whether training recommendations are available"
    )
    analysis_summary: Optional[str] = Field(
        None,
        description="Human-readable summary of the analysis"
    )


class TrainingRecommendationRequest(BaseModel):
    """Request schema for training recommendations."""

    user_id: UUID = Field(
        ...,
        description="User ID for training recommendations",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    skill_level: Optional[SkillLevel] = Field(
        None,
        description="Player skill level. If None, will be auto-detected from recent performance."
    )
    max_recommendations: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of training pack recommendations to return"
    )
    categories: Optional[List[str]] = Field(
        None,
        description="Filter recommendations by specific categories",
        example=["shooting", "aerials", "saves"]
    )
    exclude_completed: bool = Field(
        True,
        description="Whether to exclude training packs the user has already completed"
    )

    @validator('categories')
    def validate_categories(cls, v):
        if v is not None:
            valid_categories = ["shooting", "aerials", "saves", "dribbling", "positioning", "wall_play"]
            invalid = [cat for cat in v if cat not in valid_categories]
            if invalid:
                raise ValueError(f'Invalid categories: {invalid}. Valid categories: {valid_categories}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "skill_level": "platinum",
                "max_recommendations": 5,
                "categories": ["shooting", "aerials"],
                "exclude_completed": True
            }
        }


class TrainingPackRecommendation(BaseModel):
    """Individual training pack recommendation."""
    
    training_pack_id: str = Field(..., description="Training pack ID")
    name: str = Field(..., description="Training pack name")
    code: str = Field(..., description="Training pack code for Rocket League")
    category: str = Field(..., description="Training pack category")
    difficulty: int = Field(..., ge=1, le=5, description="Difficulty level (1-5)")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to user's weaknesses")
    difficulty_match: float = Field(..., ge=0.0, le=1.0, description="How well difficulty matches user skill")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Training pack quality rating")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall recommendation score")
    reasoning: str = Field(..., description="Why this training pack was recommended")
    estimated_improvement: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Estimated skill improvement potential"
    )


class TrainingRecommendationResponse(BaseModel):
    """Response schema for training recommendations."""
    
    user_id: UUID = Field(..., description="User ID for whom recommendations were generated")
    recommendations: List[TrainingPackRecommendation] = Field(
        ...,
        description="List of personalized training pack recommendations"
    )
    skill_level_detected: SkillLevel = Field(
        ...,
        description="Detected or provided skill level used for recommendations"
    )
    total_packs_evaluated: int = Field(
        ...,
        ge=0,
        description="Total number of training packs evaluated"
    )
    generation_time: datetime = Field(..., description="When recommendations were generated")
    cache_hit: bool = Field(..., description="Whether recommendations were served from cache")


class ModelInfo(BaseModel):
    """Information about a specific ML model."""
    
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    status: str = Field(..., description="Model status (healthy/degraded/error)")
    last_trained: Optional[datetime] = Field(None, description="When model was last trained")
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Model accuracy score")
    predictions_served: int = Field(..., ge=0, description="Total predictions served")
    avg_response_time: float = Field(..., ge=0.0, description="Average response time in milliseconds")


class CacheStatistics(BaseModel):
    """Cache performance statistics."""
    
    total_requests: int = Field(..., ge=0, description="Total cache requests")
    cache_hits: int = Field(..., ge=0, description="Number of cache hits")
    cache_misses: int = Field(..., ge=0, description="Number of cache misses")
    hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate")
    avg_cache_time: float = Field(..., ge=0.0, description="Average cache retrieval time in milliseconds")


class ModelStatusResponse(BaseModel):
    """Response schema for model status."""
    
    system_status: str = Field(..., description="Overall system status")
    models: List[ModelInfo] = Field(..., description="Status of all ML models")
    cache_stats: CacheStatistics = Field(..., description="Cache performance statistics")
    uptime: float = Field(..., ge=0.0, description="System uptime in seconds")
    memory_usage: float = Field(..., ge=0.0, le=100.0, description="Memory usage percentage")
    last_health_check: datetime = Field(..., description="Last health check timestamp")
