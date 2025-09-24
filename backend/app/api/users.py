"""
User management endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
import structlog

from app.database import get_db
from app.models.user import User
from app.models.match import Match
from app.models.player_stats import PlayerStats
from app.api.auth import get_current_user
from app.schemas.user import UserResponse, UserUpdate, UserStats

router = APIRouter()
logger = structlog.get_logger()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        steam_id=current_user.steam_id,
        epic_id=current_user.epic_id,
        email=current_user.email,
        current_rank=current_user.current_rank,
        mmr=current_user.mmr,
        platform=current_user.platform,
        is_premium=current_user.is_premium,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    # Update allowed fields
    if user_update.username is not None:
        current_user.username = user_update.username
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.current_rank is not None:
        current_user.current_rank = user_update.current_rank
    if user_update.mmr is not None:
        current_user.mmr = user_update.mmr
    
    try:
        db.commit()
        db.refresh(current_user)
        logger.info("User profile updated", user_id=str(current_user.id))
        
        return UserResponse(
            id=str(current_user.id),
            username=current_user.username,
            steam_id=current_user.steam_id,
            epic_id=current_user.epic_id,
            email=current_user.email,
            current_rank=current_user.current_rank,
            mmr=current_user.mmr,
            platform=current_user.platform,
            is_premium=current_user.is_premium,
            created_at=current_user.created_at,
            last_login=current_user.last_login
        )
    except Exception as e:
        db.rollback()
        logger.error("Failed to update user profile", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's gameplay statistics."""
    # Get match statistics
    total_matches = db.query(Match).filter(Match.user_id == current_user.id).count()
    wins = db.query(Match).filter(
        Match.user_id == current_user.id,
        Match.result == "win"
    ).count()
    
    win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
    
    # Get recent matches
    recent_matches = db.query(Match).filter(
        Match.user_id == current_user.id
    ).order_by(desc(Match.created_at)).limit(10).all()
    
    # Get latest player stats
    latest_stats = db.query(PlayerStats).filter(
        PlayerStats.user_id == current_user.id
    ).order_by(desc(PlayerStats.time)).limit(20).all()
    
    # Organize stats by category
    stats_by_category = {}
    for stat in latest_stats:
        if stat.category not in stats_by_category:
            stats_by_category[stat.category] = {}
        stats_by_category[stat.category][stat.stat_type] = {
            "value": stat.value,
            "percentile": stat.rank_percentile,
            "improvement_rate": stat.improvement_rate
        }
    
    return UserStats(
        total_matches=total_matches,
        wins=wins,
        losses=total_matches - wins,
        win_rate=win_rate,
        current_rank=current_user.current_rank,
        mmr=current_user.mmr,
        stats_by_category=stats_by_category,
        recent_matches=[
            {
                "id": str(match.id),
                "playlist": match.playlist,
                "result": match.result,
                "score": f"{match.score_team_0}-{match.score_team_1}",
                "duration": match.duration,
                "match_date": match.match_date
            }
            for match in recent_matches
        ]
    )


@router.delete("/account")
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account and all associated data."""
    try:
        # Soft delete - mark as inactive
        current_user.is_active = False
        current_user.email = None  # Clear PII
        current_user.username = f"deleted_user_{str(current_user.id)[:8]}"
        
        db.commit()
        logger.info("User account deleted", user_id=str(current_user.id))
        
        return {"message": "Account successfully deleted"}
    except Exception as e:
        db.rollback()
        logger.error("Failed to delete user account", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )
