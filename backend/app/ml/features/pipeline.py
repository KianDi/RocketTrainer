"""
Feature Engineering Pipeline for RocketTrainer

Comprehensive pipeline that combines feature extraction, preprocessing,
and selection for ML model training and inference.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import structlog

from .extractor import FeatureExtractor
from .preprocessor import DataPreprocessor, create_skill_category_features
from .selector import FeatureSelector
from ..config import ml_config
from ..utils import data_validator, performance_monitor
from ...models.match import Match
from ...models.user import User

logger = structlog.get_logger(__name__)


class FeatureEngineeringPipeline:
    """Complete feature engineering pipeline for ML models."""
    
    def __init__(self,
                 use_feature_selection: bool = True,
                 scaler_type: str = "standard",
                 selection_method: str = "mutual_info",
                 k_features: Optional[int] = None):
        """
        Initialize the feature engineering pipeline.
        
        Args:
            use_feature_selection: Whether to apply feature selection
            scaler_type: Type of scaler for preprocessing
            selection_method: Method for feature selection
            k_features: Number of features to select
        """
        self.use_feature_selection = use_feature_selection
        self.scaler_type = scaler_type
        self.selection_method = selection_method
        self.k_features = k_features
        
        # Initialize components
        self.extractor = FeatureExtractor()
        self.preprocessor = DataPreprocessor(scaler_type=scaler_type)
        self.selector = FeatureSelector(
            method=selection_method,
            k_features=k_features
        ) if use_feature_selection else None
        
        # State tracking
        self.is_fitted = False
        self.feature_names: Optional[List[str]] = None
        self.final_features: Optional[List[str]] = None
        
        logger.info("FeatureEngineeringPipeline initialized",
                   use_feature_selection=use_feature_selection,
                   scaler_type=scaler_type,
                   selection_method=selection_method)
    
    def extract_features_from_matches(self, 
                                    matches: List[Match],
                                    user_id: Optional[str] = None) -> pd.DataFrame:
        """
        Extract features from a list of matches.
        
        Args:
            matches: List of Match objects
            user_id: Optional user ID for filtering
            
        Returns:
            DataFrame with extracted features
        """
        try:
            if not matches:
                logger.warning("No matches provided for feature extraction")
                return pd.DataFrame()
            
            # Filter matches by user if specified
            if user_id:
                matches = [m for m in matches if str(m.user_id) == str(user_id)]
            
            # Filter processed matches only
            processed_matches = [m for m in matches if m.processed]
            
            if not processed_matches:
                logger.warning("No processed matches found for feature extraction")
                return pd.DataFrame()
            
            logger.info("Extracting features from matches",
                       total_matches=len(matches),
                       processed_matches=len(processed_matches),
                       user_id=user_id)
            
            # Extract features using the extractor
            features_df = self.extractor.extract_player_features(processed_matches)
            
            if features_df.empty:
                logger.warning("No features extracted from matches")
                return pd.DataFrame()
            
            # Store feature names
            self.feature_names = [col for col in features_df.columns 
                                if col not in ['match_id', 'match_date']]
            
            logger.info("Feature extraction completed",
                       samples=len(features_df),
                       features=len(self.feature_names))
            
            return features_df
            
        except Exception as e:
            logger.error("Failed to extract features from matches", error=str(e))
            raise
    
    def fit(self, 
            matches: List[Match], 
            target_labels: Optional[np.ndarray] = None,
            user_id: Optional[str] = None) -> 'FeatureEngineeringPipeline':
        """
        Fit the pipeline on training data.
        
        Args:
            matches: Training matches
            target_labels: Target labels for supervised feature selection
            user_id: Optional user ID for filtering
        """
        try:
            logger.info("Fitting feature engineering pipeline")
            
            # Extract features
            features_df = self.extract_features_from_matches(matches, user_id)
            
            if features_df.empty:
                raise ValueError("No features extracted for pipeline fitting")
            
            # Prepare feature matrix (exclude metadata columns)
            X = features_df[self.feature_names]
            
            # Validate data
            is_valid, errors = data_validator.validate_player_data(X)
            if not is_valid:
                logger.warning("Data validation issues during fitting", errors=errors)
            
            # Fit preprocessor
            if target_labels is not None and self.use_feature_selection:
                # Fit with target for feature selection in preprocessing
                self.preprocessor.fit(X, target_labels)
            else:
                self.preprocessor.fit(X)
            
            # Apply preprocessing
            X_preprocessed = self.preprocessor.transform(X)
            X_preprocessed_df = pd.DataFrame(
                X_preprocessed, 
                columns=self.preprocessor.selected_features or self.feature_names,
                index=X.index
            )
            
            # Fit feature selector if enabled
            if self.selector and target_labels is not None:
                self.selector.fit(X_preprocessed_df, target_labels)
                self.final_features = self.selector.selected_features
            else:
                self.final_features = list(X_preprocessed_df.columns)
            
            self.is_fitted = True
            
            logger.info("Feature engineering pipeline fitted successfully",
                       original_features=len(self.feature_names),
                       final_features=len(self.final_features))
            
            return self
            
        except Exception as e:
            logger.error("Failed to fit feature engineering pipeline", error=str(e))
            raise
    
    def transform(self, matches: List[Match], user_id: Optional[str] = None) -> np.ndarray:
        """
        Transform matches into ML-ready feature matrix.
        
        Args:
            matches: Matches to transform
            user_id: Optional user ID for filtering
            
        Returns:
            Transformed feature matrix
        """
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before transforming")
        
        try:
            # Extract features
            features_df = self.extract_features_from_matches(matches, user_id)
            
            if features_df.empty:
                logger.warning("No features extracted for transformation")
                return np.array([]).reshape(0, len(self.final_features))
            
            # Prepare feature matrix
            X = features_df[self.feature_names]
            
            # Apply preprocessing
            X_preprocessed = self.preprocessor.transform(X)
            X_preprocessed_df = pd.DataFrame(
                X_preprocessed,
                columns=self.preprocessor.selected_features or self.feature_names,
                index=X.index
            )
            
            # Apply feature selection
            if self.selector:
                X_final_df = self.selector.transform(X_preprocessed_df)
                X_final = X_final_df.values
            else:
                X_final = X_preprocessed_df.values
            
            logger.debug("Feature transformation completed",
                        input_samples=len(matches),
                        output_shape=X_final.shape)
            
            return X_final
            
        except Exception as e:
            logger.error("Failed to transform features", error=str(e))
            raise
    
    def fit_transform(self, 
                     matches: List[Match],
                     target_labels: Optional[np.ndarray] = None,
                     user_id: Optional[str] = None) -> np.ndarray:
        """Fit pipeline and transform data in one step."""
        return self.fit(matches, target_labels, user_id).transform(matches, user_id)
    
    def create_feature_analysis_report(self, matches: List[Match]) -> Dict[str, Any]:
        """Create comprehensive feature analysis report."""
        try:
            # Extract raw features
            features_df = self.extract_features_from_matches(matches)
            
            if features_df.empty:
                return {"error": "No features extracted for analysis"}
            
            report = {
                "data_summary": {
                    "total_matches": len(matches),
                    "processed_matches": len([m for m in matches if m.processed]),
                    "feature_extraction_samples": len(features_df),
                    "extracted_features": len(self.feature_names) if self.feature_names else 0
                },
                "feature_statistics": {},
                "skill_category_analysis": {},
                "preprocessing_info": {},
                "selection_info": {}
            }
            
            # Feature statistics
            X = features_df[self.feature_names] if self.feature_names else features_df
            report["feature_statistics"] = self.preprocessor.create_feature_summary(X)
            
            # Skill category analysis
            skill_features = create_skill_category_features(X)
            report["skill_category_analysis"] = {
                category: {
                    "feature_count": len(df.columns),
                    "features": list(df.columns)
                }
                for category, df in skill_features.items()
                if not df.empty
            }
            
            # Preprocessing info
            if self.is_fitted:
                report["preprocessing_info"] = self.preprocessor.get_preprocessing_info()
                
                # Selection info
                if self.selector:
                    report["selection_info"] = self.selector.create_selection_report()
            
            return report
            
        except Exception as e:
            logger.error("Failed to create feature analysis report", error=str(e))
            return {"error": str(e)}
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get comprehensive pipeline information."""
        return {
            "configuration": {
                "use_feature_selection": self.use_feature_selection,
                "scaler_type": self.scaler_type,
                "selection_method": self.selection_method,
                "k_features": self.k_features
            },
            "state": {
                "is_fitted": self.is_fitted,
                "original_features": len(self.feature_names) if self.feature_names else 0,
                "final_features": len(self.final_features) if self.final_features else 0,
                "final_feature_names": self.final_features
            },
            "components": {
                "extractor": "FeatureExtractor",
                "preprocessor": f"DataPreprocessor({self.scaler_type})",
                "selector": f"FeatureSelector({self.selection_method})" if self.selector else None
            }
        }
