"""
Replay management endpoints for uploading and analyzing Rocket League replays.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
import structlog

from app.database import get_db
from app.models.user import User
from app.models.match import Match
from app.api.auth import get_current_user
from app.schemas.replay import ReplayResponse, ReplayUpload, ReplayAnalysis, ReplaySearchRequest, ReplaySearchResponse
from app.services.replay_service import ReplayService
from app.services.ballchasing_service import ballchasing_service
from app.celery_app import celery_app

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
            match_date=datetime.utcnow(),  # Set current time as default, will be updated after processing
            score_team_0=0,  # Will be updated after processing
            score_team_1=0,  # Will be updated after processing
            result="unknown",  # Will be updated after processing
            processed=False
        )
        
        db.add(match)
        db.commit()
        db.refresh(match)
        
        # Queue background processing using Celery
        task_result = await ReplayService.process_replay_file(
            match_id=str(match.id),
            file_content=file_content,
            filename=file.filename
        )

        logger.info(
            "Replay uploaded for processing",
            user_id=str(current_user.id),
            match_id=str(match.id),
            filename=file.filename,
            task_id=task_result.get("task_id")
        )

        return ReplayResponse(
            id=str(match.id),
            filename=file.filename,
            status="processing",
            message="Replay uploaded successfully and is being processed",
            uploaded_at=match.created_at,
            task_id=task_result.get("task_id")
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
            match_date=datetime.utcnow(),  # Set current time as default, will be updated after processing
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


@router.get("/task-status/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the status of a background processing task."""
    try:
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)

        if task_result.state == "PENDING":
            response = {
                "task_id": task_id,
                "state": "PENDING",
                "current": 0,
                "total": 100,
                "status": "Task is waiting to be processed..."
            }
        elif task_result.state == "PROGRESS":
            response = {
                "task_id": task_id,
                "state": "PROGRESS",
                "current": task_result.info.get("current", 0),
                "total": task_result.info.get("total", 100),
                "status": task_result.info.get("status", "Processing...")
            }
        elif task_result.state == "SUCCESS":
            response = {
                "task_id": task_id,
                "state": "SUCCESS",
                "current": 100,
                "total": 100,
                "status": "Task completed successfully!",
                "result": task_result.result
            }
        else:  # FAILURE
            response = {
                "task_id": task_id,
                "state": "FAILURE",
                "current": 0,
                "total": 100,
                "status": f"Task failed: {str(task_result.info)}",
                "error": str(task_result.info)
            }

        return response

    except Exception as e:
        logger.error("Failed to get task status", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task status"
        )


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


@router.post("/search-ballchasing", response_model=ReplaySearchResponse)
async def search_ballchasing_replays(
    search_request: ReplaySearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Search for replays on Ballchasing.com."""
    try:
        # Use the user's Steam ID if no player name provided
        player_name = search_request.player_name
        if not player_name and current_user.steam_id:
            # Convert Steam ID to player name if needed
            player_name = current_user.username

        search_results = await ballchasing_service.search_replays(
            player_name=player_name,
            playlist=search_request.playlist,
            season=search_request.season,
            count=search_request.count,
            sort_by=search_request.sort_by,
            sort_dir=search_request.sort_dir
        )

        if not search_results:
            return ReplaySearchResponse(
                replays=[],
                count=0,
                message="No replays found or search failed"
            )

        # Transform results to our format
        replays = []
        for replay in search_results.get("list", []):
            replays.append({
                "id": replay.get("id", ""),
                "title": replay.get("title", "Untitled"),
                "playlist": replay.get("playlist_name", "unknown"),
                "duration": replay.get("duration", 0),
                "date": replay.get("date", ""),
                "blue_score": replay.get("blue", {}).get("goals", 0),
                "orange_score": replay.get("orange", {}).get("goals", 0),
                "uploader": replay.get("uploader", {}).get("name", "Unknown")
            })

        logger.info(
            "Ballchasing search completed",
            user_id=str(current_user.id),
            results_count=len(replays)
        )

        return ReplaySearchResponse(
            replays=replays,
            count=len(replays),
            message=f"Found {len(replays)} replays"
        )

    except Exception as e:
        logger.error("Ballchasing search failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search replays"
        )


@router.get("/ballchasing/{replay_id}/preview")
async def preview_ballchasing_replay(
    replay_id: str,
    current_user: User = Depends(get_current_user)
):
    """Preview a Ballchasing.com replay before importing."""
    try:
        replay_stats = await ballchasing_service.get_replay_stats(replay_id)
        if not replay_stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Replay not found on Ballchasing.com"
            )

        match_info = replay_stats.get("match_info", {})
        players = replay_stats.get("players", [])

        # Find user in the replay if possible
        user_in_replay = None
        if current_user.steam_id:
            user_stats = ballchasing_service.extract_player_stats_for_user(replay_stats, current_user.steam_id)
            if user_stats:
                user_in_replay = {
                    "found": True,
                    "team": user_stats.get("team", "unknown"),
                    "score": user_stats.get("score", 0),
                    "goals": user_stats.get("goals", 0),
                    "assists": user_stats.get("assists", 0),
                    "saves": user_stats.get("saves", 0)
                }

        return {
            "replay_id": replay_id,
            "match_info": match_info,
            "players_count": len(players),
            "user_in_replay": user_in_replay or {"found": False},
            "can_import": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ballchasing preview failed", replay_id=replay_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview replay"
        )
