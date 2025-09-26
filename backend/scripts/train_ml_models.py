#!/usr/bin/env python3
"""
Train ML Models for RocketTrainer

This script trains the WeaknessDetector and SkillAnalyzer models
using synthetic data and saves them for use in the application.
"""

import sys
import os
import json
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.ml.training.model_trainer import ModelTrainer
from app.ml.training.synthetic_data_generator import SyntheticDataGenerator
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def main():
    """Train all ML models."""
    logger.info("Starting ML model training")
    
    try:
        # Initialize trainer
        trainer = ModelTrainer(use_synthetic_data=True)
        
        # Generate training data
        logger.info("Generating synthetic training data")
        features_df, labels_dict = trainer.prepare_training_data(
            num_players=1000,  # Generate data for 1000 players
            matches_per_player=30  # 30 matches per player
        )
        
        logger.info("Training data prepared",
                   total_samples=len(features_df),
                   unique_players=len(set(labels_dict["player_ids"])))
        
        # Train WeaknessDetector
        logger.info("Training WeaknessDetector model")
        weakness_results = trainer.train_weakness_detector(
            features_df, 
            labels_dict,
            optimize_hyperparams=False  # Set to True for better performance but longer training
        )
        
        logger.info("WeaknessDetector training completed",
                   train_accuracy=weakness_results["train_accuracy"],
                   test_accuracy=weakness_results["test_accuracy"])
        
        # Train SkillAnalyzer
        logger.info("Training SkillAnalyzer model")
        skill_results = trainer.train_skill_analyzer(
            features_df,
            labels_dict,
            optimize_hyperparams=False  # Set to True for better performance but longer training
        )
        
        logger.info("SkillAnalyzer training completed",
                   test_r2=skill_results["test_r2"],
                   overall_mse=skill_results["overall_mse"])
        
        # Save training summary
        training_summary = {
            "training_completed_at": weakness_results["trained_at"],
            "weakness_detector": {
                "model_path": weakness_results["model_path"],
                "train_accuracy": weakness_results["train_accuracy"],
                "test_accuracy": weakness_results["test_accuracy"],
                "cv_mean": weakness_results["cv_mean"],
                "cv_std": weakness_results["cv_std"],
                "num_classes": weakness_results["num_classes"],
                "class_names": weakness_results["class_names"]
            },
            "skill_analyzer": {
                "model_path": skill_results["model_path"],
                "test_r2": skill_results["test_r2"],
                "overall_mse": skill_results["overall_mse"],
                "num_skills": skill_results["num_skills"],
                "skill_categories": skill_results["skill_categories"]
            },
            "training_data": {
                "num_players": 1000,
                "matches_per_player": 30,
                "total_samples": len(features_df),
                "synthetic_data": True
            }
        }
        
        # Save summary
        summary_path = "/app/ml/trained_models/training_summary.json"
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, 'w') as f:
            json.dump(training_summary, f, indent=2)
        
        logger.info("Training completed successfully",
                   summary_path=summary_path,
                   weakness_accuracy=weakness_results["test_accuracy"],
                   skill_r2=skill_results["test_r2"])
        
        print("\n" + "="*60)
        print("🎉 ML MODEL TRAINING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"WeaknessDetector Accuracy: {weakness_results['test_accuracy']:.3f}")
        print(f"SkillAnalyzer R² Score: {skill_results['test_r2']:.3f}")
        print(f"Models saved to: {trainer.model_save_dir}")
        print(f"Training summary: {summary_path}")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error("Training failed", error=str(e), exc_info=True)
        print(f"\n❌ Training failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
