"""
Data Preprocessor for RocketTrainer ML Models

Preprocesses extracted features for machine learning models including
scaling, normalization, handling missing values, and feature selection.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
import structlog

from ..config import ml_config
from ..utils import data_validator

logger = structlog.get_logger(__name__)


class DataPreprocessor:
    """Preprocesses feature data for ML models."""
    
    def __init__(self, 
                 scaler_type: str = "standard",
                 imputation_strategy: str = "median",
                 feature_selection_k: Optional[int] = None):
        """
        Initialize the data preprocessor.
        
        Args:
            scaler_type: Type of scaler ('standard', 'minmax', 'robust')
            imputation_strategy: Strategy for missing values ('mean', 'median', 'most_frequent')
            feature_selection_k: Number of top features to select (None = no selection)
        """
        self.scaler_type = scaler_type
        self.imputation_strategy = imputation_strategy
        self.feature_selection_k = feature_selection_k
        
        # Initialize components
        self.scaler = self._create_scaler()
        self.imputer = SimpleImputer(strategy=imputation_strategy)
        self.feature_selector = None
        
        # State tracking
        self.is_fitted = False
        self.feature_names: Optional[List[str]] = None
        self.selected_features: Optional[List[str]] = None
        
        logger.info("DataPreprocessor initialized",
                   scaler_type=scaler_type,
                   imputation_strategy=imputation_strategy,
                   feature_selection_k=feature_selection_k)
    
    def _create_scaler(self):
        """Create the appropriate scaler based on configuration."""
        if self.scaler_type == "standard":
            return StandardScaler()
        elif self.scaler_type == "minmax":
            return MinMaxScaler()
        elif self.scaler_type == "robust":
            return RobustScaler()
        else:
            logger.warning("Unknown scaler type, using StandardScaler", 
                          scaler_type=self.scaler_type)
            return StandardScaler()
    
    def fit(self, X: pd.DataFrame, y: Optional[np.ndarray] = None) -> 'DataPreprocessor':
        """
        Fit the preprocessor on training data.
        
        Args:
            X: Feature matrix
            y: Target vector (optional, needed for feature selection)
        """
        try:
            logger.info("Fitting data preprocessor", 
                       samples=len(X), 
                       features=len(X.columns))
            
            # Validate input data
            is_valid, errors = data_validator.validate_player_data(X)
            if not is_valid:
                logger.warning("Data validation issues found", errors=errors)
            
            # Store feature names
            self.feature_names = list(X.columns)
            
            # Handle missing values
            X_imputed = self.imputer.fit_transform(X)
            X_imputed = pd.DataFrame(X_imputed, columns=X.columns, index=X.index)
            
            # Feature selection (if enabled and target provided)
            if self.feature_selection_k and y is not None:
                self.feature_selector = SelectKBest(
                    score_func=mutual_info_classif,
                    k=min(self.feature_selection_k, len(X.columns))
                )
                X_selected = self.feature_selector.fit_transform(X_imputed, y)
                
                # Get selected feature names
                selected_indices = self.feature_selector.get_support(indices=True)
                self.selected_features = [X.columns[i] for i in selected_indices]
                
                logger.info("Feature selection completed",
                           original_features=len(X.columns),
                           selected_features=len(self.selected_features))
                
                # Use selected features for scaling
                X_for_scaling = pd.DataFrame(X_selected, columns=self.selected_features, index=X.index)
            else:
                X_for_scaling = X_imputed
                self.selected_features = self.feature_names
            
            # Fit scaler
            self.scaler.fit(X_for_scaling)
            
            self.is_fitted = True
            
            logger.info("Data preprocessor fitted successfully",
                       final_features=len(self.selected_features))
            
            return self
            
        except Exception as e:
            logger.error("Failed to fit data preprocessor", error=str(e))
            raise
    
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transform data using fitted preprocessor.
        
        Args:
            X: Feature matrix to transform
            
        Returns:
            Transformed feature matrix
        """
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before transforming data")
        
        try:
            logger.debug("Transforming data", samples=len(X), features=len(X.columns))
            
            # Ensure we have the same features as training
            missing_features = set(self.feature_names) - set(X.columns)
            if missing_features:
                logger.warning("Missing features in transform data", 
                              missing_features=list(missing_features))
                # Add missing features with zeros
                for feature in missing_features:
                    X[feature] = 0.0
            
            # Reorder columns to match training
            X = X[self.feature_names]
            
            # Handle missing values
            X_imputed = self.imputer.transform(X)
            X_imputed = pd.DataFrame(X_imputed, columns=X.columns, index=X.index)
            
            # Apply feature selection if used
            if self.feature_selector is not None:
                X_selected = self.feature_selector.transform(X_imputed)
                X_for_scaling = pd.DataFrame(X_selected, columns=self.selected_features, index=X.index)
            else:
                X_for_scaling = X_imputed
            
            # Scale features
            X_scaled = self.scaler.transform(X_for_scaling)
            
            logger.debug("Data transformation completed", 
                        output_shape=X_scaled.shape)
            
            return X_scaled
            
        except Exception as e:
            logger.error("Failed to transform data", error=str(e))
            raise
    
    def fit_transform(self, X: pd.DataFrame, y: Optional[np.ndarray] = None) -> np.ndarray:
        """Fit the preprocessor and transform data in one step."""
        return self.fit(X, y).transform(X)
    
    def inverse_transform(self, X_scaled: np.ndarray) -> pd.DataFrame:
        """
        Inverse transform scaled data back to original scale.
        
        Args:
            X_scaled: Scaled feature matrix
            
        Returns:
            Data in original scale
        """
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before inverse transforming")
        
        try:
            # Inverse scale
            X_unscaled = self.scaler.inverse_transform(X_scaled)
            
            # Create DataFrame with appropriate column names
            feature_names = self.selected_features or self.feature_names
            df = pd.DataFrame(X_unscaled, columns=feature_names)
            
            logger.debug("Inverse transformation completed", shape=df.shape)
            
            return df
            
        except Exception as e:
            logger.error("Failed to inverse transform data", error=str(e))
            raise
    
    def get_feature_importance_weights(self) -> Optional[Dict[str, float]]:
        """Get feature importance weights from feature selection."""
        if self.feature_selector is None or not self.is_fitted:
            return None
        
        try:
            scores = self.feature_selector.scores_
            selected_indices = self.feature_selector.get_support(indices=True)
            
            importance_dict = {}
            for i, feature_idx in enumerate(selected_indices):
                feature_name = self.feature_names[feature_idx]
                importance_dict[feature_name] = float(scores[feature_idx])
            
            # Normalize to sum to 1
            total_score = sum(importance_dict.values())
            if total_score > 0:
                importance_dict = {k: v/total_score for k, v in importance_dict.items()}
            
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            logger.error("Failed to get feature importance", error=str(e))
            return None
    
    def get_preprocessing_info(self) -> Dict[str, Any]:
        """Get information about the preprocessing configuration."""
        return {
            "scaler_type": self.scaler_type,
            "imputation_strategy": self.imputation_strategy,
            "feature_selection_k": self.feature_selection_k,
            "is_fitted": self.is_fitted,
            "original_features": len(self.feature_names) if self.feature_names else 0,
            "selected_features": len(self.selected_features) if self.selected_features else 0,
            "selected_feature_names": self.selected_features
        }
    
    def create_feature_summary(self, X: pd.DataFrame) -> Dict[str, Any]:
        """Create a summary of feature statistics."""
        try:
            summary = {
                "shape": X.shape,
                "missing_values": X.isnull().sum().to_dict(),
                "feature_stats": {}
            }
            
            # Calculate statistics for numeric features
            numeric_features = X.select_dtypes(include=[np.number]).columns
            for feature in numeric_features:
                summary["feature_stats"][feature] = {
                    "mean": float(X[feature].mean()),
                    "std": float(X[feature].std()),
                    "min": float(X[feature].min()),
                    "max": float(X[feature].max()),
                    "missing_count": int(X[feature].isnull().sum())
                }
            
            return summary
            
        except Exception as e:
            logger.error("Failed to create feature summary", error=str(e))
            return {"error": str(e)}


def create_skill_category_features(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Group features by skill categories for specialized analysis.
    
    Args:
        df: Feature DataFrame
        
    Returns:
        Dictionary mapping skill categories to their relevant features
    """
    skill_features = {
        "mechanical": [],
        "positioning": [],
        "game_sense": [],
        "boost_management": [],
        "rotation": [],
        "aerial_ability": [],
        "shooting": [],
        "defending": []
    }
    
    # Map features to skill categories based on feature names
    for column in df.columns:
        if any(keyword in column.lower() for keyword in ['goal', 'shot', 'accuracy']):
            skill_features["shooting"].append(column)
            skill_features["mechanical"].append(column)
        elif any(keyword in column.lower() for keyword in ['save', 'defensive']):
            skill_features["defending"].append(column)
            skill_features["mechanical"].append(column)
        elif any(keyword in column.lower() for keyword in ['boost']):
            skill_features["boost_management"].append(column)
        elif any(keyword in column.lower() for keyword in ['aerial', 'air']):
            skill_features["aerial_ability"].append(column)
            skill_features["mechanical"].append(column)
        elif any(keyword in column.lower() for keyword in ['assist', 'contribution']):
            skill_features["game_sense"].append(column)
        elif any(keyword in column.lower() for keyword in ['speed', 'ground']):
            skill_features["positioning"].append(column)
    
    # Create DataFrames for each skill category
    result = {}
    for category, features in skill_features.items():
        if features:
            # Remove duplicates while preserving order
            unique_features = list(dict.fromkeys(features))
            result[category] = df[unique_features]
        else:
            result[category] = pd.DataFrame()
    
    return result
