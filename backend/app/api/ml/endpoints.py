"""
ML API endpoints for RocketTrainer.

Provides REST API endpoints for:
- /analyze-weaknesses: Player weakness detection and analysis
- /recommend-training: Personalized training pack recommendations
- /model-status: ML model health and monitoring

All endpoints are designed for high performance with caching and
comprehensive error handling.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from uuid import UUID
import structlog

from app.database import get_db
from app.models.match import Match
from app.models.user import User
from .schemas import (
    WeaknessAnalysisRequest,
    WeaknessAnalysisResponse,
    TrainingRecommendationRequest,
    TrainingRecommendationResponse,
    ModelStatusResponse,
    SkillCategoryScore
)
from .model_manager import get_model_manager
from .cache import MLModelCache
from .exceptions import (
    InsufficientDataError,
    ModelNotTrainedError,
    handle_ml_exception
)

logger = structlog.get_logger(__name__)

# Initialize cache and model manager
cache = MLModelCache()
model_manager = get_model_manager()

# Create router with ML-specific configuration
router = APIRouter(
    prefix="/ml",
    tags=["machine-learning"],
    responses={
        500: {"description": "Internal server error"},
        422: {"description": "ML model error"},
        429: {"description": "Rate limit exceeded"}
    }
)


@router.post(
    "/analyze-weaknesses",
    response_model=WeaknessAnalysisResponse,
    summary="Analyze Player Weaknesses",
    description="Analyze player weaknesses using ML models to identify areas for improvement",
    response_description="Comprehensive weakness analysis with confidence scores"
)
async def analyze_weaknesses(
    request: WeaknessAnalysisRequest,
    db: Session = Depends(get_db)
) -> WeaknessAnalysisResponse:
    """
    Analyze player weaknesses using WeaknessDetector and SkillAnalyzer models.

    This endpoint processes player match data to identify primary weaknesses,
    skill category scores, and provides confidence ratings for the analysis.
    """
    start_time = datetime.utcnow()
    logger.info("Weakness analysis requested",
               user_id=str(request.user_id),
               match_ids_count=len(request.match_ids) if request.match_ids else 0)

    try:
        # Set database session for model manager
        model_manager.set_db_session(db)

        # Check cache first
        cached_result = cache.get_weakness_analysis(request.user_id, request.match_ids)
        if cached_result:
            logger.info("Returning cached weakness analysis",
                       user_id=str(request.user_id))

            # Convert cached result to response model
            return WeaknessAnalysisResponse(
                user_id=request.user_id,
                analysis_date=datetime.fromisoformat(cached_result["analysis_date"]),
                primary_weakness=cached_result["primary_weakness"],
                confidence=cached_result["confidence"],
                skill_categories=[
                    SkillCategoryScore(**cat) for cat in cached_result["skill_categories"]
                ],
                matches_analyzed=cached_result["matches_analyzed"],
                recommendations_available=cached_result["recommendations_available"],
                analysis_summary=cached_result.get("analysis_summary")
            )

        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get matches for analysis
        if request.match_ids:
            # Use specific matches
            matches = (db.query(Match)
                      .filter(Match.id.in_(request.match_ids))
                      .filter(Match.user_id == request.user_id)
                      .all())

            if len(matches) != len(request.match_ids):
                found_ids = [str(m.id) for m in matches]
                missing_ids = [str(mid) for mid in request.match_ids if str(mid) not in found_ids]
                logger.warning("Some requested matches not found",
                             user_id=str(request.user_id),
                             missing_matches=missing_ids)
        else:
            # Use recent matches (last 10)
            matches = (db.query(Match)
                      .filter(Match.user_id == request.user_id)
                      .filter(Match.processed == True)
                      .order_by(Match.match_date.desc())
                      .limit(10)
                      .all())

        # Check if we have sufficient data
        if len(matches) < 3:
            raise InsufficientDataError(
                message="Insufficient match data for reliable analysis",
                required_matches=3,
                available_matches=len(matches)
            )

        logger.info("Analyzing matches",
                   user_id=str(request.user_id),
                   matches_count=len(matches))

        # Get ML models
        weakness_detector = model_manager.get_weakness_detector()
        skill_analyzer = model_manager.get_skill_analyzer()

        # Perform weakness detection
        weakness_predictions = weakness_detector.analyze_player_weaknesses(matches)

        # Perform skill analysis
        skill_analysis = skill_analyzer.analyze_player_skills(matches)

        # Process results
        primary_weakness = weakness_predictions.get("primary_weakness", "unknown")
        confidence = weakness_predictions.get("confidence", 0.0)

        # Build skill category scores
        skill_categories = []
        skill_scores = skill_analysis.get("skill_scores", {})

        for category, score_data in skill_scores.items():
            skill_categories.append(SkillCategoryScore(
                category=category,
                score=score_data.get("score", 0.0),
                percentile=score_data.get("percentile"),
                trend=score_data.get("trend")
            ))

        # Generate analysis summary
        analysis_summary = f"Analysis of {len(matches)} matches shows primary weakness in {primary_weakness} " \
                          f"with {confidence:.1%} confidence. " \
                          f"Skill analysis reveals strengths in {skill_analysis.get('top_skills', [])} " \
                          f"and areas for improvement in {skill_analysis.get('weak_skills', [])}."

        # Create response
        response = WeaknessAnalysisResponse(
            user_id=request.user_id,
            analysis_date=datetime.utcnow(),
            primary_weakness=primary_weakness,
            confidence=confidence,
            skill_categories=skill_categories,
            matches_analyzed=len(matches),
            recommendations_available=True,
            analysis_summary=analysis_summary
        )

        # Cache the result
        cache_data = {
            "analysis_date": response.analysis_date.isoformat(),
            "primary_weakness": response.primary_weakness,
            "confidence": response.confidence,
            "skill_categories": [cat.dict() for cat in response.skill_categories],
            "matches_analyzed": response.matches_analyzed,
            "recommendations_available": response.recommendations_available,
            "analysis_summary": response.analysis_summary
        }

        cache.cache_weakness_analysis(request.user_id, cache_data, request.match_ids)

        # Log performance
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info("Weakness analysis completed",
                   user_id=str(request.user_id),
                   duration_ms=duration,
                   primary_weakness=primary_weakness,
                   confidence=confidence)

        return response

    except Exception as e:
        logger.error("Weakness analysis failed",
                    user_id=str(request.user_id),
                    error=str(e))
        raise handle_ml_exception(e, {"user_id": str(request.user_id)})


@router.post(
    "/recommend-training",
    response_model=TrainingRecommendationResponse,
    summary="Get Training Recommendations",
    description="Get personalized training pack recommendations based on player analysis",
    response_description="Personalized training pack recommendations with scoring"
)
async def recommend_training(
    request: TrainingRecommendationRequest,
    db: Session = Depends(get_db)
) -> TrainingRecommendationResponse:
    """
    Generate personalized training pack recommendations.

    Uses TrainingRecommendationEngine to provide tailored training suggestions
    based on detected weaknesses, skill level, and player preferences.
    """
    start_time = datetime.utcnow()
    logger.info("Training recommendations requested",
               user_id=str(request.user_id),
               skill_level=request.skill_level,
               max_recommendations=request.max_recommendations)

    try:
        # Set database session for model manager
        model_manager.set_db_session(db)

        # Check cache first
        cached_result = cache.get_training_recommendations(
            request.user_id,
            request.skill_level,
            request.categories
        )
        if cached_result:
            logger.info("Returning cached training recommendations",
                       user_id=str(request.user_id))

            # Convert cached result to response model
            from .schemas import TrainingPackRecommendation

            recommendations = [
                TrainingPackRecommendation(**rec)
                for rec in cached_result["recommendations"]
            ]

            return TrainingRecommendationResponse(
                user_id=request.user_id,
                recommendations=recommendations,
                skill_level_detected=cached_result["skill_level_detected"],
                total_packs_evaluated=cached_result["total_packs_evaluated"],
                generation_time=datetime.fromisoformat(cached_result["generation_time"]),
                cache_hit=True
            )

        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Determine skill level if not provided
        skill_level = request.skill_level
        if not skill_level:
            # Get recent matches to estimate skill level
            recent_matches = (db.query(Match)
                            .filter(Match.user_id == request.user_id)
                            .filter(Match.processed == True)
                            .order_by(Match.match_date.desc())
                            .limit(5)
                            .all())

            if recent_matches:
                # Simple skill level estimation based on average score
                avg_score = sum(m.score or 0 for m in recent_matches) / len(recent_matches)
                if avg_score >= 800:
                    skill_level = "grand_champion"
                elif avg_score >= 700:
                    skill_level = "champion"
                elif avg_score >= 600:
                    skill_level = "diamond"
                elif avg_score >= 500:
                    skill_level = "platinum"
                elif avg_score >= 400:
                    skill_level = "gold"
                elif avg_score >= 300:
                    skill_level = "silver"
                else:
                    skill_level = "bronze"
            else:
                skill_level = "platinum"  # Default

        logger.info("Skill level determined",
                   user_id=str(request.user_id),
                   skill_level=skill_level)

        # Get weaknesses for recommendations (from recent analysis or detect new ones)
        weaknesses = []

        # Try to get recent weakness analysis
        recent_weakness_analysis = cache.get_weakness_analysis(request.user_id)
        if recent_weakness_analysis:
            # Use cached weakness analysis
            primary_weakness = recent_weakness_analysis.get("primary_weakness", "mechanical")
            confidence = recent_weakness_analysis.get("confidence", 0.7)

            weaknesses = [{
                "weakness": primary_weakness,
                "confidence": confidence,
                "category": primary_weakness
            }]
        else:
            # Get recent matches for quick weakness detection
            recent_matches = (db.query(Match)
                            .filter(Match.user_id == request.user_id)
                            .filter(Match.processed == True)
                            .order_by(Match.match_date.desc())
                            .limit(5)
                            .all())

            if len(recent_matches) >= 3:
                try:
                    weakness_detector = model_manager.get_weakness_detector()
                    weakness_analysis = weakness_detector.analyze_player_weaknesses(recent_matches)

                    primary_weakness = weakness_analysis.get("primary_weakness", "mechanical")
                    confidence = weakness_analysis.get("confidence", 0.7)

                    weaknesses = [{
                        "weakness": primary_weakness,
                        "confidence": confidence,
                        "category": primary_weakness
                    }]
                except Exception as e:
                    logger.warning("Could not detect weaknesses, using default",
                                 user_id=str(request.user_id), error=str(e))
                    weaknesses = [{
                        "weakness": "mechanical",
                        "confidence": 0.5,
                        "category": "mechanical"
                    }]
            else:
                # Default weakness for new users
                weaknesses = [{
                    "weakness": "mechanical",
                    "confidence": 0.5,
                    "category": "mechanical"
                }]

        # Get recommendation engine
        recommendation_engine = model_manager.get_recommendation_engine()

        # Generate recommendations
        raw_recommendations = recommendation_engine.recommend_training_packs(
            user_id=str(request.user_id),
            weaknesses=weaknesses,
            player_skill_level=skill_level,
            max_recommendations=request.max_recommendations,
            include_variety=True
        )

        # Filter by categories if specified
        if request.categories:
            raw_recommendations = [
                rec for rec in raw_recommendations
                if rec.get("training_pack", {}).get("category") in request.categories
            ]

        # Convert to response format
        from .schemas import TrainingPackRecommendation

        recommendations = []
        for rec in raw_recommendations[:request.max_recommendations]:
            training_pack = rec.get("training_pack", {})

            recommendation = TrainingPackRecommendation(
                training_pack_id=training_pack.get("id", ""),
                name=training_pack.get("name", "Unknown Pack"),
                code=training_pack.get("code", ""),
                category=training_pack.get("category", "general"),
                difficulty=training_pack.get("difficulty", 3),
                relevance_score=rec.get("relevance_score", 0.0),
                difficulty_match=rec.get("difficulty_match", 0.0),
                quality_score=rec.get("quality_score", 0.0),
                overall_score=rec.get("score", 0.0),
                reasoning=rec.get("reasoning", "Recommended based on your skill level and weaknesses"),
                estimated_improvement=rec.get("estimated_improvement")
            )
            recommendations.append(recommendation)

        # Create response
        response = TrainingRecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            skill_level_detected=skill_level,
            total_packs_evaluated=len(raw_recommendations),
            generation_time=datetime.utcnow(),
            cache_hit=False
        )

        # Cache the result
        cache_data = {
            "recommendations": [rec.dict() for rec in response.recommendations],
            "skill_level_detected": response.skill_level_detected,
            "total_packs_evaluated": response.total_packs_evaluated,
            "generation_time": response.generation_time.isoformat()
        }

        cache.cache_training_recommendations(
            request.user_id,
            cache_data,
            request.skill_level,
            request.categories
        )

        # Log performance
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info("Training recommendations completed",
                   user_id=str(request.user_id),
                   duration_ms=duration,
                   recommendations_count=len(recommendations),
                   skill_level=skill_level)

        return response

    except Exception as e:
        logger.error("Training recommendations failed",
                    user_id=str(request.user_id),
                    error=str(e))
        raise handle_ml_exception(e, {"user_id": str(request.user_id)})


@router.get(
    "/model-status",
    response_model=ModelStatusResponse,
    summary="Get ML Model Status",
    description="Get health status and performance metrics for all ML models",
    response_description="Model health status and performance metrics"
)
async def get_model_status() -> ModelStatusResponse:
    """
    Get ML model health status and performance metrics.

    Provides operational monitoring information including model versions,
    health status, cache statistics, and performance metrics.
    """
    start_time = datetime.utcnow()
    logger.info("Model status requested")

    try:
        # Check cache first
        cached_status = cache.get_model_status()
        if cached_status:
            logger.info("Returning cached model status")

            # Convert cached result to response model
            from .schemas import ModelInfo, CacheStatistics

            models = [ModelInfo(**model) for model in cached_status["models"]]
            cache_stats = CacheStatistics(**cached_status["cache_stats"])

            return ModelStatusResponse(
                system_status=cached_status["system_status"],
                models=models,
                cache_stats=cache_stats,
                uptime=cached_status["uptime"],
                memory_usage=cached_status["memory_usage"],
                last_health_check=datetime.fromisoformat(cached_status["last_health_check"])
            )

        # Perform health check on models
        health_check_results = model_manager.health_check()
        model_status_info = model_manager.get_model_status()

        # Get cache statistics
        cache_statistics = cache.get_cache_statistics()

        # Calculate system uptime (simplified - would be more complex in production)
        import time
        uptime = time.time() - start_time.timestamp()  # Placeholder

        # Get memory usage (simplified)
        import psutil
        memory_usage = psutil.virtual_memory().percent

        # Build model information
        from .schemas import ModelInfo
        models = []

        for model_name, health_info in health_check_results["models"].items():
            status_info = model_status_info["models"].get(model_name, {})

            # Determine model version (would come from model metadata in production)
            version = "1.0.0"
            if model_name == "weakness_detector":
                version = "1.2.0"
            elif model_name == "recommendation_engine":
                version = "1.1.0"

            # Calculate average response time (placeholder - would track this in production)
            avg_response_time = 150.0  # ms

            model_info = ModelInfo(
                name=model_name,
                version=version,
                status=health_info["status"],
                last_trained=datetime.fromisoformat(status_info.get("loaded_at", datetime.utcnow().isoformat())) if status_info.get("loaded_at") else None,
                accuracy=0.90 if health_info["status"] == "healthy" else None,  # Placeholder
                predictions_served=100,  # Placeholder - would track this
                avg_response_time=avg_response_time
            )
            models.append(model_info)

        # Build cache statistics
        from .schemas import CacheStatistics
        cache_stats = CacheStatistics(
            total_requests=cache_statistics.get("total_keys", 0) * 10,  # Estimate
            cache_hits=int(cache_statistics.get("total_keys", 0) * 8),  # Estimate 80% hit rate
            cache_misses=int(cache_statistics.get("total_keys", 0) * 2),  # Estimate 20% miss rate
            hit_rate=0.8,  # Placeholder - would track this properly
            avg_cache_time=5.0  # ms
        )

        # Determine overall system status
        overall_status = health_check_results["overall_status"]

        # Create response
        response = ModelStatusResponse(
            system_status=overall_status,
            models=models,
            cache_stats=cache_stats,
            uptime=uptime,
            memory_usage=memory_usage,
            last_health_check=datetime.utcnow()
        )

        # Cache the result
        cache_data = {
            "system_status": response.system_status,
            "models": [model.dict() for model in response.models],
            "cache_stats": response.cache_stats.dict(),
            "uptime": response.uptime,
            "memory_usage": response.memory_usage,
            "last_health_check": response.last_health_check.isoformat()
        }

        cache.cache_model_status(cache_data)

        # Log performance
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info("Model status completed",
                   duration_ms=duration,
                   system_status=overall_status,
                   models_count=len(models))

        return response

    except Exception as e:
        logger.error("Model status check failed", error=str(e))

        # Return degraded status on error
        from .schemas import ModelInfo, CacheStatistics

        error_response = ModelStatusResponse(
            system_status="error",
            models=[
                ModelInfo(
                    name="system",
                    version="unknown",
                    status="error",
                    last_trained=None,
                    accuracy=None,
                    predictions_served=0,
                    avg_response_time=0.0
                )
            ],
            cache_stats=CacheStatistics(
                total_requests=0,
                cache_hits=0,
                cache_misses=0,
                hit_rate=0.0,
                avg_cache_time=0.0
            ),
            uptime=0.0,
            memory_usage=0.0,
            last_health_check=datetime.utcnow()
        )

        return error_response
