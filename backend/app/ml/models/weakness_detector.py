"""
Weakness Detection Model for RocketTrainer

Identifies player weaknesses across different skill categories using
machine learning classification and statistical analysis.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
import structlog

from .base import BaseMLModel
from ..config import ml_config, SkillCategory
from ..features.pipeline import FeatureEngineeringPipeline
from ..utils import performance_monitor
from ...models.match import Match

logger = structlog.get_logger(__name__)


class WeaknessDetector(BaseMLModel):
    """ML model for detecting player weaknesses across skill categories."""
    
    def __init__(self,
                 model_type: str = "random_forest",
                 n_estimators: int = 100,
                 max_depth: Optional[int] = None,
                 random_state: Optional[int] = None):
        """
        Initialize weakness detection model.

        Args:
            model_type: Type of model ('random_forest', 'gradient_boosting')
            n_estimators: Number of trees in ensemble
            max_depth: Maximum depth of trees
            random_state: Random state for reproducibility
        """
        super().__init__(model_name="WeaknessDetector")
        
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state or ml_config.random_state
        
        # Initialize model
        self.model = self._create_model()
        
        # Weakness detection specific attributes
        self.skill_categories = list(ml_config.skill_categories)
        self.confidence_threshold = ml_config.confidence_threshold
        
        # Feature engineering pipeline
        self.feature_pipeline = FeatureEngineeringPipeline(
            use_feature_selection=True,
            selection_method="mutual_info",
            k_features=20  # Focus on top 20 most relevant features
        )
        
        logger.info("WeaknessDetector initialized",
                   model_type=model_type,
                   n_estimators=n_estimators,
                   skill_categories=len(self.skill_categories))
    
    def _create_model(self):
        """Create the appropriate ML model based on configuration."""
        if self.model_type == "random_forest":
            return RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                random_state=self.random_state,
                class_weight='balanced',  # Handle imbalanced classes
                n_jobs=-1
            )
        elif self.model_type == "gradient_boosting":
            return GradientBoostingClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth or 3,
                random_state=self.random_state,
                learning_rate=0.1
            )
        else:
            logger.warning("Unknown model type, using RandomForest", model_type=self.model_type)
            return RandomForestClassifier(
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                n_jobs=-1
            )
    
    def _create_weakness_labels(self, matches: List[Match]) -> np.ndarray:
        """
        Create weakness labels from match performance data.

        This is a heuristic approach for initial model training.
        In production, labels would come from expert analysis or user feedback.
        """
        labels = []
        available_categories = [cat.value for cat in self.skill_categories]

        for match in matches:
            # Calculate performance metrics
            shot_accuracy = match.goals / max(match.shots, 1)
            save_rate = match.saves / max(match.match_duration_minutes, 1)
            score_efficiency = match.score / max(match.match_duration_minutes, 1)

            # Determine primary weakness based on performance
            # Use only categories that exist in our skill_categories
            if shot_accuracy < 0.3 and "shooting" in available_categories:
                weakness = "shooting"
            elif save_rate < 0.5 and "defending" in available_categories:
                weakness = "defending"
            elif match.boost_usage and match.boost_usage > 0.8 and "boost_management" in available_categories:
                weakness = "boost_management"
            elif score_efficiency < 50 and "mechanical" in available_categories:
                weakness = "mechanical"
            elif "positioning" in available_categories:
                weakness = "positioning"
            else:
                # Default to first available category
                weakness = available_categories[0]

            # Convert to category index
            weakness_idx = available_categories.index(weakness)
            labels.append(weakness_idx)

        return np.array(labels)
    
    def train(self, matches: List[Match], validation_split: float = 0.2) -> Dict[str, Any]:
        """
        Train the weakness detection model.
        
        Args:
            matches: Training matches
            validation_split: Fraction of data for validation
            
        Returns:
            Training results and metrics
        """
        try:
            logger.info("Training weakness detection model", 
                       matches=len(matches),
                       validation_split=validation_split)
            
            if len(matches) < ml_config.min_matches_required:
                raise ValueError(f"Insufficient matches for training: {len(matches)} < {ml_config.min_matches_required}")
            
            # Create weakness labels
            y = self._create_weakness_labels(matches)
            
            # Extract and preprocess features
            X = self.feature_pipeline.fit_transform(matches, y)
            
            logger.info("Feature extraction completed",
                       samples=X.shape[0],
                       features=X.shape[1])
            
            # Validate data quality
            if X.shape[0] != len(y):
                raise ValueError(f"Feature matrix and labels size mismatch: {X.shape[0]} != {len(y)}")
            
            # Train model
            self.model.fit(X, y)
            
            # Cross-validation evaluation
            cv_scores = cross_val_score(
                self.model, X, y,
                cv=StratifiedKFold(n_splits=min(5, len(matches)), shuffle=True, random_state=self.random_state),
                scoring='accuracy'
            )
            
            # Calculate training metrics
            y_pred = self.model.predict(X)
            y_pred_proba = self.model.predict_proba(X)
            
            training_results = {
                "model_type": self.model_type,
                "training_samples": len(matches),
                "feature_count": X.shape[1],
                "cv_accuracy_mean": float(cv_scores.mean()),
                "cv_accuracy_std": float(cv_scores.std()),
                "training_accuracy": float(self.model.score(X, y)),
                "class_distribution": {
                    cat.value: int(np.sum(y == i))
                    for i, cat in enumerate(self.skill_categories)
                },
                "feature_importance": self._get_feature_importance(),
                "meets_accuracy_threshold": cv_scores.mean() >= ml_config.min_accuracy_threshold
            }
            
            # Mark as trained
            self.is_trained = True
            
            # Log performance
            performance_monitor.log_model_performance(
                model_name="WeaknessDetector",
                y_true=y,
                y_pred=y_pred
            )
            
            logger.info("Weakness detection model trained successfully",
                       cv_accuracy=f"{cv_scores.mean():.3f}±{cv_scores.std():.3f}",
                       meets_threshold=training_results["meets_accuracy_threshold"])
            
            return training_results
            
        except Exception as e:
            logger.error("Failed to train weakness detection model", error=str(e))
            raise
    
    def predict(self, matches: List[Match]) -> List[Dict[str, Any]]:
        """
        Predict weaknesses for given matches.
        
        Args:
            matches: Matches to analyze
            
        Returns:
            List of weakness predictions with confidence scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        try:
            logger.debug("Predicting weaknesses", matches=len(matches))
            
            # Extract features
            X = self.feature_pipeline.transform(matches)
            
            if X.shape[0] == 0:
                logger.warning("No features extracted for prediction")
                return []
            
            # Make predictions
            y_pred = self.model.predict(X)
            y_pred_proba = self.model.predict_proba(X)

            # Get the classes that the model was actually trained on
            trained_classes = self.model.classes_

            logger.debug("Prediction debug info",
                        y_pred=y_pred.tolist(),
                        trained_classes=trained_classes.tolist(),
                        n_classes=len(trained_classes),
                        skill_categories_count=len(self.skill_categories))

            predictions = []

            for i, match in enumerate(matches):
                if i >= len(y_pred):
                    break

                predicted_class_label = y_pred[i]  # This is the actual class label, not index
                confidence_scores = y_pred_proba[i]

                # Find the index of this class in trained_classes
                predicted_class_idx = np.where(trained_classes == predicted_class_label)[0][0]

                # Use the class label directly as the weakness index
                predicted_weakness = self.skill_categories[predicted_class_label].value
                prediction_confidence = float(confidence_scores[predicted_class_idx])
                
                # Get top 3 weaknesses with confidence scores
                top_weaknesses = []
                for j, score in enumerate(confidence_scores):
                    if score >= self.confidence_threshold:
                        # Use trained_classes[j] to get the actual class label
                        class_label = trained_classes[j]
                        weakness_name = self.skill_categories[class_label].value
                        top_weaknesses.append({
                            "category": weakness_name,
                            "confidence": float(score),
                            "severity": self._calculate_severity(score)
                        })
                
                # Sort by confidence
                top_weaknesses.sort(key=lambda x: x["confidence"], reverse=True)
                
                prediction = {
                    "match_id": str(match.id),
                    "primary_weakness": predicted_weakness,
                    "confidence": prediction_confidence,
                    "is_confident": prediction_confidence >= self.confidence_threshold,
                    "top_weaknesses": top_weaknesses[:3],  # Top 3 weaknesses
                    "analysis_summary": self._generate_analysis_summary(
                        predicted_weakness, prediction_confidence, top_weaknesses
                    )
                }
                
                predictions.append(prediction)
            
            logger.debug("Weakness predictions completed", predictions=len(predictions))
            
            return predictions
            
        except Exception as e:
            logger.error("Failed to predict weaknesses", error=str(e))
            raise
    
    def _calculate_severity(self, confidence: float) -> str:
        """Calculate weakness severity based on confidence score."""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _generate_analysis_summary(self, 
                                 primary_weakness: str, 
                                 confidence: float,
                                 top_weaknesses: List[Dict]) -> str:
        """Generate human-readable analysis summary."""
        if confidence < self.confidence_threshold:
            return f"Analysis shows mixed performance across skill areas. Consider focusing on fundamental mechanics."
        
        severity = self._calculate_severity(confidence)
        
        if len(top_weaknesses) == 1:
            return f"Primary weakness identified in {primary_weakness} with {severity} confidence. Focus training on this area."
        else:
            other_areas = [w["category"] for w in top_weaknesses[1:3]]
            return f"Primary weakness in {primary_weakness} ({severity} confidence). Also consider improving {', '.join(other_areas)}."
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores from the trained model."""
        if not hasattr(self.model, 'feature_importances_'):
            return {}
        
        try:
            importances = self.model.feature_importances_
            feature_names = self.feature_pipeline.final_features or []
            
            if len(importances) != len(feature_names):
                logger.warning("Feature importance length mismatch")
                return {}
            
            importance_dict = {
                name: float(importance)
                for name, importance in zip(feature_names, importances)
            }
            
            # Sort by importance
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            logger.error("Failed to get feature importance", error=str(e))
            return {}
    
    def analyze_player_weaknesses(self, matches: List[Match]) -> Dict[str, Any]:
        """
        Comprehensive weakness analysis for a player.
        
        Args:
            matches: Player's recent matches
            
        Returns:
            Detailed weakness analysis report
        """
        try:
            if not matches:
                return {"error": "No matches provided for analysis"}
            
            # Get predictions for all matches
            predictions = self.predict(matches)
            
            if not predictions:
                return {"error": "No predictions generated"}
            
            # Aggregate weakness analysis
            weakness_counts = {}
            confidence_scores = {}
            
            for pred in predictions:
                weakness = pred["primary_weakness"]
                confidence = pred["confidence"]
                
                if weakness not in weakness_counts:
                    weakness_counts[weakness] = 0
                    confidence_scores[weakness] = []
                
                weakness_counts[weakness] += 1
                confidence_scores[weakness].append(confidence)
            
            # Calculate average confidence per weakness
            weakness_analysis = {}
            for weakness, count in weakness_counts.items():
                avg_confidence = np.mean(confidence_scores[weakness])
                weakness_analysis[weakness] = {
                    "frequency": count,
                    "percentage": (count / len(predictions)) * 100,
                    "avg_confidence": float(avg_confidence),
                    "severity": self._calculate_severity(avg_confidence)
                }
            
            # Sort by frequency and confidence
            sorted_weaknesses = sorted(
                weakness_analysis.items(),
                key=lambda x: (x[1]["frequency"], x[1]["avg_confidence"]),
                reverse=True
            )
            
            analysis_report = {
                "total_matches_analyzed": len(matches),
                "confident_predictions": len([p for p in predictions if p["is_confident"]]),
                "primary_weaknesses": dict(sorted_weaknesses[:3]),  # Top 3
                "all_weaknesses": dict(sorted_weaknesses),
                "improvement_recommendations": self._generate_improvement_recommendations(sorted_weaknesses),
                "analysis_confidence": float(np.mean([p["confidence"] for p in predictions])),
                "feature_importance": self._get_feature_importance()
            }
            
            return analysis_report
            
        except Exception as e:
            logger.error("Failed to analyze player weaknesses", error=str(e))
            return {"error": str(e)}
    
    def _generate_improvement_recommendations(self, sorted_weaknesses: List[Tuple]) -> List[str]:
        """Generate actionable improvement recommendations."""
        if not sorted_weaknesses:
            return ["Continue practicing to gather more performance data."]

        recommendations = []

        # Focus on top weakness
        top_weakness = sorted_weaknesses[0]
        weakness_name = top_weakness[0]
        weakness_data = top_weakness[1]

        if weakness_data["avg_confidence"] >= 0.7:
            if weakness_name == "shooting":
                recommendations.append("Focus on shooting accuracy training packs and free play shooting drills.")
            elif weakness_name == "defending":
                recommendations.append("Practice save training packs and defensive positioning drills.")
            elif weakness_name == "boost_management":
                recommendations.append("Work on boost efficiency and collection route optimization.")
            elif weakness_name == "mechanical":
                recommendations.append("Focus on fundamental mechanics: ball control, car control, and consistency.")
            elif weakness_name == "positioning":
                recommendations.append("Study rotation patterns and practice positioning in different game scenarios.")
            elif weakness_name == "aerial_ability":
                recommendations.append("Practice aerial training packs and air roll control exercises.")
            elif weakness_name == "game_sense":
                recommendations.append("Focus on decision-making drills and game awareness exercises.")
            else:
                recommendations.append(f"Focus on improving {weakness_name} through targeted practice.")

        # Add secondary recommendations
        if len(sorted_weaknesses) > 1:
            secondary_weakness = sorted_weaknesses[1][0]
            recommendations.append(f"Secondary focus: work on {secondary_weakness} skills in practice sessions.")

        return recommendations

    def _prepare_features(self, matches: List[Match]) -> np.ndarray:
        """Prepare features for ML model (required by BaseMLModel)."""
        return self.feature_pipeline.transform(matches)

    def _prepare_targets(self, matches: List[Match]) -> np.ndarray:
        """Prepare target labels for ML model (required by BaseMLModel)."""
        return self._create_weakness_labels(matches)
