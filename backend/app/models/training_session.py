"""
Training session model for tracking user training progress.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID, Integer, Float, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class TrainingSession(Base):
    """Training session model representing a user's training session."""
    
    __tablename__ = "training_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    training_pack_id = Column(UUID(as_uuid=True), ForeignKey("training_packs.id"), nullable=False, index=True)
    
    # Session metadata
    session_type = Column(String(20), default="practice")  # practice, warmup, focused
    difficulty_attempted = Column(Integer, nullable=True)  # if user modified difficulty
    
    # Performance metrics
    duration = Column(Integer, nullable=False)  # seconds
    attempts = Column(Integer, nullable=False)
    successes = Column(Integer, nullable=False)
    
    # Detailed stats
    accuracy = Column(Float, nullable=True)  # success rate
    average_time_per_shot = Column(Float, nullable=True)
    improvement_score = Column(Float, nullable=True)  # compared to previous sessions
    consistency_score = Column(Float, nullable=True)  # how consistent the performance was
    
    # Progress tracking
    personal_best = Column(Boolean, default=False)
    streak_count = Column(Integer, default=0)  # consecutive successful shots
    
    # Session data
    shot_data = Column(JSON, nullable=True)  # detailed per-shot data
    notes = Column(String(500), nullable=True)  # user notes
    
    # Ratings
    difficulty_rating = Column(Integer, nullable=True)  # user's difficulty rating 1-10
    enjoyment_rating = Column(Integer, nullable=True)  # user's enjoyment rating 1-10
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="training_sessions")
    training_pack = relationship("TrainingPack", back_populates="training_sessions")
    
    def __repr__(self):
        return f"<TrainingSession(user_id={self.user_id}, pack_id={self.training_pack_id}, accuracy={self.accuracy})>"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.attempts == 0:
            return 0.0
        return (self.successes / self.attempts) * 100
    
    @property
    def duration_minutes(self) -> float:
        """Get duration in minutes."""
        return self.duration / 60.0
    
    @property
    def shots_per_minute(self) -> float:
        """Calculate shots per minute."""
        if self.duration == 0:
            return 0.0
        return (self.attempts / self.duration) * 60
