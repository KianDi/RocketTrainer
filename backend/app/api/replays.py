"""
Replay management endpoints for uploading and analyzing Rocket League replays.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
import structlog

from app.database import get_db
from app.models.user import User
from app.models.match import Match
from app.api.auth import get_current_user
from app.schemas.replay import ReplayResponse, ReplayUpload, ReplayAnalysis
from app.services.replay_service import ReplayService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/upload", response_model=ReplayResponse)
async def upload_replay(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a replay file for analysis."""
    # Validate file type
    if not file.filename.endswith('.replay'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .replay files are supported"
        )
    
    # Validate file size (50MB limit)
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 50MB limit"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Create match record
        match = Match(
            user_id=current_user.id,
            replay_filename=file.filename,
            playlist="unknown",  # Will be updated after processing
            duration=0,  # Will be updated after processing
            score_team_0=0,  # Will be updated after processing
            score_team_1=0,  # Will be updated after processing
            result="unknown",  # Will be updated after processing
            processed=False
        )
        
        db.add(match)
        db.commit()
        db.refresh(match)
        
        # Queue background processing
        background_tasks.add_task(
            ReplayService.process_replay_file,
            match_id=str(match.id),
            file_content=file_content,
            filename=file.filename
        )
        
        logger.info(
            "Replay uploaded for processing",
            user_id=str(current_user.id),
            match_id=str(match.id),
            filename=file.filename
        )
        
        return ReplayResponse(
            id=str(match.id),
            filename=file.filename,
            status="processing",
            message="Replay uploaded successfully and is being processed",
            uploaded_at=match.created_at
        )
        
    except Exception as e:
        logger.error("Replay upload failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload replay"
        )


@router.post("/ballchasing-import", response_model=ReplayResponse)
async def import_from_ballchasing(
    background_tasks: BackgroundTasks,
    replay_data: ReplayUpload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import a replay from Ballchasing.com using replay ID."""
    # Check if replay already exists
    existing_match = db.query(Match).filter(
        Match.ballchasing_id == replay_data.ballchasing_id
    ).first()
    
    if existing_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Replay already imported"
        )
    
    try:
        # Create match record
        match = Match(
            user_id=current_user.id,
            ballchasing_id=replay_data.ballchasing_id,
            playlist="unknown",  # Will be updated after processing
            duration=0,  # Will be updated after processing
            score_team_0=0,  # Will be updated after processing
            score_team_1=0,  # Will be updated after processing
            result="unknown",  # Will be updated after processing
            processed=False
        )
        
        db.add(match)
        db.commit()
        db.refresh(match)
        
        # Queue background processing
        background_tasks.add_task(
            ReplayService.process_ballchasing_replay,
            match_id=str(match.id),
            ballchasing_id=replay_data.ballchasing_id
        )
        
        logger.info(
            "Ballchasing replay imported for processing",
            user_id=str(current_user.id),
            match_id=str(match.id),
            ballchasing_id=replay_data.ballchasing_id
        )
        
        return ReplayResponse(
            id=str(match.id),
            ballchasing_id=replay_data.ballchasing_id,
            status="processing",
            message="Replay imported successfully and is being processed",
            uploaded_at=match.created_at
        )
        
    except Exception as e:
        logger.error("Ballchasing import failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import replay"
        )


@router.get("/{replay_id}", response_model=ReplayAnalysis)
async def get_replay_analysis(
    replay_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analysis of a replay."""
    match = db.query(Match).filter(
        Match.id == replay_id,
        Match.user_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay not found"
        )
    
    return ReplayAnalysis(
        id=str(match.id),
        filename=match.replay_filename,
        ballchasing_id=match.ballchasing_id,
        playlist=match.playlist,
        duration=match.duration,
        match_date=match.match_date,
        result=match.result,
        score=f"{match.score_team_0}-{match.score_team_1}",
        player_stats={
            "goals": match.goals,
            "assists": match.assists,
            "saves": match.saves,
            "shots": match.shots,
            "score": match.score,
            "boost_usage": match.boost_usage,
            "average_speed": match.average_speed
        },
        weakness_analysis=match.weakness_analysis,
        processed=match.processed,
        processed_at=match.processed_at,
        created_at=match.created_at
    )


@router.get("/", response_model=List[ReplayResponse])
async def get_user_replays(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's uploaded replays."""
    matches = db.query(Match).filter(
        Match.user_id == current_user.id
    ).order_by(desc(Match.created_at)).offset(skip).limit(limit).all()
    
    return [
        ReplayResponse(
            id=str(match.id),
            filename=match.replay_filename,
            ballchasing_id=match.ballchasing_id,
            status="processed" if match.processed else "processing",
            playlist=match.playlist,
            result=match.result,
            uploaded_at=match.created_at,
            processed_at=match.processed_at
        )
        for match in matches
    ]


@router.delete("/{replay_id}")
async def delete_replay(
    replay_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a replay and its analysis."""
    match = db.query(Match).filter(
        Match.id == replay_id,
        Match.user_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay not found"
        )
    
    try:
        db.delete(match)
        db.commit()
        
        logger.info("Replay deleted", user_id=str(current_user.id), match_id=replay_id)
        return {"message": "Replay deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error("Failed to delete replay", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete replay"
        )
