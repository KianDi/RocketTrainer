"""
Training pack model for storing Rocket League training packs.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID, Integer, Text, ARRAY, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class TrainingPack(Base):
    """Training pack model representing a Rocket League training pack."""
    
    __tablename__ = "training_packs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    creator = Column(String(100), nullable=True)
    
    # Categorization
    category = Column(String(50), nullable=False, index=True)  # aerials, saves, shooting, etc.
    subcategory = Column(String(50), nullable=True)  # air_dribbles, redirect_shots, etc.
    difficulty = Column(Integer, nullable=False)  # 1-10 scale
    skill_level = Column(String(20), nullable=False)  # bronze, silver, gold, platinum, diamond, champion, grand_champion
    
    # Metadata
    tags = Column(ARRAY(String), nullable=True)  # array of tags
    shots_count = Column(Integer, nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # minutes
    
    # Quality metrics
    rating = Column(Float, nullable=True)  # average user rating
    rating_count = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)  # how many times used
    
    # Flags
    is_official = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    training_sessions = relationship("TrainingSession", back_populates="training_pack")
    
    def __repr__(self):
        return f"<TrainingPack(code={self.code}, name={self.name}, category={self.category})>"
    
    @property
    def difficulty_text(self) -> str:
        """Get difficulty as text."""
        difficulty_map = {
            1: "Very Easy",
            2: "Easy", 
            3: "Easy-Medium",
            4: "Medium",
            5: "Medium",
            6: "Medium-Hard",
            7: "Hard",
            8: "Hard",
            9: "Very Hard",
            10: "Extreme"
        }
        return difficulty_map.get(self.difficulty, "Unknown")
    
    @property
    def average_rating(self) -> float:
        """Get average rating, defaulting to 0 if no ratings."""
        return self.rating or 0.0
