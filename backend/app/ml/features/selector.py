"""
Feature Selector for RocketTrainer ML Models

Advanced feature selection methods for identifying the most relevant
features for weakness detection and training recommendations.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from sklearn.feature_selection import (
    SelectKBest, SelectPercentile, RFE, RFECV,
    f_classif, mutual_info_classif, chi2
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import structlog

from ..config import ml_config, SkillCategory
from ..utils import data_validator

logger = structlog.get_logger(__name__)


class FeatureSelector:
    """Advanced feature selection for ML models."""
    
    def __init__(self, 
                 method: str = "mutual_info",
                 k_features: Optional[int] = None,
                 percentile: float = 50.0):
        """
        Initialize feature selector.
        
        Args:
            method: Selection method ('mutual_info', 'f_classif', 'rfe', 'rfecv')
            k_features: Number of features to select (None = auto)
            percentile: Percentile of features to keep (for percentile-based selection)
        """
        self.method = method
        self.k_features = k_features
        self.percentile = percentile
        
        self.selector = None
        self.is_fitted = False
        self.feature_names: Optional[List[str]] = None
        self.selected_features: Optional[List[str]] = None
        self.feature_scores: Optional[Dict[str, float]] = None
        
        logger.info("FeatureSelector initialized",
                   method=method,
                   k_features=k_features,
                   percentile=percentile)
    
    def fit(self, X: pd.DataFrame, y: np.ndarray) -> 'FeatureSelector':
        """
        Fit the feature selector on training data.
        
        Args:
            X: Feature matrix
            y: Target vector
        """
        try:
            logger.info("Fitting feature selector",
                       samples=len(X),
                       features=len(X.columns),
                       method=self.method)
            
            # Validate input data
            is_valid, errors = data_validator.validate_feature_matrix(X.values, y)
            if not is_valid:
                logger.warning("Feature matrix validation issues", errors=errors)
            
            self.feature_names = list(X.columns)
            
            # Create selector based on method
            self.selector = self._create_selector(X, y)
            
            # Fit selector
            self.selector.fit(X, y)
            
            # Get selected features
            if hasattr(self.selector, 'get_support'):
                selected_mask = self.selector.get_support()
                self.selected_features = [
                    feature for feature, selected in zip(self.feature_names, selected_mask)
                    if selected
                ]
            else:
                self.selected_features = self.feature_names
            
            # Get feature scores
            self.feature_scores = self._get_feature_scores()
            
            self.is_fitted = True
            
            logger.info("Feature selector fitted successfully",
                       selected_features=len(self.selected_features),
                       selection_ratio=len(self.selected_features) / len(self.feature_names))
            
            return self
            
        except Exception as e:
            logger.error("Failed to fit feature selector", error=str(e))
            raise
    
    def _create_selector(self, X: pd.DataFrame, y: np.ndarray):
        """Create the appropriate selector based on method."""
        n_features = len(X.columns)
        k = self.k_features or min(20, max(5, n_features // 2))
        
        if self.method == "mutual_info":
            return SelectKBest(score_func=mutual_info_classif, k=k)
        
        elif self.method == "f_classif":
            return SelectKBest(score_func=f_classif, k=k)
        
        elif self.method == "percentile":
            return SelectPercentile(score_func=mutual_info_classif, percentile=self.percentile)
        
        elif self.method == "rfe":
            estimator = RandomForestClassifier(
                n_estimators=50,
                random_state=ml_config.random_state,
                n_jobs=-1
            )
            return RFE(estimator=estimator, n_features_to_select=k)
        
        elif self.method == "rfecv":
            estimator = LogisticRegression(
                random_state=ml_config.random_state,
                max_iter=1000
            )
            return RFECV(
                estimator=estimator,
                step=1,
                cv=3,
                scoring='accuracy',
                min_features_to_select=max(3, k // 4)
            )
        
        else:
            logger.warning("Unknown selection method, using mutual_info", method=self.method)
            return SelectKBest(score_func=mutual_info_classif, k=k)
    
    def _get_feature_scores(self) -> Dict[str, float]:
        """Extract feature scores from the fitted selector."""
        if not self.selector or not self.feature_names:
            return {}
        
        try:
            scores_dict = {}
            
            if hasattr(self.selector, 'scores_'):
                # For SelectKBest and SelectPercentile
                scores = self.selector.scores_
                for feature, score in zip(self.feature_names, scores):
                    scores_dict[feature] = float(score)
            
            elif hasattr(self.selector, 'ranking_'):
                # For RFE and RFECV (lower rank = better)
                rankings = self.selector.ranking_
                max_rank = max(rankings)
                for feature, rank in zip(self.feature_names, rankings):
                    # Convert rank to score (higher = better)
                    scores_dict[feature] = float(max_rank - rank + 1)
            
            elif hasattr(self.selector, 'estimator_') and hasattr(self.selector.estimator_, 'feature_importances_'):
                # For tree-based estimators
                importances = self.selector.estimator_.feature_importances_
                selected_mask = self.selector.get_support()
                
                for i, (feature, selected) in enumerate(zip(self.feature_names, selected_mask)):
                    if selected:
                        # Find the index in the selected features
                        selected_idx = np.where(selected_mask[:i+1])[0][-1] if selected else 0
                        scores_dict[feature] = float(importances[selected_idx])
                    else:
                        scores_dict[feature] = 0.0
            
            # Sort by score (descending)
            return dict(sorted(scores_dict.items(), key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            logger.error("Failed to extract feature scores", error=str(e))
            return {}
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform data by selecting features."""
        if not self.is_fitted:
            raise ValueError("FeatureSelector must be fitted before transforming")
        
        try:
            # Ensure we have the expected features
            missing_features = set(self.feature_names) - set(X.columns)
            if missing_features:
                logger.warning("Missing features in transform data",
                              missing_features=list(missing_features))
                for feature in missing_features:
                    X[feature] = 0.0
            
            # Reorder to match training
            X_ordered = X[self.feature_names]
            
            # Apply selection
            if hasattr(self.selector, 'transform'):
                X_selected = self.selector.transform(X_ordered)
                return pd.DataFrame(X_selected, columns=self.selected_features, index=X.index)
            else:
                return X_ordered[self.selected_features]
                
        except Exception as e:
            logger.error("Failed to transform features", error=str(e))
            raise
    
    def fit_transform(self, X: pd.DataFrame, y: np.ndarray) -> pd.DataFrame:
        """Fit selector and transform data in one step."""
        return self.fit(X, y).transform(X)
    
    def get_feature_ranking(self) -> List[Tuple[str, float]]:
        """Get features ranked by importance/score."""
        if not self.feature_scores:
            return []
        
        return [(feature, score) for feature, score in self.feature_scores.items()]
    
    def get_selected_features_by_category(self) -> Dict[str, List[str]]:
        """Group selected features by skill category."""
        if not self.selected_features:
            return {}
        
        categories = {
            "mechanical": [],
            "positioning": [],
            "game_sense": [],
            "boost_management": [],
            "aerial_ability": [],
            "shooting": [],
            "defending": []
        }
        
        for feature in self.selected_features:
            feature_lower = feature.lower()
            
            # Categorize based on feature name patterns
            if any(keyword in feature_lower for keyword in ['goal', 'shot', 'accuracy']):
                categories["shooting"].append(feature)
                categories["mechanical"].append(feature)
            elif any(keyword in feature_lower for keyword in ['save', 'defensive']):
                categories["defending"].append(feature)
                categories["mechanical"].append(feature)
            elif any(keyword in feature_lower for keyword in ['boost']):
                categories["boost_management"].append(feature)
            elif any(keyword in feature_lower for keyword in ['aerial', 'air']):
                categories["aerial_ability"].append(feature)
                categories["mechanical"].append(feature)
            elif any(keyword in feature_lower for keyword in ['assist', 'contribution']):
                categories["game_sense"].append(feature)
            elif any(keyword in feature_lower for keyword in ['speed', 'ground', 'position']):
                categories["positioning"].append(feature)
            else:
                # Default to game_sense for uncategorized features
                categories["game_sense"].append(feature)
        
        # Remove duplicates while preserving order
        for category in categories:
            categories[category] = list(dict.fromkeys(categories[category]))
        
        return categories
    
    def create_selection_report(self) -> Dict[str, Any]:
        """Create a comprehensive feature selection report."""
        if not self.is_fitted:
            return {"error": "FeatureSelector not fitted"}
        
        try:
            report = {
                "method": self.method,
                "total_features": len(self.feature_names) if self.feature_names else 0,
                "selected_features": len(self.selected_features) if self.selected_features else 0,
                "selection_ratio": (
                    len(self.selected_features) / len(self.feature_names)
                    if self.feature_names and self.selected_features else 0
                ),
                "top_features": self.get_feature_ranking()[:10],  # Top 10
                "features_by_category": self.get_selected_features_by_category(),
                "selection_summary": {
                    "mechanical_features": 0,
                    "positioning_features": 0,
                    "game_sense_features": 0,
                    "other_features": 0
                }
            }
            
            # Count features by category
            categories = report["features_by_category"]
            for category, features in categories.items():
                if category in ["mechanical", "positioning", "game_sense"]:
                    report["selection_summary"][f"{category}_features"] = len(features)
                else:
                    report["selection_summary"]["other_features"] += len(features)
            
            return report
            
        except Exception as e:
            logger.error("Failed to create selection report", error=str(e))
            return {"error": str(e)}
