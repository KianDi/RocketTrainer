"""
Coaching insights and weakness detection schemas for RocketTrainer.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PerformanceArea(BaseModel):
    """Schema for individual performance area analysis."""
    name: str = Field(..., description="Performance area name (e.g., 'positioning', 'rotation')")
    score: float = Field(..., ge=0, le=1, description="Composite score for this area (0-1 scale)")
    percentile: Optional[float] = Field(None, ge=0, le=100, description="Percentile rank compared to similar players")
    status: str = Field(..., description="Performance status: 'strength', 'average', 'weakness'")
    contributing_metrics: List[str] = Field(default_factory=list, description="Metrics that contribute to this area")
    raw_score: Optional[float] = Field(None, description="Raw score before normalization")


class WeaknessInsight(BaseModel):
    """Schema for detailed weakness analysis and coaching feedback."""
    area: str = Field(..., description="Performance area with weakness")
    severity: float = Field(..., ge=0, le=1, description="Weakness severity (0-1 scale, higher = more severe)")
    impact_potential: float = Field(..., ge=0, le=1, description="Improvement potential (0-1 scale, higher = more impact)")
    primary_issue: str = Field(..., description="Main issue identified in this area")
    coaching_feedback: str = Field(..., description="Natural language coaching advice")
    specific_recommendations: List[str] = Field(default_factory=list, description="Actionable improvement suggestions")
    confidence: float = Field(default=0.8, ge=0, le=1, description="Confidence in this analysis")


class StrengthInsight(BaseModel):
    """Schema for highlighting player strengths."""
    area: str = Field(..., description="Performance area that is a strength")
    score: float = Field(..., ge=0, le=1, description="Performance score in this area")
    percentile: Optional[float] = Field(None, description="Percentile rank for this strength")
    positive_feedback: str = Field(..., description="Encouraging feedback about this strength")
    leverage_suggestions: List[str] = Field(default_factory=list, description="How to leverage this strength")


class CoachingInsights(BaseModel):
    """Schema for comprehensive coaching analysis results."""
    match_id: str = Field(..., description="ID of the analyzed match")
    overall_performance_score: float = Field(..., ge=0, le=1, description="Overall performance composite score")
    performance_areas: List[PerformanceArea] = Field(default_factory=list, description="Analysis of all performance areas")
    top_weaknesses: List[WeaknessInsight] = Field(default_factory=list, description="Top 2-3 areas needing improvement")
    top_strengths: List[StrengthInsight] = Field(default_factory=list, description="Top performing areas")
    improvement_priority: str = Field(..., description="Primary area to focus improvement efforts")
    key_takeaway: str = Field(..., description="Main coaching message for this match")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When insights were generated")
    confidence_score: float = Field(default=0.8, ge=0, le=1, description="Overall confidence in the analysis")


class WeaknessAnalysisRequest(BaseModel):
    """Schema for requesting weakness analysis."""
    match_id: str = Field(..., description="Match ID to analyze")
    include_strengths: bool = Field(default=True, description="Whether to include strength analysis")
    detail_level: str = Field(default="standard", description="Analysis detail level: 'quick', 'standard', 'detailed'")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus analysis on")


class CoachingInsightsResponse(BaseModel):
    """Schema for coaching insights API response."""
    success: bool = Field(default=True, description="Whether analysis was successful")
    insights: Optional[CoachingInsights] = Field(None, description="Generated coaching insights")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    processing_time_ms: Optional[int] = Field(None, description="Time taken to generate insights")
    cache_hit: bool = Field(default=False, description="Whether results were served from cache")


class PerformanceMetrics(BaseModel):
    """Schema for normalized performance metrics used in analysis."""
    # Core gameplay metrics
    goals_per_minute: Optional[float] = None
    assists_per_minute: Optional[float] = None
    saves_per_minute: Optional[float] = None
    shots_per_minute: Optional[float] = None
    score_per_minute: Optional[float] = None
    
    # Movement and positioning
    positioning_score: Optional[float] = None
    rotation_score: Optional[float] = None
    boost_efficiency: Optional[float] = None
    aerial_efficiency: Optional[float] = None
    
    # Time distribution
    time_supersonic: Optional[float] = None
    time_on_ground: Optional[float] = None
    time_low_air: Optional[float] = None
    time_high_air: Optional[float] = None
    
    # Action counts (normalized by match duration)
    defensive_actions_per_minute: Optional[float] = None
    offensive_actions_per_minute: Optional[float] = None
    
    # Speed and movement
    average_speed: Optional[float] = None
    boost_usage: Optional[float] = None


class AnalysisContext(BaseModel):
    """Schema for match context used in analysis."""
    playlist: str = Field(..., description="Match playlist type")
    duration: int = Field(..., description="Match duration in seconds")
    result: str = Field(..., description="Match result: 'win', 'loss', 'tie'")
    score_differential: int = Field(..., description="Goal difference in the match")
    team_score: int = Field(..., description="Player's team score")
    opponent_score: int = Field(..., description="Opponent team score")
    match_date: Optional[datetime] = Field(None, description="When the match was played")
    rank_estimate: Optional[str] = Field(None, description="Estimated player rank")
