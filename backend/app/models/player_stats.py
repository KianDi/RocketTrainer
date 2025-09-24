"""
Player statistics model using TimescaleDB for time-series data.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID, Float, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class PlayerStats(Base):
    """Time-series player statistics for tracking improvement over time."""
    
    __tablename__ = "player_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time = Column(DateTime(timezone=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=True, index=True)
    
    # Stat metadata
    stat_type = Column(String(50), nullable=False, index=True)  # 'aerial_accuracy', 'save_percentage', etc.
    category = Column(String(30), nullable=False)  # 'mechanical', 'positioning', 'game_sense'
    
    # Stat values
    value = Column(Float, nullable=False)
    rank_percentile = Column(Float, nullable=True)  # compared to same rank
    improvement_rate = Column(Float, nullable=True)  # rate of improvement
    confidence_score = Column(Float, nullable=True)  # ML model confidence
    
    # Context
    playlist = Column(String(30), nullable=True)  # which game mode
    sample_size = Column(Float, nullable=True)  # number of data points used
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    match = relationship("Match", back_populates="player_stats")
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_player_stats_user_time', 'user_id', 'time'),
        Index('idx_player_stats_type_time', 'stat_type', 'time'),
        Index('idx_player_stats_category_time', 'category', 'time'),
    )
    
    def __repr__(self):
        return f"<PlayerStats(user_id={self.user_id}, stat_type={self.stat_type}, value={self.value})>"


# Common stat types for reference
STAT_TYPES = {
    # Mechanical skills
    'aerial_accuracy': 'mechanical',
    'aerial_frequency': 'mechanical', 
    'save_percentage': 'mechanical',
    'shot_accuracy': 'mechanical',
    'dribble_success': 'mechanical',
    'boost_efficiency': 'mechanical',
    
    # Positioning
    'positioning_score': 'positioning',
    'defensive_positioning': 'positioning',
    'offensive_positioning': 'positioning',
    'midfield_presence': 'positioning',
    'rotation_timing': 'positioning',
    
    # Game sense
    'challenge_timing': 'game_sense',
    'boost_collection': 'game_sense',
    'ball_prediction': 'game_sense',
    'teammate_awareness': 'game_sense',
    'decision_making': 'game_sense',
}
