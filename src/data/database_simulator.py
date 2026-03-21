"""Database simulator for generating realistic browsing data for testing"""

import random
import uuid
from datetime import datetime, timedelta, date
from typing import List, Tuple, Optional, Dict
from collections import defaultdict

from .models import TabAnalyticsRecord, ContentPreferenceRecord


class DatabaseSimulator:
    """Generates realistic browsing data for testing when actual extension data is unavailable"""
    
    # Realistic distributions for categories
    CATEGORY_WEIGHTS = {
        'productive': 0.35,
        'distraction': 0.40,
        'neutral': 0.25
    }
    
    # Content type distributions
    CONTENT_TYPE_WEIGHTS = {
        'text': 0.45,
        'video': 0.25,
        'interactive': 0.15,
        'audio': 0.10,
        'mixed': 0.05
    }
    
    # Study-related domains for productive sessions
    PRODUCTIVE_DOMAINS = [
        'stackoverflow.com',
        'github.com',
        'medium.com',
        'dev.to',
        'arxiv.org',
        'scholar.google.com',
        'coursera.org',
        'udemy.com',
        'docs.python.org',
        'developer.mozilla.org',
        'leetcode.com',
        'kaggle.com',
        'towardsdatascience.com',
        'freecodecamp.org',
        'realpython.com'
    ]
    
    # Distraction domains
    DISTRACTION_DOMAINS = [
        'youtube.com',
        'reddit.com',
        'twitter.com',
        'facebook.com',
        'instagram.com',
        'tiktok.com',
        'netflix.com',
        'twitch.tv'
    ]
    
    # Neutral domains
    NEUTRAL_DOMAINS = [
        'gmail.com',
        'google.com',
        'amazon.com',
        'wikipedia.org',
        'news.ycombinator.com'
    ]
    
    # Study topics for URL generation
    STUDY_TOPICS = [
        'python', 'javascript', 'machine-learning', 'data-science',
        'web-development', 'algorithms', 'databases', 'cloud-computing',
        'cybersecurity', 'artificial-intelligence', 'react', 'nodejs',
        'docker', 'kubernetes', 'aws', 'deep-learning'
    ]
    
    # Peak study hours (9 AM - 11 PM with higher probability)
    PEAK_HOURS = list(range(9, 23))
    OFF_PEAK_HOURS = list(range(0, 9)) + [23]
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the database simulator
        
        Args:
            seed: Random seed for reproducible data generation
        """
        if seed is not None:
            random.seed(seed)
        self.rng = random.Random(seed)
    
    def generate_tab_analytics(
        self, 
        num_records: int, 
        date_range: Tuple[datetime, datetime]
    ) -> List[TabAnalyticsRecord]:
        """
        Generate realistic tab_analytics records
        
        Args:
            num_records: Number of records to generate
            date_range: Tuple of (start_datetime, end_datetime)
            
        Returns:
            List of TabAnalyticsRecord objects
        """
        records = []
        
        for _ in range(num_records):
            # Generate category based on realistic distribution
            category = self._weighted_choice(self.CATEGORY_WEIGHTS)
            
            # Select appropriate domain based on category
            if category == 'productive':
                hostname = self.rng.choice(self.PRODUCTIVE_DOMAINS)
            elif category == 'distraction':
                hostname = self.rng.choice(self.DISTRACTION_DOMAINS)
            else:
                hostname = self.rng.choice(self.NEUTRAL_DOMAINS)
            
            # Generate URL with topic for productive sessions
            if category == 'productive':
                topic = self.rng.choice(self.STUDY_TOPICS)
                url = f"https://{hostname}/{topic}/{self.rng.choice(['tutorial', 'guide', 'documentation', 'article'])}"
            else:
                url = f"https://{hostname}/{self.rng.choice(['watch', 'post', 'article'])}/{uuid.uuid4().hex[:8]}"
            
            # Generate content type
            content_type = self._weighted_choice(self.CONTENT_TYPE_WEIGHTS)
            
            # Generate realistic session duration
            active_seconds = self.generate_realistic_session_duration(category)
            
            # Generate realistic timestamp
            timestamp = self.generate_realistic_timestamp(date_range)
            
            # Create record
            record = TabAnalyticsRecord(
                session_id=str(uuid.uuid4()),
                hostname=hostname,
                url=url,
                category=category,
                content_type=content_type,
                active_seconds=active_seconds,
                timestamp=timestamp
            )
            records.append(record)
        
        # Sort by timestamp for realistic ordering
        records.sort(key=lambda r: r.timestamp)
        
        return records
    
    def generate_content_preferences(
        self, 
        tab_analytics: List[TabAnalyticsRecord]
    ) -> List[ContentPreferenceRecord]:
        """
        Generate content_preferences aggregates aligned with tab_analytics data
        
        Args:
            tab_analytics: List of TabAnalyticsRecord to aggregate
            
        Returns:
            List of ContentPreferenceRecord objects (daily aggregates)
        """
        # Group by date and content_type
        aggregates: Dict[Tuple[date, str], Dict] = defaultdict(lambda: {
            'total_time_seconds': 0,
            'session_count': 0,
            'productive_sessions': 0,
            'total_sessions': 0
        })
        
        for record in tab_analytics:
            record_date = record.timestamp.date()
            key = (record_date, record.content_type)
            
            aggregates[key]['total_time_seconds'] += record.active_seconds
            aggregates[key]['session_count'] += 1
            aggregates[key]['total_sessions'] += 1
            
            if record.category == 'productive':
                aggregates[key]['productive_sessions'] += 1
        
        # Convert to ContentPreferenceRecord objects
        preferences = []
        for (record_date, content_type), data in aggregates.items():
            # Calculate productivity score (ratio of productive sessions)
            productivity_score = (
                data['productive_sessions'] / data['total_sessions']
                if data['total_sessions'] > 0 else 0.0
            )
            
            preference = ContentPreferenceRecord(
                date=record_date,
                content_type=content_type,
                total_time_seconds=data['total_time_seconds'],
                session_count=data['session_count'],
                productivity_score=productivity_score
            )
            preferences.append(preference)
        
        # Sort by date
        preferences.sort(key=lambda p: p.date)
        
        return preferences
    
    def generate_realistic_session_duration(self, category: str = 'neutral') -> int:
        """
        Generate realistic session duration using log-normal distribution
        
        Args:
            category: Session category (affects duration distribution)
            
        Returns:
            Session duration in seconds
        """
        # Log-normal distribution parameters (mean and std of underlying normal)
        # Productive sessions tend to be longer
        if category == 'productive':
            mu = 5.5  # ln(seconds) - median around 4 minutes
            sigma = 1.2
        elif category == 'distraction':
            mu = 4.8  # ln(seconds) - median around 2 minutes
            sigma = 1.5
        else:  # neutral
            mu = 4.0  # ln(seconds) - median around 1 minute
            sigma = 1.0
        
        # Generate log-normal value
        duration = int(self.rng.lognormvariate(mu, sigma))
        
        # Clamp to reasonable bounds (5 seconds to 2 hours)
        duration = max(5, min(duration, 7200))
        
        return duration
    
    def generate_realistic_timestamp(
        self, 
        date_range: Tuple[datetime, datetime]
    ) -> datetime:
        """
        Generate realistic timestamp with daily/weekly patterns
        
        Creates timestamps that follow realistic usage patterns:
        - Higher probability during peak hours (9 AM - 11 PM)
        - Lower probability during off-peak hours (midnight - 9 AM)
        - Weekday vs weekend patterns
        
        Args:
            date_range: Tuple of (start_datetime, end_datetime)
            
        Returns:
            Datetime with realistic daily/weekly patterns
        """
        start_dt, end_dt = date_range
        
        # Calculate total seconds in range
        total_seconds = int((end_dt - start_dt).total_seconds())
        
        # Generate random offset
        random_seconds = self.rng.randint(0, total_seconds)
        base_timestamp = start_dt + timedelta(seconds=random_seconds)
        
        # Adjust hour to follow daily patterns
        # 70% chance of peak hours, 30% chance of off-peak
        if self.rng.random() < 0.70:
            hour = self.rng.choice(self.PEAK_HOURS)
        else:
            hour = self.rng.choice(self.OFF_PEAK_HOURS)
        
        # Replace hour while keeping date
        timestamp = base_timestamp.replace(
            hour=hour,
            minute=self.rng.randint(0, 59),
            second=self.rng.randint(0, 59)
        )
        
        # Ensure timestamp is within range
        if timestamp < start_dt:
            timestamp = start_dt
        elif timestamp > end_dt:
            timestamp = end_dt
        
        return timestamp
    
    def _weighted_choice(self, weights: Dict[str, float]) -> str:
        """
        Select a random item based on weights
        
        Args:
            weights: Dictionary mapping items to their weights
            
        Returns:
            Selected item
        """
        items = list(weights.keys())
        weight_values = list(weights.values())
        return self.rng.choices(items, weights=weight_values, k=1)[0]
