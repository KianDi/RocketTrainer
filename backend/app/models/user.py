"""
User model for RocketTrainer.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID, Boolean, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model representing a RocketTrainer user."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    steam_id = Column(String(20), unique=True, nullable=True, index=True)
    epic_id = Column(String(50), unique=True, nullable=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    
    # Rocket League profile
    current_rank = Column(String(20), nullable=True)
    mmr = Column(Integer, nullable=True)
    platform = Column(String(20), nullable=True)  # steam, epic, psn, xbox
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    matches = relationship("Match", back_populates="user", cascade="all, delete-orphan")
    training_sessions = relationship("TrainingSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
    
    @property
    def display_name(self) -> str:
        """Get display name for the user."""
        return self.username or f"User_{str(self.id)[:8]}"
    
    @property
    def primary_platform_id(self) -> str:
        """Get the primary platform ID."""
        return self.steam_id or self.epic_id or str(self.id)
