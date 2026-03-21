"""Topic extraction component for identifying and ranking study topics from browsing data"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict
from datetime import date
import re
from urllib.parse import urlparse

from ..data.models import TabAnalyticsRecord


@dataclass
class RankedTopic:
    """A study topic with frequency and time metrics"""
    topic: str
    weekly_frequency: int
    daily_frequencies: Dict[date, int]
    total_time_seconds: int
    rank: int


@dataclass
class TopicExtractionResult:
    """Result of topic extraction containing ranked topics"""
    ranked_topics: List[RankedTopic]
    top_topics: List[RankedTopic]  # top N topics


class TopicExtractor:
    """Extracts and ranks study topics from browsing data"""
    
    def __init__(self, top_n: int = 5):
        """
        Initialize TopicExtractor
        
        Args:
            top_n: Number of top topics to return for content recommendation
        """
        self.top_n = top_n
    
    def extract_topics(self, sessions: List[TabAnalyticsRecord]) -> TopicExtractionResult:
        """
        Extract and rank topics from browsing sessions
        
        Args:
            sessions: List of browsing session records
            
        Returns:
            TopicExtractionResult containing ranked topics
        """
        if not sessions:
            return TopicExtractionResult(ranked_topics=[], top_topics=[])
        
        # Extract topics from each session
        topic_sessions = []
        for session in sessions:
            topic = self.extract_topic_from_url(session.url, session.hostname)
            if topic:
                topic_sessions.append((topic, session))
        
        # Calculate daily frequencies
        daily_freq = self.calculate_daily_frequency(sessions)
        
        # Calculate weekly frequencies
        weekly_freq = self.calculate_weekly_frequency(sessions)
        
        # Calculate total time per topic
        topic_time_map = defaultdict(int)
        for topic, session in topic_sessions:
            topic_time_map[topic] += session.active_seconds
        
        # Rank topics
        ranked_topics = self.rank_topics(weekly_freq, dict(topic_time_map), daily_freq)
        
        # Get top N topics
        top_topics = ranked_topics[:self.top_n]
        
        return TopicExtractionResult(
            ranked_topics=ranked_topics,
            top_topics=top_topics
        )
    
    def extract_topic_from_url(self, url: str, hostname: str) -> Optional[str]:
        """
        Extract topic from URL and hostname using pattern matching
        
        Args:
            url: Full URL of the browsing session
            hostname: Hostname from the URL
            
        Returns:
            Extracted topic string or None if no topic found
        """
        # Parse the URL
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Common patterns for educational content
        # Pattern 1: /topic/subtopic or /learn/topic
        topic_patterns = [
            r'/(?:topic|learn|course|tutorial|guide|docs?|documentation)/([a-z0-9-]+)',
            r'/([a-z0-9-]+)/(?:tutorial|guide|learn|course)',
            r'/tag/([a-z0-9-]+)',
            r'/category/([a-z0-9-]+)',
        ]
        
        for pattern in topic_patterns:
            match = re.search(pattern, path)
            if match:
                topic = match.group(1).replace('-', ' ').replace('_', ' ')
                return topic
        
        # Pattern 2: Extract from path segments (e.g., /python/advanced-concepts)
        path_segments = [seg for seg in path.split('/') if seg and len(seg) > 2]
        if path_segments:
            # Use the first meaningful segment as topic
            first_segment = path_segments[0].replace('-', ' ').replace('_', ' ')
            # Filter out common non-topic segments
            non_topics = {'blog', 'post', 'article', 'page', 'index', 'home', 'www'}
            if first_segment not in non_topics:
                return first_segment
        
        # Pattern 3: Extract from query parameters (e.g., ?q=machine+learning)
        if parsed.query:
            query_match = re.search(r'[?&]q=([^&]+)', url)
            if query_match:
                topic = query_match.group(1).replace('+', ' ').replace('%20', ' ')
                return topic
        
        # Fallback: Use hostname as topic (remove common prefixes and TLD)
        hostname_clean = hostname.lower()
        hostname_clean = re.sub(r'^(www\.|m\.)', '', hostname_clean)
        hostname_clean = re.sub(r'\.(com|org|net|edu|io|dev)$', '', hostname_clean)
        
        return hostname_clean
    
    def calculate_daily_frequency(self, sessions: List[TabAnalyticsRecord]) -> Dict[str, Dict[date, int]]:
        """
        Calculate daily frequency for each topic
        
        Args:
            sessions: List of browsing session records
            
        Returns:
            Dictionary mapping topic to daily frequency counts
        """
        daily_freq = defaultdict(lambda: defaultdict(int))
        
        for session in sessions:
            topic = self.extract_topic_from_url(session.url, session.hostname)
            if topic:
                session_date = session.timestamp.date()
                daily_freq[topic][session_date] += 1
        
        # Convert to regular dict
        return {topic: dict(dates) for topic, dates in daily_freq.items()}
    
    def calculate_weekly_frequency(self, sessions: List[TabAnalyticsRecord]) -> Dict[str, int]:
        """
        Calculate weekly frequency for each topic across all sessions
        
        Args:
            sessions: List of browsing session records
            
        Returns:
            Dictionary mapping topic to total frequency count
        """
        weekly_freq = defaultdict(int)
        
        for session in sessions:
            topic = self.extract_topic_from_url(session.url, session.hostname)
            if topic:
                weekly_freq[topic] += 1
        
        return dict(weekly_freq)
    
    def rank_topics(
        self, 
        frequencies: Dict[str, int], 
        time_map: Dict[str, int],
        daily_frequencies: Dict[str, Dict[date, int]]
    ) -> List[RankedTopic]:
        """
        Rank topics by frequency with total time as tiebreaker
        
        Args:
            frequencies: Dictionary mapping topic to frequency count
            time_map: Dictionary mapping topic to total time in seconds
            daily_frequencies: Dictionary mapping topic to daily frequency counts
            
        Returns:
            List of RankedTopic objects sorted by rank
        """
        if not frequencies:
            return []
        
        # Create list of topics with their metrics
        topic_data = []
        for topic, freq in frequencies.items():
            total_time = time_map.get(topic, 0)
            daily_freq = daily_frequencies.get(topic, {})
            topic_data.append((topic, freq, total_time, daily_freq))
        
        # Sort by frequency (descending), then by total time (descending) as tiebreaker
        topic_data.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Create RankedTopic objects with rank
        ranked_topics = []
        for rank, (topic, freq, total_time, daily_freq) in enumerate(topic_data, start=1):
            ranked_topics.append(RankedTopic(
                topic=topic,
                weekly_frequency=freq,
                daily_frequencies=daily_freq,
                total_time_seconds=total_time,
                rank=rank
            ))
        
        return ranked_topics
