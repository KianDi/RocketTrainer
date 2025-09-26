"""
ML Model Trainer for RocketTrainer

Trains machine learning models using synthetic or real data.
Implements training pipelines for WeaknessDetector, SkillAnalyzer,
and TrainingRecommendationEngine models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
import pickle
import os
import structlog
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib

from .synthetic_data_generator import SyntheticDataGenerator
from ..features.pipeline import FeatureEngineeringPipeline
from ..config import ml_config
from ..utils import performance_monitor
from ...models.match import Match

logger = structlog.get_logger(__name__)


class ModelTrainer:
    """Trains ML models for RocketTrainer."""
    
    def __init__(self, 
                 model_save_dir: str = "/app/ml/trained_models",
                 use_synthetic_data: bool = True):
        """
        Initialize the model trainer.
        
        Args:
            model_save_dir: Directory to save trained models
            use_synthetic_data: Whether to use synthetic data for training
        """
        self.model_save_dir = model_save_dir
        self.use_synthetic_data = use_synthetic_data
        
        # Create save directory
        os.makedirs(model_save_dir, exist_ok=True)
        
        # Initialize components
        self.data_generator = SyntheticDataGenerator()
        self.feature_pipeline = FeatureEngineeringPipeline()
        self.label_encoder = LabelEncoder()
        
        # Model configurations
        self.model_configs = {
            "weakness_detector": {
                "model_class": RandomForestClassifier,
                "params": {
                    "n_estimators": 100,
                    "max_depth": 10,
                    "min_samples_split": 5,
                    "min_samples_leaf": 2,
                    "random_state": ml_config.random_state,
                    "n_jobs": -1
                },
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [5, 10, 15],
                    "min_samples_split": [2, 5, 10]
                }
            },
            "skill_analyzer": {
                "model_class": RandomForestRegressor,
                "params": {
                    "n_estimators": 100,
                    "max_depth": 12,
                    "min_samples_split": 5,
                    "min_samples_leaf": 2,
                    "random_state": ml_config.random_state,
                    "n_jobs": -1
                },
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [8, 12, 16],
                    "min_samples_split": [2, 5, 10]
                }
            }
        }
        
        logger.info("ModelTrainer initialized",
                   save_dir=model_save_dir,
                   use_synthetic=use_synthetic_data)
    
    def prepare_training_data(self, 
                            num_players: int = 1000,
                            matches_per_player: int = 30) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
        """Prepare training data (synthetic or real)."""
        if self.use_synthetic_data:
            logger.info("Generating synthetic training data")
            features_df, labels_dict = self.data_generator.create_training_dataset(
                num_players=num_players,
                matches_per_player=matches_per_player
            )
        else:
            # TODO: Implement real data loading when replay parsing is available
            logger.warning("Real data training not yet implemented, using synthetic data")
            features_df, labels_dict = self.data_generator.create_training_dataset(
                num_players=num_players,
                matches_per_player=matches_per_player
            )
        
        return features_df, labels_dict
    
    def train_weakness_detector(self, 
                              features_df: pd.DataFrame,
                              labels_dict: Dict[str, np.ndarray],
                              optimize_hyperparams: bool = False) -> Dict[str, Any]:
        """Train the weakness detection model."""
        logger.info("Training weakness detector model")
        
        # Convert match data to Match objects for feature pipeline
        matches = self._dataframe_to_matches(features_df)

        # Prepare labels first
        y = labels_dict["primary_weakness"]
        y_encoded = self.label_encoder.fit_transform(y)

        # Extract features using pipeline with target labels for feature selection
        X = self.feature_pipeline.fit_transform(matches, target_labels=y_encoded)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=ml_config.random_state, stratify=y_encoded
        )
        
        # Get model configuration
        config = self.model_configs["weakness_detector"]
        
        if optimize_hyperparams:
            # Hyperparameter optimization
            logger.info("Optimizing hyperparameters for weakness detector")
            grid_search = GridSearchCV(
                config["model_class"](),
                config["param_grid"],
                cv=5,
                scoring='accuracy',
                n_jobs=-1,
                verbose=1
            )
            grid_search.fit(X_train, y_train)
            model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            logger.info("Best parameters found", params=best_params)
        else:
            # Use default parameters
            model = config["model_class"](**config["params"])
            model.fit(X_train, y_train)
        
        # Evaluate model
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=5)
        
        # Predictions for detailed evaluation
        y_pred = model.predict(X_test)
        
        # Classification report
        class_names = self.label_encoder.classes_
        report = classification_report(y_test, y_pred, target_names=class_names, output_dict=True)
        
        # Feature importance
        feature_importance = dict(zip(
            self.feature_pipeline.final_features or [],
            model.feature_importances_
        ))
        
        # Save model and metadata
        model_path = os.path.join(self.model_save_dir, "weakness_detector.joblib")
        encoder_path = os.path.join(self.model_save_dir, "weakness_detector_encoder.joblib")
        pipeline_path = os.path.join(self.model_save_dir, "weakness_detector_pipeline.joblib")
        
        joblib.dump(model, model_path)
        joblib.dump(self.label_encoder, encoder_path)
        joblib.dump(self.feature_pipeline, pipeline_path)
        
        training_results = {
            "model_type": "weakness_detector",
            "train_accuracy": float(train_score),
            "test_accuracy": float(test_score),
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "classification_report": report,
            "feature_importance": feature_importance,
            "model_path": model_path,
            "encoder_path": encoder_path,
            "pipeline_path": pipeline_path,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "num_classes": len(class_names),
            "class_names": class_names.tolist(),
            "trained_at": datetime.now().isoformat()
        }
        
        logger.info("Weakness detector training completed",
                   train_accuracy=train_score,
                   test_accuracy=test_score,
                   cv_mean=cv_scores.mean())
        
        return training_results
    
    def train_skill_analyzer(self,
                           features_df: pd.DataFrame,
                           labels_dict: Dict[str, np.ndarray],
                           optimize_hyperparams: bool = False) -> Dict[str, Any]:
        """Train the skill analysis model."""
        logger.info("Training skill analyzer model")
        
        # Convert match data to Match objects for feature pipeline
        matches = self._dataframe_to_matches(features_df)
        
        # Extract features using pipeline (reuse fitted pipeline from weakness detector)
        if not self.feature_pipeline.is_fitted:
            X = self.feature_pipeline.fit_transform(matches)
        else:
            X = self.feature_pipeline.transform(matches)
        
        # Prepare labels (skill scores for all categories)
        y = labels_dict["skill_scores"]  # Shape: (n_samples, n_skill_categories)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=ml_config.random_state
        )
        
        # Get model configuration
        config = self.model_configs["skill_analyzer"]
        
        if optimize_hyperparams:
            # Hyperparameter optimization
            logger.info("Optimizing hyperparameters for skill analyzer")
            grid_search = GridSearchCV(
                config["model_class"](),
                config["param_grid"],
                cv=5,
                scoring='neg_mean_squared_error',
                n_jobs=-1,
                verbose=1
            )
            grid_search.fit(X_train, y_train)
            model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            logger.info("Best parameters found", params=best_params)
        else:
            # Use default parameters
            model = config["model_class"](**config["params"])
            model.fit(X_train, y_train)
        
        # Evaluate model
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        # Predictions for detailed evaluation
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Per-skill category performance
        skill_categories = self.data_generator.skill_categories
        skill_metrics = {}
        for i, skill in enumerate(skill_categories):
            skill_mse = mean_squared_error(y_test[:, i], y_pred[:, i])
            skill_r2 = r2_score(y_test[:, i], y_pred[:, i])
            skill_metrics[skill] = {
                "mse": float(skill_mse),
                "r2": float(skill_r2)
            }
        
        # Feature importance
        feature_importance = dict(zip(
            self.feature_pipeline.final_features or [],
            model.feature_importances_
        ))
        
        # Save model
        model_path = os.path.join(self.model_save_dir, "skill_analyzer.joblib")
        joblib.dump(model, model_path)
        
        training_results = {
            "model_type": "skill_analyzer",
            "train_r2": float(train_score),
            "test_r2": float(test_score),
            "overall_mse": float(mse),
            "overall_r2": float(r2),
            "skill_metrics": skill_metrics,
            "feature_importance": feature_importance,
            "model_path": model_path,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "num_skills": len(skill_categories),
            "skill_categories": skill_categories,
            "trained_at": datetime.now().isoformat()
        }
        
        logger.info("Skill analyzer training completed",
                   test_r2=test_score,
                   overall_mse=mse)
        
        return training_results
    
    def _dataframe_to_matches(self, df: pd.DataFrame) -> List[Match]:
        """Convert DataFrame to Match objects for feature pipeline."""
        matches = []

        for _, row in df.iterrows():
            # Create a mock Match object with the required attributes
            match = type('Match', (), {})()

            # Set basic attributes from DataFrame
            match.id = row.get('match_id', f"synthetic_{len(matches)}")
            match.user_id = row['user_id']
            match.goals = int(row['goals'])
            match.assists = int(row['assists'])
            match.saves = int(row['saves'])
            match.shots = int(row['shots'])
            match.score = int(row['score'])
            match.match_duration_minutes = float(row['match_duration_minutes'])
            match.is_win = bool(row['is_win'])
            match.result = row['result']
            match.match_date = row['match_date']
            match.playlist = row.get('playlist', 'ranked_2v2')
            match.processed = True

            # Add missing attributes that the feature extractor expects
            # Team scores (estimate based on result and individual performance)
            if match.result == 'win':
                match.score_team_0 = max(3, match.goals + 2)  # Winning team score
                match.score_team_1 = max(0, match.score_team_0 - 2)  # Losing team score
            elif match.result == 'loss':
                match.score_team_1 = max(3, 4)  # Opponent team score
                match.score_team_0 = max(0, match.score_team_1 - 2)  # Player's team score
            else:  # draw
                match.score_team_0 = 2
                match.score_team_1 = 2

            # Advanced stats (synthetic values based on skill levels if available)
            profile_data = row.get('_player_profile', {})
            skill_levels = row.get('_true_skills', {})

            # Boost usage (0-100, based on boost management skill)
            boost_skill = skill_levels.get('boost_management', 0.5)
            match.boost_usage = 50 + (boost_skill - 0.5) * 40  # 30-70 range

            # Speed (based on mechanical skill)
            mechanical_skill = skill_levels.get('mechanical', 0.5)
            match.average_speed = 800 + (mechanical_skill - 0.5) * 400  # 600-1000 range

            # Time distribution (based on aerial ability)
            aerial_skill = skill_levels.get('aerial_ability', 0.5)
            total_seconds = match.match_duration_minutes * 60

            # Higher aerial skill = more time in air
            air_time_ratio = 0.1 + aerial_skill * 0.3  # 10-40% in air
            ground_time_ratio = 1.0 - air_time_ratio

            match.time_on_ground = ground_time_ratio * total_seconds
            match.time_low_air = air_time_ratio * 0.7 * total_seconds  # 70% of air time is low
            match.time_high_air = air_time_ratio * 0.3 * total_seconds  # 30% of air time is high

            matches.append(match)

        return matches
