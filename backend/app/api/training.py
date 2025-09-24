"""
Training endpoints for managing training packs and sessions.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import structlog

from app.database import get_db
from app.models.user import User
from app.models.training_pack import TrainingPack
from app.models.training_session import TrainingSession
from app.api.auth import get_current_user
from app.schemas.training import (
    TrainingPackResponse, 
    TrainingSessionCreate, 
    TrainingSessionResponse,
    TrainingRecommendation
)
from app.services.training_service import TrainingService

router = APIRouter()
logger = structlog.get_logger()


@router.get("/packs", response_model=List[TrainingPackResponse])
async def get_training_packs(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty_min: Optional[int] = Query(None, ge=1, le=10, description="Minimum difficulty"),
    difficulty_max: Optional[int] = Query(None, ge=1, le=10, description="Maximum difficulty"),
    skill_level: Optional[str] = Query(None, description="Filter by skill level"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get training packs with optional filtering."""
    query = db.query(TrainingPack).filter(TrainingPack.is_active == True)
    
    # Apply filters
    if category:
        query = query.filter(TrainingPack.category == category)
    if difficulty_min:
        query = query.filter(TrainingPack.difficulty >= difficulty_min)
    if difficulty_max:
        query = query.filter(TrainingPack.difficulty <= difficulty_max)
    if skill_level:
        query = query.filter(TrainingPack.skill_level == skill_level)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            TrainingPack.name.ilike(search_term) |
            TrainingPack.description.ilike(search_term)
        )
    
    # Order by rating and usage
    query = query.order_by(desc(TrainingPack.rating), desc(TrainingPack.usage_count))
    
    packs = query.offset(skip).limit(limit).all()
    
    return [
        TrainingPackResponse(
            id=str(pack.id),
            name=pack.name,
            code=pack.code,
            description=pack.description,
            creator=pack.creator,
            category=pack.category,
            subcategory=pack.subcategory,
            difficulty=pack.difficulty,
            skill_level=pack.skill_level,
            tags=pack.tags or [],
            shots_count=pack.shots_count,
            estimated_duration=pack.estimated_duration,
            rating=pack.rating,
            rating_count=pack.rating_count,
            usage_count=pack.usage_count,
            is_official=pack.is_official,
            is_featured=pack.is_featured
        )
        for pack in packs
    ]


@router.get("/recommendations", response_model=List[TrainingRecommendation])
async def get_training_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized training pack recommendations."""
    try:
        recommendations = await TrainingService.get_recommendations(
            user_id=str(current_user.id),
            db=db
        )
        
        return recommendations
        
    except Exception as e:
        logger.error("Failed to get training recommendations", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )


@router.post("/sessions", response_model=TrainingSessionResponse)
async def create_training_session(
    session_data: TrainingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a completed training session."""
    # Verify training pack exists
    training_pack = db.query(TrainingPack).filter(
        TrainingPack.id == session_data.training_pack_id
    ).first()
    
    if not training_pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training pack not found"
        )
    
    try:
        # Calculate derived metrics
        accuracy = (session_data.successes / session_data.attempts * 100) if session_data.attempts > 0 else 0
        
        # Create training session
        session = TrainingSession(
            user_id=current_user.id,
            training_pack_id=session_data.training_pack_id,
            session_type=session_data.session_type,
            duration=session_data.duration,
            attempts=session_data.attempts,
            successes=session_data.successes,
            accuracy=accuracy,
            started_at=session_data.started_at,
            notes=session_data.notes
        )
        
        # Check if this is a personal best
        previous_best = db.query(TrainingSession).filter(
            and_(
                TrainingSession.user_id == current_user.id,
                TrainingSession.training_pack_id == session_data.training_pack_id
            )
        ).order_by(desc(TrainingSession.accuracy)).first()
        
        if not previous_best or accuracy > previous_best.accuracy:
            session.personal_best = True
        
        db.add(session)
        
        # Update training pack usage count
        training_pack.usage_count += 1
        
        db.commit()
        db.refresh(session)
        
        logger.info(
            "Training session logged",
            user_id=str(current_user.id),
            session_id=str(session.id),
            pack_code=training_pack.code,
            accuracy=accuracy
        )
        
        return TrainingSessionResponse(
            id=str(session.id),
            training_pack_id=str(session.training_pack_id),
            training_pack_name=training_pack.name,
            training_pack_code=training_pack.code,
            session_type=session.session_type,
            duration=session.duration,
            attempts=session.attempts,
            successes=session.successes,
            accuracy=session.accuracy,
            personal_best=session.personal_best,
            notes=session.notes,
            started_at=session.started_at,
            completed_at=session.completed_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error("Failed to create training session", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log training session"
        )


@router.get("/sessions", response_model=List[TrainingSessionResponse])
async def get_training_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    training_pack_id: Optional[str] = Query(None, description="Filter by training pack"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's training sessions."""
    query = db.query(TrainingSession).filter(TrainingSession.user_id == current_user.id)
    
    if training_pack_id:
        query = query.filter(TrainingSession.training_pack_id == training_pack_id)
    
    sessions = query.order_by(desc(TrainingSession.completed_at)).offset(skip).limit(limit).all()
    
    return [
        TrainingSessionResponse(
            id=str(session.id),
            training_pack_id=str(session.training_pack_id),
            training_pack_name=session.training_pack.name,
            training_pack_code=session.training_pack.code,
            session_type=session.session_type,
            duration=session.duration,
            attempts=session.attempts,
            successes=session.successes,
            accuracy=session.accuracy,
            personal_best=session.personal_best,
            notes=session.notes,
            started_at=session.started_at,
            completed_at=session.completed_at
        )
        for session in sessions
    ]


@router.get("/progress")
async def get_training_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's training progress and statistics."""
    try:
        progress = await TrainingService.get_user_progress(
            user_id=str(current_user.id),
            db=db
        )
        
        return progress
        
    except Exception as e:
        logger.error("Failed to get training progress", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get training progress"
        )
