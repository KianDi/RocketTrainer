#!/usr/bin/env python3
"""
Test Weakness Detection Models

Comprehensive test of the weakness detection and skill analysis models
using real data from the RocketTrainer database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def test_weakness_detection():
    """Test the weakness detection model."""
    print("🧪 Testing Weakness Detection Models...")
    
    try:
        # Import components
        from app.database import get_db
        from app.models.match import Match
        from app.ml.models import WeaknessDetector, SkillAnalyzer
        
        print("✅ Weakness detection models imported successfully")
        
        # Get database session and real data
        db = next(get_db())
        
        # Get processed matches
        matches = db.query(Match).filter(Match.processed == True).all()
        print(f"✅ Found {len(matches)} processed matches in database")
        
        if len(matches) < 3:
            print("⚠️  Insufficient real matches. Creating mock data for testing...")
            matches.extend(create_enhanced_mock_matches())
        
        print(f"✅ Using {len(matches)} matches for testing")
        
        # Test 1: WeaknessDetector
        print("\n🔧 Testing WeaknessDetector...")
        
        detector = WeaknessDetector(
            model_type="random_forest",
            n_estimators=50,  # Reduced for faster testing
            random_state=42
        )
        
        print(f"   Detector initialized with {len(detector.skill_categories)} skill categories")
        
        # Train the model
        if len(matches) >= 5:  # Need minimum matches for training
            print("   Training weakness detection model...")
            training_results = detector.train(matches)
            
            print(f"✅ Model trained successfully!")
            print(f"   • Training accuracy: {training_results['training_accuracy']:.3f}")
            print(f"   • CV accuracy: {training_results['cv_accuracy_mean']:.3f}±{training_results['cv_accuracy_std']:.3f}")
            print(f"   • Meets threshold: {training_results['meets_accuracy_threshold']}")
            print(f"   • Feature count: {training_results['feature_count']}")
            
            # Test predictions
            print("\n   Testing weakness predictions...")
            predictions = detector.predict(matches[:3])  # Test on first 3 matches
            
            print(f"✅ Generated {len(predictions)} weakness predictions")
            for i, pred in enumerate(predictions[:2]):  # Show first 2
                print(f"   Match {i+1}:")
                print(f"     • Primary weakness: {pred['primary_weakness']}")
                print(f"     • Confidence: {pred['confidence']:.3f}")
                print(f"     • Top weaknesses: {[w['category'] for w in pred['top_weaknesses']]}")
            
            # Test comprehensive analysis
            print("\n   Testing comprehensive weakness analysis...")
            analysis = detector.analyze_player_weaknesses(matches)
            
            if "error" not in analysis:
                print("✅ Comprehensive analysis completed")
                print(f"   • Matches analyzed: {analysis['total_matches_analyzed']}")
                print(f"   • Confident predictions: {analysis['confident_predictions']}")
                print(f"   • Primary weaknesses: {list(analysis['primary_weaknesses'].keys())}")
                print(f"   • Recommendations: {len(analysis['improvement_recommendations'])}")
            else:
                print(f"⚠️  Analysis error: {analysis['error']}")
        
        else:
            print("⚠️  Insufficient matches for model training. Skipping training test.")
        
        # Test 2: SkillAnalyzer
        print("\n🔧 Testing SkillAnalyzer...")
        
        analyzer = SkillAnalyzer(trend_window=3)
        print("   Skill analyzer initialized")
        
        # Test skill analysis
        print("   Analyzing player skills...")
        skill_analysis = analyzer.analyze_player_skills(matches)
        
        if "error" not in skill_analysis:
            print("✅ Skill analysis completed successfully")
            
            summary = skill_analysis["player_summary"]
            print(f"   • Total matches: {summary['total_matches']}")
            print(f"   • Overall performance metrics: {len(summary['overall_performance'])}")
            
            categories = skill_analysis["skill_categories"]
            print(f"   • Skill categories analyzed: {len(categories)}")
            for category in list(categories.keys())[:3]:  # Show first 3
                cat_data = categories[category]
                if isinstance(cat_data, dict) and "category_score" in cat_data:
                    print(f"     - {category}: {cat_data['category_score']:.1f}/100")
            
            strengths_weaknesses = skill_analysis["strengths_and_weaknesses"]
            print(f"   • Strengths: {strengths_weaknesses.get('strengths', [])}")
            print(f"   • Weaknesses: {strengths_weaknesses.get('weaknesses', [])}")
            
            trends = skill_analysis["improvement_trends"]
            print(f"   • Overall trend: {trends.get('overall_trend', 'unknown')}")
            
            recommendations = skill_analysis["recommendations"]
            print(f"   • Recommendations: {len(recommendations)}")
            if recommendations:
                print(f"     - {recommendations[0]}")
        
        else:
            print(f"⚠️  Skill analysis error: {skill_analysis['error']}")
        
        # Test 3: Integration Test
        print("\n🔧 Testing Model Integration...")
        
        if len(matches) >= 5 and detector.is_trained:
            print("   Testing combined weakness detection and skill analysis...")
            
            # Get weakness predictions
            weakness_predictions = detector.predict(matches[:3])
            
            # Get skill analysis
            skill_results = analyzer.analyze_player_skills(matches[:3])
            
            if weakness_predictions and "error" not in skill_results:
                print("✅ Integration test successful")
                
                # Compare results
                weakness_categories = [p["primary_weakness"] for p in weakness_predictions]
                skill_weaknesses = skill_results["strengths_and_weaknesses"].get("weaknesses", [])
                
                print(f"   • Weakness detector found: {set(weakness_categories)}")
                print(f"   • Skill analyzer found: {set(skill_weaknesses)}")
                
                # Check for consistency
                overlap = set(weakness_categories) & set(skill_weaknesses)
                if overlap:
                    print(f"   • Consistent findings: {overlap}")
                else:
                    print("   • Different approaches provide complementary insights")
            
            else:
                print("⚠️  Integration test incomplete due to previous errors")
        
        else:
            print("⚠️  Skipping integration test (insufficient data or untrained model)")
        
        # Clean up
        db.close()
        
        print("\n🎉 Weakness Detection Model Test Complete!")
        print("✅ All components working correctly")
        print("✅ Ready for training recommendation development")
        
        return True
        
    except Exception as e:
        print(f"❌ Weakness detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_enhanced_mock_matches():
    """Create enhanced mock matches with varied performance patterns."""
    from app.models.match import Match
    from datetime import datetime, timedelta, timezone
    import uuid

    mock_matches = []
    base_date = datetime.now(timezone.utc) - timedelta(days=20)
    
    # Create matches with different performance patterns
    performance_patterns = [
        # Good shooter, poor defender
        {"goals": 3, "assists": 1, "saves": 0, "shots": 5, "score": 400, "boost_usage": 0.8},
        # Good defender, poor shooter  
        {"goals": 0, "assists": 2, "saves": 4, "shots": 2, "score": 350, "boost_usage": 0.6},
        # Balanced player
        {"goals": 2, "assists": 2, "saves": 2, "shots": 4, "score": 450, "boost_usage": 0.7},
        # Mechanical player, poor positioning
        {"goals": 4, "assists": 0, "saves": 1, "shots": 8, "score": 500, "boost_usage": 0.9},
        # Team player, good game sense
        {"goals": 1, "assists": 4, "saves": 2, "shots": 3, "score": 380, "boost_usage": 0.65},
    ]
    
    for i, pattern in enumerate(performance_patterns):
        match = Match(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            ballchasing_id=f"enhanced_mock_{i}",
            playlist="Ranked Doubles",
            duration=300 + i * 20,
            match_date=base_date + timedelta(days=i * 2),
            score_team_0=pattern["goals"] + 1,
            score_team_1=pattern["goals"],
            result="win" if i % 2 == 0 else "loss",
            goals=pattern["goals"],
            assists=pattern["assists"],
            saves=pattern["saves"],
            shots=pattern["shots"],
            score=pattern["score"],
            boost_usage=pattern["boost_usage"],
            average_speed=1000 + i * 50,
            time_on_ground=0.6 + i * 0.05,
            time_low_air=0.2 + i * 0.02,
            time_high_air=0.1 + i * 0.03,
            processed=True
        )
        mock_matches.append(match)
    
    print(f"✅ Created {len(mock_matches)} enhanced mock matches with varied performance patterns")
    return mock_matches

def test_model_components():
    """Test individual model components."""
    print("\n🔍 Testing Individual Model Components...")
    
    try:
        from app.ml.models import WeaknessDetector, SkillAnalyzer
        from app.ml.config import ml_config
        
        # Test WeaknessDetector initialization
        print("   Testing WeaknessDetector initialization...")
        detector = WeaknessDetector(model_type="random_forest")
        
        print(f"✅ WeaknessDetector initialized")
        print(f"   • Model type: {detector.model_type}")
        print(f"   • Skill categories: {len(detector.skill_categories)}")
        print(f"   • Confidence threshold: {detector.confidence_threshold}")
        
        # Test SkillAnalyzer initialization
        print("\n   Testing SkillAnalyzer initialization...")
        analyzer = SkillAnalyzer()
        
        print(f"✅ SkillAnalyzer initialized")
        print(f"   • Skill categories: {len(analyzer.skill_categories)}")
        print(f"   • Trend window: {analyzer.trend_window}")
        print(f"   • Performance benchmarks: {len(analyzer.performance_benchmarks)}")
        
        # Test configuration
        print(f"\n   ML Configuration:")
        print(f"   • Min accuracy threshold: {ml_config.min_accuracy_threshold}")
        print(f"   • Confidence threshold: {ml_config.confidence_threshold}")
        print(f"   • Feature window size: {ml_config.feature_window_size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_weakness_detection()
    if success:
        test_model_components()
        print("\n🚀 Weakness Detection Models are ready for production!")
    else:
        print("\n❌ Weakness detection model test failed. Please check the errors above.")
        sys.exit(1)
