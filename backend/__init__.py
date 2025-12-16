"""
Assessment Recommendation Engine Backend Package
"""

from flask import Flask
from .config import Config
from .recommender import AssessmentRecommender
from .database import DatabasePersistence

__version__ = "1.0.0"
__author__ = "Assessment Recommendation Engine"

__all__ = [
    'Flask',
    'Config',
    'AssessmentRecommender',
    'DatabasePersistence',
    'create_app',
    'get_recommender',
]


def create_app():
    """Factory function to create and configure the Flask application."""
    from .flask_app import app
    return app


def get_recommender():
    """Get the AssessmentRecommender instance."""
    return AssessmentRecommender()
