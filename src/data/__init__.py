"""Data layer components for database interaction and simulation"""

from .database_connector import DatabaseConnector
from .database_simulator import DatabaseSimulator
from .models import (
    TabAnalyticsRecord,
    ContentPreferenceRecord,
    BlogPost,
    ResearchPaper
)

__all__ = [
    'DatabaseConnector',
    'DatabaseSimulator',
    'TabAnalyticsRecord',
    'ContentPreferenceRecord',
    'BlogPost',
    'ResearchPaper'
]
