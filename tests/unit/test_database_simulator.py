"""Unit tests for DatabaseSimulator class"""

import pytest
from datetime import datetime, timedelta, date
from src.data.database_simulator import DatabaseSimulator
from src.data.models import TabAnalyticsRecord, ContentPreferenceRecord


@pytest.fixture
def simulator():
    """Create DatabaseSimulator instance with fixed seed"""
    return DatabaseSimulator(seed=42)


@pytest.fixture
def date_range():
    """Sample date range for testing"""
    start = datetime(2024, 1, 1, 0, 0, 0)
    end = datetime(2024, 1, 7, 23, 59, 59)
    return (start, end)


class TestDatabaseSimulatorInit:
    """Test DatabaseSimulator initialization"""
    
    def test_init_with_seed(self):
        """Test initialization with seed for reproducibility"""
        sim1 = DatabaseSimulator(seed=42)
        sim2 = DatabaseSimulator(seed=42)
        
        # Both should generate same data
        records1 = sim1.generate_tab_analytics(10, (datetime(2024, 1, 1), datetime(2024, 1, 2)))
        records2 = sim2.generate_tab_analytics(10, (datetime(2024, 1, 1), datetime(2024, 1, 2)))
        
        assert len(records1) == len(records2)
        for r1, r2 in zip(records1, records2):
            assert r1.category == r2.category
            assert r1.content_type == r2.content_type
    
    def test_init_without_seed(self):
        """Test initialization without seed produces random data"""
        sim = DatabaseSimulator()
        records = sim.generate_tab_analytics(10, (datetime(2024, 1, 1), datetime(2024, 1, 2)))
        assert len(records) == 10


class TestGenerateTabAnalytics:
    """Test tab_analytics record generation"""
    
    def test_generates_correct_number_of_records(self, simulator, date_range):
        """Test that correct number of records are generated"""
        records = simulator.generate_tab_analytics(50, date_range)
        assert len(records) == 50
    
    def test_all_records_are_valid(self, simulator, date_range):
        """Test that all generated records are valid TabAnalyticsRecord objects"""
        records = simulator.generate_tab_analytics(20, date_range)
        
        for record in records:
            assert isinstance(record, TabAnalyticsRecord)
            assert record.session_id is not None
            assert record.hostname is not None
            assert record.url is not None
            assert record.category in ['productive', 'distraction', 'neutral']
            assert record.content_type in ['text', 'video', 'interactive', 'audio', 'mixed']
            assert record.active_seconds > 0
            assert record.timestamp is not None
    
    def test_records_sorted_by_timestamp(self, simulator, date_range):
        """Test that records are sorted chronologically"""
        records = simulator.generate_tab_analytics(30, date_range)
        
        timestamps = [r.timestamp for r in records]
        assert timestamps == sorted(timestamps)
    
    def test_timestamps_within_range(self, simulator, date_range):
        """Test that all timestamps fall within specified range"""
        records = simulator.generate_tab_analytics(25, date_range)
        start, end = date_range
        
        for record in records:
            assert start <= record.timestamp <= end
    
    def test_productive_sessions_use_productive_domains(self, simulator, date_range):
        """Test that productive sessions use appropriate domains"""
        records = simulator.generate_tab_analytics(100, date_range)
        
        productive_records = [r for r in records if r.category == 'productive']
        
        for record in productive_records:
            assert record.hostname in DatabaseSimulator.PRODUCTIVE_DOMAINS
    
    def test_distraction_sessions_use_distraction_domains(self, simulator, date_range):
        """Test that distraction sessions use appropriate domains"""
        records = simulator.generate_tab_analytics(100, date_range)
        
        distraction_records = [r for r in records if r.category == 'distraction']
        
        for record in distraction_records:
            assert record.hostname in DatabaseSimulator.DISTRACTION_DOMAINS
    
    def test_category_distribution_is_realistic(self, simulator, date_range):
        """Test that category distribution follows expected weights"""
        records = simulator.generate_tab_analytics(1000, date_range)
        
        categories = [r.category for r in records]
        productive_ratio = categories.count('productive') / len(categories)
        distraction_ratio = categories.count('distraction') / len(categories)
        neutral_ratio = categories.count('neutral') / len(categories)
        
        # Allow 10% tolerance
        assert 0.25 <= productive_ratio <= 0.45
        assert 0.30 <= distraction_ratio <= 0.50
        assert 0.15 <= neutral_ratio <= 0.35


class TestGenerateContentPreferences:
    """Test content_preferences generation"""
    
    def test_generates_preferences_from_tab_analytics(self, simulator, date_range):
        """Test that preferences are generated from tab analytics"""
        tab_records = simulator.generate_tab_analytics(50, date_range)
        preferences = simulator.generate_content_preferences(tab_records)
        
        assert len(preferences) > 0
        assert all(isinstance(p, ContentPreferenceRecord) for p in preferences)
    
    def test_preferences_sorted_by_date(self, simulator, date_range):
        """Test that preferences are sorted by date"""
        tab_records = simulator.generate_tab_analytics(50, date_range)
        preferences = simulator.generate_content_preferences(tab_records)
        
        dates = [p.date for p in preferences]
        assert dates == sorted(dates)
    
    def test_preferences_aggregate_correctly(self, simulator):
        """Test that preferences correctly aggregate tab analytics"""
        # Create specific tab records
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 23, 59, 59)
        
        tab_records = simulator.generate_tab_analytics(20, (start, end))
        preferences = simulator.generate_content_preferences(tab_records)
        
        # Verify aggregation
        for pref in preferences:
            # Find matching tab records
            matching_records = [
                r for r in tab_records
                if r.timestamp.date() == pref.date and r.content_type == pref.content_type
            ]
            
            # Verify totals
            expected_time = sum(r.active_seconds for r in matching_records)
            assert pref.total_time_seconds == expected_time
            assert pref.session_count == len(matching_records)
    
    def test_productivity_score_calculation(self, simulator, date_range):
        """Test that productivity score is calculated correctly"""
        tab_records = simulator.generate_tab_analytics(50, date_range)
        preferences = simulator.generate_content_preferences(tab_records)
        
        for pref in preferences:
            assert 0.0 <= pref.productivity_score <= 1.0
    
    def test_empty_tab_analytics_returns_empty_preferences(self, simulator):
        """Test that empty input returns empty preferences"""
        preferences = simulator.generate_content_preferences([])
        assert len(preferences) == 0


class TestGenerateRealisticSessionDuration:
    """Test session duration generation"""
    
    def test_duration_within_bounds(self, simulator):
        """Test that durations are within reasonable bounds"""
        for _ in range(100):
            duration = simulator.generate_realistic_session_duration()
            assert 5 <= duration <= 7200  # 5 seconds to 2 hours
    
    def test_productive_sessions_longer(self, simulator):
        """Test that productive sessions tend to be longer"""
        productive_durations = [
            simulator.generate_realistic_session_duration('productive')
            for _ in range(100)
        ]
        distraction_durations = [
            simulator.generate_realistic_session_duration('distraction')
            for _ in range(100)
        ]
        
        avg_productive = sum(productive_durations) / len(productive_durations)
        avg_distraction = sum(distraction_durations) / len(distraction_durations)
        
        # Productive sessions should average longer
        assert avg_productive > avg_distraction
    
    def test_different_categories_produce_different_distributions(self, simulator):
        """Test that different categories have different duration patterns"""
        productive = simulator.generate_realistic_session_duration('productive')
        distraction = simulator.generate_realistic_session_duration('distraction')
        neutral = simulator.generate_realistic_session_duration('neutral')
        
        # All should be valid durations
        assert all(5 <= d <= 7200 for d in [productive, distraction, neutral])


class TestGenerateRealisticTimestamp:
    """Test timestamp generation with daily/weekly patterns"""
    
    def test_timestamp_within_range(self, simulator, date_range):
        """Test that timestamps fall within specified range"""
        for _ in range(50):
            timestamp = simulator.generate_realistic_timestamp(date_range)
            start, end = date_range
            assert start <= timestamp <= end
    
    def test_peak_hours_more_common(self, simulator):
        """Test that peak hours (9-23) are more common than off-peak"""
        date_range = (datetime(2024, 1, 1), datetime(2024, 1, 7))
        timestamps = [
            simulator.generate_realistic_timestamp(date_range)
            for _ in range(500)
        ]
        
        peak_count = sum(1 for ts in timestamps if 9 <= ts.hour < 23)
        off_peak_count = len(timestamps) - peak_count
        
        # Peak hours should be more common (around 70%)
        peak_ratio = peak_count / len(timestamps)
        assert 0.60 <= peak_ratio <= 0.80
    
    def test_timestamps_have_varied_minutes_and_seconds(self, simulator, date_range):
        """Test that timestamps have realistic minute/second variation"""
        timestamps = [
            simulator.generate_realistic_timestamp(date_range)
            for _ in range(50)
        ]
        
        minutes = [ts.minute for ts in timestamps]
        seconds = [ts.second for ts in timestamps]
        
        # Should have variety (not all the same)
        assert len(set(minutes)) > 10
        assert len(set(seconds)) > 10


class TestIntegration:
    """Integration tests for complete workflow"""
    
    def test_complete_workflow(self, simulator, date_range):
        """Test complete workflow from tab analytics to preferences"""
        # Generate tab analytics
        tab_records = simulator.generate_tab_analytics(100, date_range)
        
        # Generate preferences
        preferences = simulator.generate_content_preferences(tab_records)
        
        # Verify consistency
        assert len(tab_records) == 100
        assert len(preferences) > 0
        
        # All dates in preferences should come from tab records
        tab_dates = set(r.timestamp.date() for r in tab_records)
        pref_dates = set(p.date for p in preferences)
        assert pref_dates.issubset(tab_dates)
    
    def test_reproducibility_with_seed(self):
        """Test that same seed produces identical results"""
        sim1 = DatabaseSimulator(seed=123)
        sim2 = DatabaseSimulator(seed=123)
        
        date_range = (datetime(2024, 1, 1), datetime(2024, 1, 7))
        
        records1 = sim1.generate_tab_analytics(50, date_range)
        records2 = sim2.generate_tab_analytics(50, date_range)
        
        # Should be identical
        for r1, r2 in zip(records1, records2):
            assert r1.category == r2.category
            assert r1.content_type == r2.content_type
            assert r1.hostname == r2.hostname
            assert r1.active_seconds == r2.active_seconds
