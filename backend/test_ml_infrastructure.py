#!/usr/bin/env python3
"""
Test ML Infrastructure Setup

Quick test to verify that the ML infrastructure is properly set up
and all components can be imported and initialized.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ml_imports():
    """Test that all ML components can be imported."""
    print("🧪 Testing ML Infrastructure Setup...")
    
    try:
        # Test core ML imports
        from app.ml.config import MLConfig, ml_config
        from app.ml.utils import ModelManager, DataValidator, PerformanceMonitor
        print("✅ Core ML components imported successfully")
        
        # Test configuration
        print(f"✅ ML Config loaded - Min accuracy threshold: {ml_config.min_accuracy_threshold}")
        print(f"✅ Skill categories: {len(ml_config.skill_categories)} categories")
        
        # Test model manager
        model_manager = ModelManager()
        print(f"✅ Model Manager initialized - Models dir: {model_manager.models_dir}")
        
        # Test data validator
        validator = DataValidator()
        print("✅ Data Validator initialized")
        
        # Test performance monitor
        monitor = PerformanceMonitor()
        print("✅ Performance Monitor initialized")
        
        # Test base model import
        from app.ml.models.base import BaseMLModel
        print("✅ Base ML Model class imported")
        
        print("\n🎉 ML Infrastructure Setup Complete!")
        print("✅ All components initialized successfully")
        print("✅ Ready for ML model development")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ml_config():
    """Test ML configuration values."""
    from app.ml.config import ml_config

    print("\n📋 ML Configuration Summary:")
    print(f"   • Weakness Detection Model: {ml_config.weakness_detection_model}")
    print(f"   • Recommendation Model: {ml_config.recommendation_model}")
    print(f"   • Feature Window Size: {ml_config.feature_window_size}")
    print(f"   • Min Matches Required: {ml_config.min_matches_required}")
    print(f"   • Min Accuracy Threshold: {ml_config.min_accuracy_threshold}")
    print(f"   • Confidence Threshold: {ml_config.confidence_threshold}")
    print(f"   • Skill Categories: {', '.join([cat.value for cat in ml_config.skill_categories])}")

if __name__ == "__main__":
    success = test_ml_imports()
    if success:
        test_ml_config()
        print("\n🚀 Ready to proceed with Phase 3 ML Development!")
    else:
        print("\n❌ ML Infrastructure setup failed. Please check the errors above.")
        sys.exit(1)
