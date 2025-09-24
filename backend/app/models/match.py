"""
Match model for storing Rocket League replay data.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID, Integer, ForeignKey, JSON, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Match(Base):
    """Match model representing a Rocket League match/replay."""
    
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # External identifiers
    ballchasing_id = Column(String(50), unique=True, nullable=True, index=True)
    replay_filename = Column(String(255), nullable=True)
    
    # Match metadata
    playlist = Column(String(30), nullable=False)  # ranked-duels, ranked-doubles, etc.
    duration = Column(Integer, nullable=False)  # seconds
    match_date = Column(DateTime(timezone=True), nullable=False)
    
    # Match results
    score_team_0 = Column(Integer, nullable=False)
    score_team_1 = Column(Integer, nullable=False)
    result = Column(String(10), nullable=False)  # win/loss/draw
    
    # Player performance (for the user)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    score = Column(Integer, default=0)
    
    # Advanced stats
    boost_usage = Column(Float, nullable=True)
    average_speed = Column(Float, nullable=True)
    time_supersonic = Column(Float, nullable=True)
    time_on_ground = Column(Float, nullable=True)
    time_low_air = Column(Float, nullable=True)
    time_high_air = Column(Float, nullable=True)
    
    # Analysis data
    replay_data = Column(JSON, nullable=True)  # Full replay analysis
    weakness_analysis = Column(JSON, nullable=True)  # ML analysis results
    processed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="matches")
    player_stats = relationship("PlayerStats", back_populates="match", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Match(id={self.id}, playlist={self.playlist}, result={self.result})>"
    
    @property
    def is_win(self) -> bool:
        """Check if the match was a win."""
        return self.result == "win"
    
    @property
    def match_duration_minutes(self) -> float:
        """Get match duration in minutes."""
        return self.duration / 60.0
