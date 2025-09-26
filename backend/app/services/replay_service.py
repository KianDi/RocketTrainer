"""
Replay processing service for analyzing Rocket League replays.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import structlog

from app.config import settings
from app.database import SessionLocal
from app.models.match import Match
from app.models.user import User
from app.models.player_stats import PlayerStats
from app.services.ballchasing_service import ballchasing_service

logger = structlog.get_logger()


class ReplayService:
    """Service for processing and analyzing replay files."""
    
    @staticmethod
    async def process_replay_file(match_id: str, file_content: bytes, filename: str):
        """
        Process an uploaded replay file using Celery background task.
        This method now delegates to the Celery task for actual processing.
        """
        logger.info("Queuing replay file for processing",
                   match_id=match_id,
                   filename=filename,
                   file_size=len(file_content))

        try:
            # Import here to avoid circular imports
            from app.tasks.replay_processing import process_replay_file as process_task

            # Queue the processing task
            task = process_task.delay(match_id, file_content, filename)

            logger.info("Replay processing task queued",
                       match_id=match_id,
                       task_id=task.id,
                       filename=filename)

            return {"task_id": task.id, "status": "queued"}

        except Exception as e:
            logger.error("Failed to queue replay processing task",
                        match_id=match_id,
                        filename=filename,
                        error=str(e))

            # Mark match as failed immediately
            db = SessionLocal()
            try:
                match = db.query(Match).filter(Match.id == match_id).first()
                if match:
                    match.processed = True
                    match.processed_at = datetime.utcnow()
                    match.replay_data = {"error": f"Failed to queue processing: {str(e)}", "status": "failed"}
                    db.commit()
            except Exception as db_error:
                logger.error("Failed to update match status", error=str(db_error))
            finally:
                db.close()

            raise
    
    @staticmethod
    async def process_ballchasing_replay(match_id: str, ballchasing_id: str):
        """Process a replay from Ballchasing.com using the actual API."""
        logger.info("🚀 BACKGROUND TASK STARTED - Ballchasing replay processing",
                   match_id=match_id,
                   ballchasing_id=ballchasing_id)

        # Step 1: Get match and user info with a short, separate transaction
        match_info = None
        user_steam_id = None

        db = SessionLocal()
        try:
            match = db.query(Match).filter(Match.id == match_id).first()
            if not match:
                logger.error("Match not found for processing", match_id=match_id)
                return

            user = db.query(User).filter(User.id == match.user_id).first()
            if not user:
                logger.error("User not found for match", match_id=match_id, user_id=str(match.user_id))
                return

            # Store the info we need
            match_info = {
                'id': match.id,
                'user_id': match.user_id,
                'ballchasing_id': match.ballchasing_id
            }
            user_steam_id = user.steam_id

        except Exception as e:
            logger.error("Error fetching match info", match_id=match_id, error=str(e))
            ReplayService._mark_match_failed(match_id, str(e))
            return
        finally:
            db.close()

        # Step 2: Fetch replay data from Ballchasing.com (no database involved)
        try:
            replay_stats = await ballchasing_service.get_replay_stats(ballchasing_id)
            if not replay_stats:
                logger.error("Failed to fetch replay from Ballchasing", ballchasing_id=ballchasing_id)
                ReplayService._mark_match_failed(match_id, "Failed to fetch from Ballchasing.com")
                return
        except Exception as e:
            logger.error("Error fetching replay stats", ballchasing_id=ballchasing_id, error=str(e))
            ReplayService._mark_match_failed(match_id, f"Error fetching replay: {str(e)}")
            return

        # Step 3: Process the replay data
        try:
            # Extract match information
            match_info_data = replay_stats.get("match_info", {})
            score = match_info_data.get("score", {})

            # Extract match information with detailed logging
            logger.info("Processing match data",
                       match_id=match_id,
                       playlist=match_info_data.get("playlist", "unknown"),
                       duration=match_info_data.get("duration", 0),
                       blue_score=score.get("blue", 0),
                       orange_score=score.get("orange", 0))

            # Find user's stats in the replay
            user_stats = ballchasing_service.extract_player_stats_for_user(replay_stats, user_steam_id)

            # Log user stats extraction result
            if user_stats:
                logger.info("User stats extracted successfully",
                           match_id=match_id,
                           user_steam_id=user_steam_id,
                           player_name=user_stats.get("player_name", "unknown"),
                           goals=user_stats.get("goals", 0),
                           assists=user_stats.get("assists", 0),
                           saves=user_stats.get("saves", 0),
                           shots=user_stats.get("shots", 0),
                           score=user_stats.get("score", 0))
            else:
                logger.warning("No user stats extracted",
                             match_id=match_id,
                             user_steam_id=user_steam_id)

            # Prepare match updates
            match_updates = {
                'playlist': match_info_data.get("playlist", "unknown"),
                'duration': match_info_data.get("duration", 0),
                'score_team_0': score.get("blue", 0),
                'score_team_1': score.get("orange", 0),
                'replay_data': replay_stats,
                'processed': True,
                'processed_at': datetime.now(timezone.utc)
            }

            # Parse match date
            try:
                if match_info_data.get("date"):
                    match_updates['match_date'] = datetime.fromisoformat(match_info_data["date"].replace("Z", "+00:00"))
                else:
                    match_updates['match_date'] = datetime.now(timezone.utc)
            except:
                match_updates['match_date'] = datetime.now(timezone.utc)

            # Add user stats to match updates if available
            if user_stats:
                # Add player stats to updates
                player_stats_updates = {
                    'goals': user_stats.get("goals", 0),
                    'assists': user_stats.get("assists", 0),
                    'saves': user_stats.get("saves", 0),
                    'shots': user_stats.get("shots", 0),
                    'score': user_stats.get("score", 0),
                    'boost_usage': user_stats.get("boost_usage", 0.0),
                    'average_speed': user_stats.get("average_speed", 0.0),
                    'time_supersonic': user_stats.get("time_supersonic", 0.0),
                    'time_on_ground': user_stats.get("time_on_ground", 0.0),
                    'time_low_air': user_stats.get("time_low_air", 0.0),
                    'time_high_air': user_stats.get("time_high_air", 0.0)
                }

                match_updates.update(player_stats_updates)

                logger.info("Added player stats to match updates",
                           match_id=match_id,
                           player_stats=player_stats_updates)

                # Determine result based on team and score
                user_team = user_stats.get("team", "blue")
                if user_team == "blue":
                    match_updates['result'] = "win" if score.get("blue", 0) > score.get("orange", 0) else "loss"
                else:
                    match_updates['result'] = "win" if score.get("orange", 0) > score.get("blue", 0) else "loss"

                if score.get("blue", 0) == score.get("orange", 0):
                    match_updates['result'] = "draw"

                logger.info("Determined match result",
                           match_id=match_id,
                           user_team=user_team,
                           result=match_updates['result'])
            else:
                logger.warning("User not found in replay", ballchasing_id=ballchasing_id, user_steam_id=user_steam_id)
                match_updates['result'] = "unknown"

            # Log final match updates before database operation
            logger.info("Final match updates prepared",
                       match_id=match_id,
                       updates_keys=list(match_updates.keys()),
                       playlist=match_updates.get('playlist'),
                       duration=match_updates.get('duration'),
                       goals=match_updates.get('goals', 'not_set'),
                       score=match_updates.get('score', 'not_set'),
                       processed=match_updates.get('processed'))

        except Exception as e:
            logger.error("Error processing replay data", ballchasing_id=ballchasing_id, error=str(e))
            ReplayService._mark_match_failed(match_id, f"Error processing replay: {str(e)}")
            return

        # Step 4: Update the database with a fresh, short transaction
        ReplayService._update_match_with_data(match_id, match_updates)
        logger.info("Ballchasing replay processed successfully", match_id=match_id, ballchasing_id=ballchasing_id)

    @staticmethod
    def _mark_match_failed(match_id: str, error_message: str):
        """Mark a match as failed with error message."""
        db = SessionLocal()
        try:
            match = db.query(Match).filter(Match.id == match_id).first()
            if match:
                match.processed = True
                match.processed_at = datetime.now(timezone.utc)
                match.replay_data = {"error": error_message, "status": "failed"}
                db.commit()
                logger.info("Match marked as failed", match_id=match_id, error=error_message)
        except Exception as e:
            logger.error("Failed to mark match as failed", match_id=match_id, error=str(e))
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def _update_match_with_data(match_id: str, match_updates: Dict[str, Any]):
        """Update match with processed data using a fresh transaction."""
        logger.info("Starting database update",
                   match_id=match_id,
                   update_fields=list(match_updates.keys()),
                   goals_value=match_updates.get('goals', 'not_provided'),
                   score_value=match_updates.get('score', 'not_provided'))

        db = SessionLocal()
        try:
            match = db.query(Match).filter(Match.id == match_id).first()
            if match:
                logger.info("Match found in database",
                           match_id=match_id,
                           current_goals=match.goals,
                           current_score=match.score,
                           current_processed=match.processed)

                # Log before updating each field
                for field, value in match_updates.items():
                    old_value = getattr(match, field, None)
                    setattr(match, field, value)
                    logger.debug("Updated field",
                               match_id=match_id,
                               field=field,
                               old_value=old_value,
                               new_value=value)

                # Flush to ensure changes are prepared
                db.flush()

                # Log values before commit
                logger.info("About to commit changes",
                           match_id=match_id,
                           goals_after_update=match.goals,
                           score_after_update=match.score,
                           playlist_after_update=match.playlist,
                           processed_after_update=match.processed)

                db.commit()

                # Verify the commit worked by refreshing and checking
                db.refresh(match)
                logger.info("Match updated and committed successfully",
                           match_id=match_id,
                           final_goals=match.goals,
                           final_score=match.score,
                           final_playlist=match.playlist,
                           final_duration=match.duration,
                           final_processed=match.processed)
            else:
                logger.error("Match not found for update", match_id=match_id)
        except Exception as e:
            logger.error("Failed to update match",
                        match_id=match_id,
                        error=str(e),
                        error_type=type(e).__name__)
            db.rollback()
            # Re-raise to see full traceback
            raise
        finally:
            db.close()

    @staticmethod
    async def _create_player_stats_record(match: Match, user_stats: Optional[Dict[str, Any]], replay_stats: Dict[str, Any]):
        """Create detailed player stats records in the time-series database."""
        if not user_stats:
            return

        # Use a new database session for player stats
        db = SessionLocal()
        try:
            # Create player stats record for time-series analysis
            player_stat = PlayerStats(
                time=match.match_date,
                user_id=match.user_id,
                match_id=match.id,
                stat_type="match_performance",
                category="core",
                value=float(user_stats.get("score", 0)),
                playlist=match.playlist,
                sample_size=1.0
            )
            db.add(player_stat)

            # Add individual stat records for detailed analysis
            stats_to_record = [
                ("goals", "core", user_stats.get("goals", 0)),
                ("assists", "core", user_stats.get("assists", 0)),
                ("saves", "core", user_stats.get("saves", 0)),
                ("shots", "core", user_stats.get("shots", 0)),
                ("boost_usage", "boost", user_stats.get("boost_usage", 0.0)),
                ("average_speed", "movement", user_stats.get("average_speed", 0.0)),
                ("time_supersonic", "movement", user_stats.get("time_supersonic", 0.0)),
                ("time_on_ground", "positioning", user_stats.get("time_on_ground", 0.0)),
                ("time_low_air", "positioning", user_stats.get("time_low_air", 0.0)),
                ("time_high_air", "positioning", user_stats.get("time_high_air", 0.0)),
            ]

            for stat_name, category, value in stats_to_record:
                if value is not None:
                    stat_record = PlayerStats(
                        time=match.match_date,
                        user_id=match.user_id,
                        match_id=match.id,
                        stat_type=stat_name,
                        category=category,
                        value=float(value),
                        playlist=match.playlist,
                        sample_size=1.0
                    )
                    db.add(stat_record)

            db.commit()
            logger.info("Player stats records created", match_id=str(match.id), stats_count=len(stats_to_record) + 1)

        except Exception as e:
            logger.error("Failed to create player stats records", match_id=str(match.id), error=str(e))
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def _mock_replay_analysis(filename: str) -> Dict[str, Any]:
        """Create mock replay analysis data for MVP."""
        import random
        
        playlists = ["ranked-duels", "ranked-doubles", "ranked-standard"]
        results = ["win", "loss"]
        
        return {
            "playlist": random.choice(playlists),
            "duration": random.randint(240, 420),  # 4-7 minutes
            "score_team_0": random.randint(0, 5),
            "score_team_1": random.randint(0, 5),
            "result": random.choice(results),
            "player_stats": {
                "goals": random.randint(0, 3),
                "assists": random.randint(0, 2),
                "saves": random.randint(0, 4),
                "shots": random.randint(1, 8),
                "score": random.randint(100, 800),
                "boost_usage": round(random.uniform(0.3, 0.9), 2),
                "average_speed": round(random.uniform(800, 1200), 1),
                "time_supersonic": round(random.uniform(10, 60), 1),
                "time_on_ground": round(random.uniform(60, 90), 1),
                "time_low_air": round(random.uniform(5, 20), 1),
                "time_high_air": round(random.uniform(1, 10), 1)
            },
            "analysis_version": "1.0.0",
            "processed_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _mock_ballchasing_analysis(ballchasing_id: str) -> Dict[str, Any]:
        """Create mock Ballchasing analysis data for MVP."""
        analysis = ReplayService._mock_replay_analysis(f"ballchasing_{ballchasing_id}")
        analysis["ballchasing_id"] = ballchasing_id
        analysis["source"] = "ballchasing.com"
        return analysis
