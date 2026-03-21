"""Pattern analysis component for identifying study patterns from browsing sessions"""

from typing import List, Dict
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

from ..data.models import TabAnalyticsRecord


@dataclass
class PatternAnalysisResult:
    """Result of pattern analysis containing study patterns and metrics"""
    productive_sessions: List[TabAnalyticsRecord]
    topic_time_map: Dict[str, int]  # topic -> total seconds
    peak_study_hours: List[int]  # hours of day (0-23)
    content_type_preferences: Dict[str, float]  # content_type -> preference score
    sufficient_data: bool
    total_productive_time: int


class PatternAnalyzer:
    """Analyzes browsing sessions to identify study patterns and preferences"""
    
    def __init__(self, min_productive_sessions: int = 10):
        """
        Initialize PatternAnalyzer
        
        Args:
            min_productive_sessions: Minimum number of productive sessions required for analysis
        """
        self.min_productive_sessions = min_productive_sessions
    
    def analyze(self, tab_analytics: List[TabAnalyticsRecord]) -> PatternAnalysisResult:
        """
        Analyze browsing sessions to identify study patterns
        
        Args:
            tab_analytics: List of browsing session records
            
        Returns:
            PatternAnalysisResult containing analysis results
        """
        # Identify productive sessions
        productive_sessions = self.identify_productive_sessions(tab_analytics)
        
        # Check if we have sufficient data
        sufficient_data = len(productive_sessions) >= self.min_productive_sessions
        
        # Calculate topic time map
        topic_time_map = self.calculate_topic_time(productive_sessions)
        
        # Identify peak study hours
        peak_study_hours = self.identify_peak_hours(productive_sessions)
        
        # Correlate content type preferences
        content_type_preferences = self.correlate_content_preferences(productive_sessions)
        
        # Calculate total productive time
        total_productive_time = sum(session.active_seconds for session in productive_sessions)
        
        return PatternAnalysisResult(
            productive_sessions=productive_sessions,
            topic_time_map=topic_time_map,
            peak_study_hours=peak_study_hours,
            content_type_preferences=content_type_preferences,
            sufficient_data=sufficient_data,
            total_productive_time=total_productive_time
        )
    
    def identify_productive_sessions(self, records: List[TabAnalyticsRecord]) -> List[TabAnalyticsRecord]:
        """
        Filter sessions categorized as productive
        
        Args:
            records: List of browsing session records
            
        Returns:
            List of productive session records
        """
        return [record for record in records if record.category == "productive"]
    
    def calculate_topic_time(self, sessions: List[TabAnalyticsRecord]) -> Dict[str, int]:
        """
        Calculate total time spent on each topic
        
        Args:
            sessions: List of productive session records
            
        Returns:
            Dictionary mapping topic (hostname) to total seconds
        """
        topic_time = defaultdict(int)
        
        for session in sessions:
            # Use hostname as the topic identifier
            topic = session.hostname
            topic_time[topic] += session.active_seconds
        
        return dict(topic_time)
    
    def identify_peak_hours(self, sessions: List[TabAnalyticsRecord]) -> List[int]:
        """
        Identify peak study hours based on timestamp distribution
        
        Args:
            sessions: List of productive session records
            
        Returns:
            List of hours (0-23) sorted by activity level (descending)
        """
        if not sessions:
            return []
        
        # Count sessions per hour
        hour_counts = defaultdict(int)
        
        for session in sessions:
            hour = session.timestamp.hour
            hour_counts[hour] += 1
        
        # Sort hours by count (descending) and return
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [hour for hour, count in sorted_hours]
    
    def correlate_content_preferences(self, sessions: List[TabAnalyticsRecord]) -> Dict[str, float]:
        """
        Correlate content type preferences with productive sessions
        
        Args:
            sessions: List of productive session records
            
        Returns:
            Dictionary mapping content_type to preference score (0.0 to 1.0)
        """
        if not sessions:
            return {}
        
        # Calculate total time per content type
        content_type_time = defaultdict(int)
        
        for session in sessions:
            content_type_time[session.content_type] += session.active_seconds
        
        # Calculate total time across all content types
        total_time = sum(content_type_time.values())
        
        if total_time == 0:
            return {}
        
        # Calculate preference scores as proportion of total time
        preferences = {
            content_type: time / total_time
            for content_type, time in content_type_time.items()
        }
        
        return preferences
