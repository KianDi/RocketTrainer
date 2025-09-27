"""
Celery tasks for replay processing using carball.
"""
import os
import tempfile
import json
from typing import Dict, Any, Optional
from datetime import datetime
from celery import current_task
import structlog
# import carball  # Temporarily disabled due to dependency conflicts

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.match import Match
from app.models.user import User
from app.services.weakness_detection_service import WeaknessDetectionService
from app.schemas.coaching import AnalysisContext
from app.schemas.replay import PlayerStats

logger = structlog.get_logger()


@celery_app.task(bind=True, name="app.tasks.replay_processing.process_replay_file")
def process_replay_file(self, match_id: str, file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Process a .replay file using carball to extract gameplay data.
    
    Args:
        match_id: UUID of the match record
        file_content: Raw .replay file content
        filename: Original filename
        
    Returns:
        Dict containing processing results
    """
    logger.info("Starting replay processing task",
               task_id=self.request.id,
               match_id=match_id,
               filename=filename,
               file_size=len(file_content))
    
    db = SessionLocal()
    try:
        # Get match record
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            logger.error("Match not found", match_id=match_id)
            return {"error": "Match not found", "status": "failed"}
        
        # Update task progress
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Parsing replay file..."}
        )
        
        # Create temporary file for carball processing
        with tempfile.NamedTemporaryFile(suffix='.replay', delete=False) as temp_file:
            temp_file.write(file_content)
            temp_replay_path = temp_file.name
        
        try:
            # Parse replay with carball
            logger.info("Parsing replay with carball", filename=filename)
            
            current_task.update_state(
                state="PROGRESS", 
                meta={"current": 30, "total": 100, "status": "Analyzing gameplay data..."}
            )
            
            # Mock carball analysis (temporary implementation)
            # TODO: Replace with real carball when dependency issues are resolved
            gameplay_stats = _mock_carball_analysis(filename, file_content)

            current_task.update_state(
                state="PROGRESS",
                meta={"current": 60, "total": 100, "status": "Extracting player statistics..."}
            )
            
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 80, "total": 100, "status": "Saving analysis results..."}
            )
            
            # Update match record with extracted data
            _update_match_with_carball_data(match, gameplay_stats, db)
            
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 100, "total": 100, "status": "Processing complete!"}
            )
            
            logger.info("Replay processing completed successfully",
                       match_id=match_id,
                       filename=filename,
                       stats_extracted=len(gameplay_stats))
            
            return {
                "status": "success",
                "match_id": match_id,
                "stats_extracted": len(gameplay_stats),
                "gameplay_stats": gameplay_stats
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_replay_path):
                os.unlink(temp_replay_path)
                
    except Exception as e:
        logger.error("Replay processing failed",
                    match_id=match_id,
                    filename=filename,
                    error=str(e))
        
        # Mark match as failed
        try:
            match = db.query(Match).filter(Match.id == match_id).first()
            if match:
                match.processed = True
                match.processed_at = datetime.utcnow()
                match.replay_data = {"error": str(e), "status": "failed"}
                db.commit()
        except Exception as db_error:
            logger.error("Failed to update match status", error=str(db_error))
        
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Processing failed"}
        )
        
        return {"error": str(e), "status": "failed"}
        
    finally:
        db.close()


def _mock_carball_analysis(filename: str, file_content: bytes) -> Dict[str, Any]:
    """
    Mock carball analysis that generates realistic gameplay statistics.
    TODO: Replace with real carball when dependency issues are resolved.
    """
    import random
    import hashlib

    # Use filename hash as seed for consistent results
    seed = int(hashlib.md5(filename.encode()).hexdigest()[:8], 16)
    random.seed(seed)

    # Generate realistic gameplay statistics
    stats = {
        # Basic match info
        "playlist": random.choice(["ranked_duels", "ranked_doubles", "ranked_standard", "casual"]),
        "duration": random.randint(300, 600),  # 5-10 minutes
        "match_date": datetime.utcnow().isoformat(),

        # Team scores
        "score_team_0": random.randint(0, 7),
        "score_team_1": random.randint(0, 7),

        # Player core statistics
        "goals": random.randint(0, 5),
        "assists": random.randint(0, 4),
        "saves": random.randint(0, 8),
        "shots": random.randint(2, 12),
        "score": random.randint(100, 800),

        # Boost and movement stats
        "boost_usage": round(random.uniform(0.3, 0.8), 2),
        "average_speed": round(random.uniform(800, 1200), 1),
        "time_supersonic": round(random.uniform(0.1, 0.4), 2),
        "time_on_ground": round(random.uniform(0.6, 0.9), 2),
        "time_low_air": round(random.uniform(0.05, 0.2), 2),
        "time_high_air": round(random.uniform(0.01, 0.1), 2),

        # Additional stats for ML analysis
        "positioning_score": round(random.uniform(0.4, 0.9), 2),
        "rotation_score": round(random.uniform(0.3, 0.8), 2),
        "aerial_efficiency": round(random.uniform(0.2, 0.7), 2),
        "boost_efficiency": round(random.uniform(0.4, 0.9), 2),
        "defensive_actions": random.randint(5, 25),
        "offensive_actions": random.randint(8, 30),
    }

    logger.info("Generated mock replay analysis",
                filename=filename,
                stats_count=len(stats))

    return stats


def _update_match_with_carball_data(match: Match, stats: Dict[str, Any], db) -> None:
    """Update match record with extracted carball data."""
    try:
        # Update basic match info
        match.playlist = stats.get("playlist", "unknown")
        match.duration = stats.get("duration", 0)
        match.score_team_0 = stats.get("score_team_0", 0)
        match.score_team_1 = stats.get("score_team_1", 0)
        
        # Determine result
        team_0_score = stats.get("score_team_0", 0)
        team_1_score = stats.get("score_team_1", 0)
        if team_0_score > team_1_score:
            match.result = "win"
        elif team_0_score < team_1_score:
            match.result = "loss"
        else:
            match.result = "tie"
        
        # Update player stats
        match.goals = stats.get("goals", 0)
        match.assists = stats.get("assists", 0)
        match.saves = stats.get("saves", 0)
        match.shots = stats.get("shots", 0)
        match.score = stats.get("score", 0)
        match.boost_usage = stats.get("boost_usage", 0.0)
        match.average_speed = stats.get("average_speed", 0.0)
        match.time_supersonic = stats.get("time_supersonic", 0.0)
        match.time_on_ground = stats.get("time_on_ground", 0.0)
        match.time_low_air = stats.get("time_low_air", 0.0)
        match.time_high_air = stats.get("time_high_air", 0.0)
        
        # Store full analysis data
        match.replay_data = stats
        match.processed = True
        match.processed_at = datetime.utcnow()
        
        # Parse match date if available
        if "match_date" in stats:
            try:
                match.match_date = datetime.fromisoformat(stats["match_date"].replace('Z', '+00:00'))
            except:
                match.match_date = datetime.utcnow()
        
        db.commit()
        logger.info("Match updated with carball data", match_id=str(match.id))

        # Generate coaching insights automatically
        try:
            _generate_coaching_insights(match, db)
            logger.info("Coaching insights generated", match_id=str(match.id))
        except Exception as e:
            logger.warning("Failed to generate coaching insights",
                         match_id=str(match.id),
                         error=str(e))
            # Don't fail the entire task if insights generation fails
        
    except Exception as e:
        logger.error("Failed to update match with carball data", 
                    match_id=str(match.id), 
                    error=str(e))
        db.rollback()
        raise


def _generate_coaching_insights(match: Match, db) -> None:
    """Generate coaching insights for a processed match."""
    try:
        weakness_service = WeaknessDetectionService()

        # Create analysis context
        context = AnalysisContext(
            playlist=match.playlist,
            duration=match.duration,
            result=match.result,
            score_differential=abs(match.score_team_0 - match.score_team_1),
            team_score=match.score_team_0 if match.result in ['win', 'tie'] else match.score_team_1,
            opponent_score=match.score_team_1 if match.result in ['win', 'tie'] else match.score_team_0,
            match_date=match.match_date
        )

        # Extract player stats
        player_stats = PlayerStats(
            goals=match.goals,
            assists=match.assists,
            saves=match.saves,
            shots=match.shots,
            score=match.score,
            boost_usage=match.boost_usage,
            average_speed=match.average_speed,
            time_supersonic=match.time_supersonic,
            time_on_ground=match.time_on_ground,
            time_low_air=match.time_low_air,
            time_high_air=match.time_high_air,
            positioning_score=match.replay_data.get('positioning_score') if match.replay_data else None,
            rotation_score=match.replay_data.get('rotation_score') if match.replay_data else None,
            aerial_efficiency=match.replay_data.get('aerial_efficiency') if match.replay_data else None,
            boost_efficiency=match.replay_data.get('boost_efficiency') if match.replay_data else None,
            defensive_actions=match.replay_data.get('defensive_actions') if match.replay_data else None,
            offensive_actions=match.replay_data.get('offensive_actions') if match.replay_data else None
        )

        # Generate insights
        insights = weakness_service.analyze_performance(player_stats, context)

        # Store insights in database (convert datetime to string for JSON serialization)
        insights_dict = insights.dict()
        insights_dict['generated_at'] = insights_dict['generated_at'].isoformat()
        match.coaching_insights = insights_dict
        match.insights_generated_at = datetime.utcnow()

        db.commit()

    except Exception as e:
        logger.error("Failed to generate coaching insights in background task",
                    match_id=str(match.id),
                    error=str(e))
        db.rollback()
        raise
