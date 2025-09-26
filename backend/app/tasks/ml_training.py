"""
Celery tasks for ML model training and retraining.
"""
from typing import Dict, Any, List
from celery import current_task
import structlog

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.match import Match
from app.models.user import User
from app.ml.training.model_trainer import ModelTrainer

logger = structlog.get_logger()


@celery_app.task(bind=True, name="app.tasks.ml_training.retrain_ml_models")
def retrain_ml_models(self, user_id: str = None) -> Dict[str, Any]:
    """
    Retrain ML models with new replay data.
    
    Args:
        user_id: Optional user ID to retrain models for specific user
        
    Returns:
        Dict containing training results
    """
    logger.info("Starting ML model retraining task",
               task_id=self.request.id,
               user_id=user_id)
    
    db = SessionLocal()
    try:
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Gathering training data..."}
        )
        
        # Get processed matches for training
        query = db.query(Match).filter(Match.processed == True)
        if user_id:
            query = query.filter(Match.user_id == user_id)
        
        matches = query.all()
        
        if len(matches) < 10:
            logger.warning("Insufficient data for retraining", 
                          matches_count=len(matches))
            return {
                "status": "skipped",
                "reason": "Insufficient training data",
                "matches_available": len(matches)
            }
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 30, "total": 100, "status": "Training weakness detector..."}
        )
        
        # Initialize trainer
        trainer = ModelTrainer()
        
        # Train models
        training_results = {}
        
        # Train weakness detector
        weakness_result = trainer.train_weakness_detector(matches)
        training_results["weakness_detector"] = weakness_result
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 60, "total": 100, "status": "Training skill analyzer..."}
        )
        
        # Train skill analyzer
        skill_result = trainer.train_skill_analyzer(matches)
        training_results["skill_analyzer"] = skill_result
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 90, "total": 100, "status": "Training recommendation engine..."}
        )
        
        # Train recommendation engine
        recommendation_result = trainer.train_recommendation_engine(matches)
        training_results["recommendation_engine"] = recommendation_result
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Training complete!"}
        )
        
        logger.info("ML model retraining completed",
                   matches_used=len(matches),
                   training_results=training_results)
        
        return {
            "status": "success",
            "matches_used": len(matches),
            "training_results": training_results
        }
        
    except Exception as e:
        logger.error("ML model retraining failed", error=str(e))
        
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Training failed"}
        )
        
        return {"error": str(e), "status": "failed"}
        
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.ml_training.analyze_new_replay")
def analyze_new_replay(self, match_id: str) -> Dict[str, Any]:
    """
    Analyze a newly processed replay with ML models.
    
    Args:
        match_id: UUID of the processed match
        
    Returns:
        Dict containing analysis results
    """
    logger.info("Starting ML analysis for new replay",
               task_id=self.request.id,
               match_id=match_id)
    
    db = SessionLocal()
    try:
        # Get match record
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match or not match.processed:
            logger.error("Match not found or not processed", match_id=match_id)
            return {"error": "Match not found or not processed", "status": "failed"}
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Loading ML models..."}
        )
        
        # Import ML models (avoid circular imports)
        from app.api.ml.model_manager import ModelManager
        
        model_manager = ModelManager()
        model_manager.set_db_session(db)
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Analyzing weaknesses..."}
        )
        
        # Perform weakness analysis
        weakness_detector = model_manager.get_weakness_detector()
        weakness_analysis = weakness_detector.analyze_player_weaknesses([match])
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Analyzing skills..."}
        )
        
        # Perform skill analysis
        skill_analyzer = model_manager.get_skill_analyzer()
        skill_analysis = skill_analyzer.analyze_player_skills([match])
        
        # Store analysis results
        match.weakness_analysis = {
            "weakness_analysis": weakness_analysis,
            "skill_analysis": skill_analysis,
            "analyzed_at": current_task.request.id
        }
        
        db.commit()
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Analysis complete!"}
        )
        
        logger.info("ML analysis completed for replay",
                   match_id=match_id)
        
        return {
            "status": "success",
            "match_id": match_id,
            "weakness_analysis": weakness_analysis,
            "skill_analysis": skill_analysis
        }
        
    except Exception as e:
        logger.error("ML analysis failed for replay",
                    match_id=match_id,
                    error=str(e))
        
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Analysis failed"}
        )
        
        return {"error": str(e), "status": "failed"}
        
    finally:
        db.close()
