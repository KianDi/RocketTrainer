"""
Feature Extractor for RocketTrainer ML Models

Extracts meaningful features from player match data for machine learning.
Converts raw gameplay statistics into feature vectors optimized for weakness detection.
"""

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import structlog

from ..config import ml_config, SkillCategory
from ...models.match import Match
from ...models.player_stats import PlayerStats, STAT_TYPES

logger = structlog.get_logger(__name__)


class FeatureExtractor:
    """Extracts ML features from player match data."""
    
    def __init__(self):
        self.feature_names: List[str] = []
        self.skill_categories = ml_config.skill_categories
        self.feature_window = ml_config.feature_window_size
        
        logger.info("FeatureExtractor initialized", 
                   feature_window=self.feature_window,
                   skill_categories=len(self.skill_categories))
    
    def extract_match_features(self, match: Match) -> Dict[str, float]:
        """Extract features from a single match."""
        features = {}
        
        # Basic performance features
        features.update(self._extract_basic_features(match))
        
        # Efficiency features
        features.update(self._extract_efficiency_features(match))
        
        # Contextual features
        features.update(self._extract_contextual_features(match))
        
        # Advanced features (if available)
        features.update(self._extract_advanced_features(match))
        
        logger.debug("Match features extracted", 
                    match_id=str(match.id),
                    feature_count=len(features))
        
        return features
    
    def _extract_basic_features(self, match: Match) -> Dict[str, float]:
        """Extract basic gameplay statistics."""
        return {
            # Core stats
            'goals': float(match.goals),
            'assists': float(match.assists),
            'saves': float(match.saves),
            'shots': float(match.shots),
            'score': float(match.score),
            
            # Derived stats
            'goals_per_minute': float(match.goals) / max(match.match_duration_minutes, 1),
            'shots_per_minute': float(match.shots) / max(match.match_duration_minutes, 1),
            'saves_per_minute': float(match.saves) / max(match.match_duration_minutes, 1),
            
            # Match context
            'match_duration_minutes': match.match_duration_minutes,
            'is_win': 1.0 if match.is_win else 0.0,
            'is_loss': 1.0 if match.result == 'loss' else 0.0,
            'is_draw': 1.0 if match.result == 'draw' else 0.0,
        }
    
    def _extract_efficiency_features(self, match: Match) -> Dict[str, float]:
        """Extract efficiency and accuracy features."""
        features = {}
        
        # Shot accuracy
        if match.shots > 0:
            features['shot_accuracy'] = float(match.goals) / float(match.shots)
        else:
            features['shot_accuracy'] = 0.0
        
        # Contribution ratio (goals + assists vs total team score)
        team_score = match.score_team_0 if match.result != 'loss' else match.score_team_1
        if team_score > 0:
            features['contribution_ratio'] = float(match.goals + match.assists) / float(team_score)
        else:
            features['contribution_ratio'] = 0.0
        
        # Score efficiency (score per minute)
        features['score_efficiency'] = float(match.score) / max(match.match_duration_minutes, 1)
        
        # Defensive contribution
        features['defensive_contribution'] = float(match.saves) / max(match.match_duration_minutes, 1)
        
        return features
    
    def _extract_contextual_features(self, match: Match) -> Dict[str, float]:
        """Extract contextual features based on playlist and match type."""
        features = {}
        
        # Playlist encoding (one-hot)
        playlists = ['Ranked Duels', 'Ranked Doubles', 'Ranked Standard', 'Casual']
        for playlist in playlists:
            features[f'playlist_{playlist.lower().replace(" ", "_")}'] = (
                1.0 if match.playlist == playlist else 0.0
            )
        
        # Match length category
        if match.match_duration_minutes <= 4:
            features['match_length_short'] = 1.0
            features['match_length_normal'] = 0.0
            features['match_length_long'] = 0.0
        elif match.match_duration_minutes <= 7:
            features['match_length_short'] = 0.0
            features['match_length_normal'] = 1.0
            features['match_length_long'] = 0.0
        else:
            features['match_length_short'] = 0.0
            features['match_length_normal'] = 0.0
            features['match_length_long'] = 1.0
        
        # Score differential
        score_diff = abs(match.score_team_0 - match.score_team_1)
        features['score_differential'] = float(score_diff)
        features['close_match'] = 1.0 if score_diff <= 1 else 0.0
        
        return features
    
    def _extract_advanced_features(self, match: Match) -> Dict[str, float]:
        """Extract advanced features if available."""
        features = {}
        
        # Boost usage features
        if match.boost_usage is not None:
            features['boost_usage'] = float(match.boost_usage)
            features['boost_efficiency'] = float(match.score) / max(match.boost_usage, 1)
        else:
            features['boost_usage'] = 0.0
            features['boost_efficiency'] = 0.0
        
        # Speed and positioning features
        if match.average_speed is not None:
            features['average_speed'] = float(match.average_speed)
        else:
            features['average_speed'] = 0.0
        
        # Time distribution features
        if match.time_on_ground is not None:
            features['time_on_ground'] = float(match.time_on_ground)
        else:
            features['time_on_ground'] = 0.0
            
        if match.time_low_air is not None:
            features['time_low_air'] = float(match.time_low_air)
        else:
            features['time_low_air'] = 0.0
            
        if match.time_high_air is not None:
            features['time_high_air'] = float(match.time_high_air)
            features['aerial_tendency'] = float(match.time_high_air) / max(match.match_duration_minutes * 60, 1)
        else:
            features['time_high_air'] = 0.0
            features['aerial_tendency'] = 0.0
        
        return features
    
    def extract_player_features(self, matches: List[Match]) -> pd.DataFrame:
        """Extract features from multiple matches for a player."""
        if not matches:
            logger.warning("No matches provided for feature extraction")
            return pd.DataFrame()
        
        # Extract features from each match
        feature_list = []
        for match in matches:
            match_features = self.extract_match_features(match)
            match_features['match_id'] = str(match.id)
            match_features['match_date'] = match.match_date
            feature_list.append(match_features)
        
        # Convert to DataFrame
        df = pd.DataFrame(feature_list)
        
        # Sort by match date
        df = df.sort_values('match_date')
        
        # Add rolling statistics
        df = self._add_rolling_features(df)
        
        # Add trend features
        df = self._add_trend_features(df)
        
        logger.info("Player features extracted", 
                   match_count=len(matches),
                   feature_count=len(df.columns))
        
        return df
    
    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling window statistics."""
        window_size = min(self.feature_window, len(df))
        
        # Core stats rolling averages
        core_stats = ['goals', 'assists', 'saves', 'shots', 'score']
        for stat in core_stats:
            if stat in df.columns:
                df[f'{stat}_avg_{window_size}'] = df[stat].rolling(window=window_size, min_periods=1).mean()
                df[f'{stat}_std_{window_size}'] = df[stat].rolling(window=window_size, min_periods=1).std().fillna(0)
        
        # Efficiency rolling averages
        efficiency_stats = ['shot_accuracy', 'score_efficiency', 'contribution_ratio']
        for stat in efficiency_stats:
            if stat in df.columns:
                df[f'{stat}_avg_{window_size}'] = df[stat].rolling(window=window_size, min_periods=1).mean()
        
        return df
    
    def _add_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend and improvement features."""
        if len(df) < 2:
            return df
        
        # Calculate trends for key metrics
        trend_stats = ['goals', 'assists', 'saves', 'score', 'shot_accuracy']
        
        for stat in trend_stats:
            if stat in df.columns:
                # Simple linear trend (slope)
                df[f'{stat}_trend'] = df[stat].diff().rolling(window=3, min_periods=1).mean().fillna(0)
                
                # Recent vs historical performance
                if len(df) >= 5:
                    recent_avg = df[stat].tail(3).mean()
                    historical_avg = df[stat].head(-3).mean() if len(df) > 3 else recent_avg
                    df[f'{stat}_recent_vs_historical'] = recent_avg - historical_avg
                else:
                    df[f'{stat}_recent_vs_historical'] = 0.0
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """Get list of all possible feature names."""
        if not self.feature_names:
            # Generate feature names based on extraction methods
            sample_features = self._get_sample_features()
            self.feature_names = list(sample_features.keys())
        
        return self.feature_names
    
    def _get_sample_features(self) -> Dict[str, float]:
        """Generate sample features to determine feature names."""
        # Create a mock match for feature name generation
        from ...models.match import Match
        from datetime import datetime
        
        mock_match = Match(
            playlist="Ranked Doubles",
            duration=300,
            match_date=datetime.now(),
            score_team_0=3,
            score_team_1=2,
            result="win",
            goals=1,
            assists=1,
            saves=2,
            shots=3,
            score=350
        )
        
        return self.extract_match_features(mock_match)
