"""
ML API module for RocketTrainer.

This module provides REST API endpoints for machine learning operations including:
- Weakness detection and analysis
- Training pack recommendations  
- Model status and monitoring

The ML API is designed for high performance with Redis caching and
comprehensive error handling to meet <500ms response time requirements.
"""

from .endpoints import router

__all__ = ["router"]
