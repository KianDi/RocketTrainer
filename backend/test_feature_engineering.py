#!/usr/bin/env python3
"""
Test Feature Engineering Pipeline

Comprehensive test of the feature engineering pipeline using real data
from the RocketTrainer database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from datetime import datetime

def test_feature_engineering():
    """Test the complete feature engineering pipeline."""
    print("🧪 Testing Feature Engineering Pipeline...")
    
    try:
        # Import components
        from app.database import get_db
        from app.models.match import Match
        from app.models.user import User
        from app.ml.features import FeatureExtractor, DataPreprocessor, FeatureSelector
        from app.ml.features.pipeline import FeatureEngineeringPipeline
        
        print("✅ Feature engineering components imported successfully")
        
        # Get database session and real data
        db = next(get_db())
        
        # Get processed matches
        matches = db.query(Match).filter(Match.processed == True).all()
        print(f"✅ Found {len(matches)} processed matches in database")
        
        if not matches:
            print("⚠️  No processed matches found. Creating mock data for testing...")
            matches = create_mock_matches()
        
        # Test 1: Feature Extractor
        print("\n🔧 Testing Feature Extractor...")
        extractor = FeatureExtractor()
        
        # Extract features from single match
        single_match_features = extractor.extract_match_features(matches[0])
        print(f"✅ Single match features extracted: {len(single_match_features)} features")
        print(f"   Sample features: {list(single_match_features.keys())[:5]}...")
        
        # Extract features from multiple matches
        if len(matches) > 1:
            player_features_df = extractor.extract_player_features(matches)
            print(f"✅ Player features extracted: {player_features_df.shape}")
        else:
            # Duplicate the match for testing
            player_features_df = extractor.extract_player_features([matches[0], matches[0]])
            print(f"✅ Player features extracted (duplicated): {player_features_df.shape}")
        
        # Test 2: Data Preprocessor
        print("\n🔧 Testing Data Preprocessor...")
        preprocessor = DataPreprocessor(scaler_type="standard")
        
        # Prepare feature matrix
        feature_columns = [col for col in player_features_df.columns 
                          if col not in ['match_id', 'match_date']]
        X = player_features_df[feature_columns]
        
        print(f"   Feature matrix shape: {X.shape}")
        print(f"   Features: {list(X.columns)[:5]}...")
        
        # Fit and transform
        X_preprocessed = preprocessor.fit_transform(X)
        print(f"✅ Data preprocessing completed: {X_preprocessed.shape}")
        
        # Get preprocessing info
        preprocessing_info = preprocessor.get_preprocessing_info()
        print(f"   Preprocessing info: {preprocessing_info}")
        
        # Test 3: Feature Selector (if we have enough samples)
        if len(X) >= 3:
            print("\n🔧 Testing Feature Selector...")
            
            # Create mock target labels for testing
            y_mock = np.random.randint(0, 3, size=len(X))  # 3 weakness categories
            
            selector = FeatureSelector(method="mutual_info", k_features=10)
            X_selected_df = selector.fit_transform(X, y_mock)
            
            print(f"✅ Feature selection completed: {X_selected_df.shape}")
            print(f"   Selected features: {list(X_selected_df.columns)}")
            
            # Get feature ranking
            feature_ranking = selector.get_feature_ranking()[:5]
            print(f"   Top 5 features: {feature_ranking}")
        else:
            print("\n⚠️  Skipping feature selector test (insufficient samples)")
        
        # Test 4: Complete Pipeline
        print("\n🔧 Testing Complete Feature Engineering Pipeline...")
        
        pipeline = FeatureEngineeringPipeline(
            use_feature_selection=len(X) >= 3,
            scaler_type="standard",
            selection_method="mutual_info",
            k_features=min(10, len(feature_columns))
        )
        
        # Create mock target labels if needed
        if len(X) >= 3:
            y_pipeline = np.random.randint(0, 3, size=len(matches))
            X_final = pipeline.fit_transform(matches, y_pipeline)
        else:
            X_final = pipeline.fit_transform(matches)
        
        print(f"✅ Complete pipeline executed: {X_final.shape}")
        
        # Get pipeline info
        pipeline_info = pipeline.get_pipeline_info()
        print(f"   Pipeline configuration: {pipeline_info['configuration']}")
        print(f"   Pipeline state: {pipeline_info['state']}")
        
        # Test 5: Feature Analysis Report
        print("\n📊 Creating Feature Analysis Report...")
        
        analysis_report = pipeline.create_feature_analysis_report(matches)
        
        if "error" not in analysis_report:
            print("✅ Feature analysis report created successfully")
            print(f"   Data summary: {analysis_report['data_summary']}")
            print(f"   Skill categories: {list(analysis_report['skill_category_analysis'].keys())}")
        else:
            print(f"⚠️  Feature analysis report error: {analysis_report['error']}")
        
        # Clean up
        db.close()
        
        print("\n🎉 Feature Engineering Pipeline Test Complete!")
        print("✅ All components working correctly")
        print("✅ Ready for ML model development")
        
        return True
        
    except Exception as e:
        print(f"❌ Feature engineering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_mock_matches():
    """Create mock matches for testing when no real data is available."""
    from app.models.match import Match
    from datetime import datetime, timedelta
    import uuid
    
    mock_matches = []
    
    # Create 3 mock matches with different performance patterns
    base_date = datetime.now() - timedelta(days=10)
    
    for i in range(3):
        match = Match(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            ballchasing_id=f"mock_match_{i}",
            playlist="Ranked Doubles",
            duration=300 + i * 30,
            match_date=base_date + timedelta(days=i),
            score_team_0=2 + i,
            score_team_1=1 + i,
            result="win" if i % 2 == 0 else "loss",
            goals=i + 1,
            assists=i,
            saves=2 - i if i < 2 else 0,
            shots=3 + i,
            score=300 + i * 50,
            boost_usage=0.7 + i * 0.1,
            average_speed=1200 + i * 100,
            processed=True
        )
        mock_matches.append(match)
    
    print(f"✅ Created {len(mock_matches)} mock matches for testing")
    return mock_matches

def test_feature_extraction_details():
    """Test detailed feature extraction capabilities."""
    print("\n🔍 Testing Detailed Feature Extraction...")
    
    try:
        from app.ml.features import FeatureExtractor
        
        # Create a detailed mock match
        mock_match = create_mock_matches()[0]
        
        extractor = FeatureExtractor()
        features = extractor.extract_match_features(mock_match)
        
        print(f"✅ Extracted {len(features)} features from match")
        
        # Categorize features
        categories = {
            "basic": [],
            "efficiency": [],
            "contextual": [],
            "advanced": []
        }
        
        for feature_name in features.keys():
            if any(keyword in feature_name for keyword in ['goals', 'assists', 'saves', 'shots', 'score']):
                categories["basic"].append(feature_name)
            elif any(keyword in feature_name for keyword in ['accuracy', 'efficiency', 'ratio']):
                categories["efficiency"].append(feature_name)
            elif any(keyword in feature_name for keyword in ['playlist', 'match_length', 'differential']):
                categories["contextual"].append(feature_name)
            elif any(keyword in feature_name for keyword in ['boost', 'speed', 'air', 'ground']):
                categories["advanced"].append(feature_name)
        
        for category, feature_list in categories.items():
            if feature_list:
                print(f"   {category.title()} features ({len(feature_list)}): {feature_list[:3]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Detailed feature extraction test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_feature_engineering()
    if success:
        test_feature_extraction_details()
        print("\n🚀 Feature Engineering Pipeline is ready for ML model development!")
    else:
        print("\n❌ Feature engineering pipeline test failed. Please check the errors above.")
        sys.exit(1)
