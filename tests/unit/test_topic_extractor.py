"""Unit tests for TopicExtractor class"""

import pytest
from datetime import datetime, date
from src.analysis.topic_extractor import TopicExtractor, RankedTopic, TopicExtractionResult
from src.data.models import TabAnalyticsRecord


@pytest.fixture
def extractor():
    """Create TopicExtractor instance"""
    return TopicExtractor(top_n=5)


@pytest.fixture
def sample_sessions():
    """Create sample browsing sessions for testing"""
    return [
        TabAnalyticsRecord(
            session_id="s1",
            hostname="stackoverflow.com",
            url="https://stackoverflow.com/questions/python/list-comprehension",
            category="productive",
            content_type="text",
            active_seconds=300,
            timestamp=datetime(2024, 1, 1, 10, 0, 0)
        ),
        TabAnalyticsRecord(
            session_id="s2",
            hostname="stackoverflow.com",
            url="https://stackoverflow.com/questions/python/decorators",
            category="productive",
            content_type="text",
            active_seconds=450,
            timestamp=datetime(2024, 1, 1, 11, 0, 0)
        ),
        TabAnalyticsRecord(
            session_id="s3",
            hostname="docs.python.org",
            url="https://docs.python.org/3/tutorial/datastructures.html",
            category="productive",
            content_type="text",
            active_seconds=600,
            timestamp=datetime(2024, 1, 2, 9, 0, 0)
        ),
        TabAnalyticsRecord(
            session_id="s4",
            hostname="medium.com",
            url="https://medium.com/topic/machine-learning",
            category="productive",
            content_type="text",
            active_seconds=400,
            timestamp=datetime(2024, 1, 2, 14, 0, 0)
        ),
        TabAnalyticsRecord(
            session_id="s5",
            hostname="medium.com",
            url="https://medium.com/topic/machine-learning",
            category="productive",
            content_type="text",
            active_seconds=350,
            timestamp=datetime(2024, 1, 3, 10, 0, 0)
        ),
    ]


class TestTopicExtractorInit:
    """Test TopicExtractor initialization"""
    
    def test_init_with_default_top_n(self):
        """Test initialization with default top_n value"""
        extractor = TopicExtractor()
        assert extractor.top_n == 5
    
    def test_init_with_custom_top_n(self):
        """Test initialization with custom top_n value"""
        extractor = TopicExtractor(top_n=10)
        assert extractor.top_n == 10


class TestExtractTopicFromUrl:
    """Test topic extraction from URLs"""
    
    def test_extract_from_topic_path(self, extractor):
        """Test extraction from /topic/ path pattern"""
        url = "https://medium.com/topic/machine-learning"
        hostname = "medium.com"
        topic = extractor.extract_topic_from_url(url, hostname)
        assert topic == "machine learning"
    
    def test_extract_from_learn_path(self, extractor):
        """Test extraction from /learn/ path pattern"""
        url = "https://example.com/learn/python-basics"
        hostname = "example.com"
        topic = extractor.extract_topic_from_url(url, hostname)
        assert topic == "python basics"
    
    def test_extract_from_course_path(self, extractor):
        """Test extraction from /course/ path pattern"""
        url = "https://example.com/course/data-science"
        hostname = "example.com"
        topic = extractor.extract_topic_from_url(url, hostname)
        assert topic == "data science"
    
    def test_extract_from_tag_path(self, extractor):
        """Test extraction from /tag/ path pattern"""
        url = "https://dev.to/tag/javascript"
        hostname = "dev.to"
        topic = extractor.extract_topic_from_url(url, hostname)
        assert topic == "javascript"
    
    def test_extract_from_path_segments(self, extractor):
        """Test extraction from path segments"""
        url = "https://docs.python.org/3/tutorial/datastructures.html"
        hostname = "docs.python.org"
        topic = extractor.extract_topic_from_url(url, hostname)
        # Should extract first meaningful segment
        assert topic in ["3", "tutorial"]
    
    def test_extract_from_query_parameter(self, extractor):
        """Test extraction from query parameter"""
        url = "https://google.com/search?q=machine+learning"
        hostname = "google.com"
        topic = extractor.extract_topic_from_url(url, hostname)
        assert topic == "machine learning"
    
    def test_fallback_to_hostname(self, extractor):
        """Test fallback to hostname when no pattern matches"""
        url = "https://stackoverflow.com/"
        hostname = "stackoverflow.com"
        topic = extractor.extract_topic_from_url(url, hostname)
        assert topic == "stackoverflow"
    
    def test_hostname_cleaning(self, extractor):
        """Test that hostname is cleaned properly"""
        url = "https://www.github.com/"
        hostname = "www.github.com"
        topic = extractor.extract_topic_from_url(url, hostname)
        assert topic == "github"
    
    def test_case_insensitive(self, extractor):
        """Test that extraction is case insensitive"""
        url = "https://example.com/Topic/Machine-Learning"
        hostname = "example.com"
        topic = extractor.extract_topic_from_url(url, hostname)
        assert topic == "machine learning"


class TestCalculateDailyFrequency:
    """Test daily frequency calculation"""
    
    def test_calculate_daily_frequency(self, extractor, sample_sessions):
        """Test daily frequency calculation"""
        daily_freq = extractor.calculate_daily_frequency(sample_sessions)
        
        assert isinstance(daily_freq, dict)
        assert len(daily_freq) > 0
        
        # Check that each topic has daily frequencies
        for topic, dates in daily_freq.items():
            assert isinstance(dates, dict)
            for d, count in dates.items():
                assert isinstance(d, date)
                assert isinstance(count, int)
                assert count > 0
    
    def test_empty_sessions_returns_empty_dict(self, extractor):
        """Test that empty sessions return empty dictionary"""
        daily_freq = extractor.calculate_daily_frequency([])
        assert daily_freq == {}
    
    def test_same_topic_different_days(self, extractor):
        """Test that same topic on different days is counted separately"""
        sessions = [
            TabAnalyticsRecord(
                session_id="s1",
                hostname="example.com",
                url="https://example.com/topic/python",
                category="productive",
                content_type="text",
                active_seconds=300,
                timestamp=datetime(2024, 1, 1, 10, 0, 0)
            ),
            TabAnalyticsRecord(
                session_id="s2",
                hostname="example.com",
                url="https://example.com/topic/python",
                category="productive",
                content_type="text",
                active_seconds=400,
                timestamp=datetime(2024, 1, 2, 10, 0, 0)
            ),
        ]
        
        daily_freq = extractor.calculate_daily_frequency(sessions)
        
        # Should have python topic with 2 different dates
        assert "python" in daily_freq
        assert len(daily_freq["python"]) == 2
        assert daily_freq["python"][date(2024, 1, 1)] == 1
        assert daily_freq["python"][date(2024, 1, 2)] == 1


class TestCalculateWeeklyFrequency:
    """Test weekly frequency calculation"""
    
    def test_calculate_weekly_frequency(self, extractor, sample_sessions):
        """Test weekly frequency calculation"""
        weekly_freq = extractor.calculate_weekly_frequency(sample_sessions)
        
        assert isinstance(weekly_freq, dict)
        assert len(weekly_freq) > 0
        
        # Check that all frequencies are positive integers
        for topic, count in weekly_freq.items():
            assert isinstance(topic, str)
            assert isinstance(count, int)
            assert count > 0
    
    def test_empty_sessions_returns_empty_dict(self, extractor):
        """Test that empty sessions return empty dictionary"""
        weekly_freq = extractor.calculate_weekly_frequency([])
        assert weekly_freq == {}
    
    def test_frequency_counts_all_occurrences(self, extractor):
        """Test that frequency counts all occurrences of a topic"""
        sessions = [
            TabAnalyticsRecord(
                session_id=f"s{i}",
                hostname="example.com",
                url="https://example.com/topic/python",
                category="productive",
                content_type="text",
                active_seconds=300,
                timestamp=datetime(2024, 1, 1, 10, i, 0)
            )
            for i in range(5)
        ]
        
        weekly_freq = extractor.calculate_weekly_frequency(sessions)
        
        assert "python" in weekly_freq
        assert weekly_freq["python"] == 5


class TestRankTopics:
    """Test topic ranking"""
    
    def test_rank_by_frequency(self, extractor):
        """Test that topics are ranked by frequency"""
        frequencies = {"python": 10, "javascript": 5, "java": 8}
        time_map = {"python": 1000, "javascript": 500, "java": 800}
        daily_freq = {
            "python": {date(2024, 1, 1): 10},
            "javascript": {date(2024, 1, 1): 5},
            "java": {date(2024, 1, 1): 8}
        }
        
        ranked = extractor.rank_topics(frequencies, time_map, daily_freq)
        
        assert len(ranked) == 3
        assert ranked[0].topic == "python"
        assert ranked[0].rank == 1
        assert ranked[1].topic == "java"
        assert ranked[1].rank == 2
        assert ranked[2].topic == "javascript"
        assert ranked[2].rank == 3
    
    def test_tiebreaker_by_time(self, extractor):
        """Test that time is used as tiebreaker when frequencies are equal"""
        frequencies = {"python": 10, "javascript": 10, "java": 10}
        time_map = {"python": 1000, "javascript": 1500, "java": 800}
        daily_freq = {
            "python": {date(2024, 1, 1): 10},
            "javascript": {date(2024, 1, 1): 10},
            "java": {date(2024, 1, 1): 10}
        }
        
        ranked = extractor.rank_topics(frequencies, time_map, daily_freq)
        
        assert len(ranked) == 3
        # With equal frequency, should be sorted by time (descending)
        assert ranked[0].topic == "javascript"  # 1500 seconds
        assert ranked[1].topic == "python"  # 1000 seconds
        assert ranked[2].topic == "java"  # 800 seconds
    
    def test_empty_frequencies_returns_empty_list(self, extractor):
        """Test that empty frequencies return empty list"""
        ranked = extractor.rank_topics({}, {}, {})
        assert ranked == []
    
    def test_ranked_topic_contains_all_fields(self, extractor):
        """Test that RankedTopic contains all required fields"""
        frequencies = {"python": 10}
        time_map = {"python": 1000}
        daily_freq = {"python": {date(2024, 1, 1): 5, date(2024, 1, 2): 5}}
        
        ranked = extractor.rank_topics(frequencies, time_map, daily_freq)
        
        assert len(ranked) == 1
        topic = ranked[0]
        assert isinstance(topic, RankedTopic)
        assert topic.topic == "python"
        assert topic.weekly_frequency == 10
        assert topic.total_time_seconds == 1000
        assert topic.rank == 1
        assert len(topic.daily_frequencies) == 2


class TestExtractTopics:
    """Test complete topic extraction workflow"""
    
    def test_extract_topics_returns_result(self, extractor, sample_sessions):
        """Test that extract_topics returns TopicExtractionResult"""
        result = extractor.extract_topics(sample_sessions)
        
        assert isinstance(result, TopicExtractionResult)
        assert isinstance(result.ranked_topics, list)
        assert isinstance(result.top_topics, list)
    
    def test_top_topics_limited_to_top_n(self, extractor, sample_sessions):
        """Test that top_topics is limited to top_n"""
        result = extractor.extract_topics(sample_sessions)
        
        assert len(result.top_topics) <= extractor.top_n
    
    def test_empty_sessions_returns_empty_result(self, extractor):
        """Test that empty sessions return empty result"""
        result = extractor.extract_topics([])
        
        assert result.ranked_topics == []
        assert result.top_topics == []
    
    def test_ranked_topics_sorted_correctly(self, extractor, sample_sessions):
        """Test that ranked topics are sorted by frequency and time"""
        result = extractor.extract_topics(sample_sessions)
        
        # Verify that topics are sorted by rank
        for i in range(len(result.ranked_topics) - 1):
            current = result.ranked_topics[i]
            next_topic = result.ranked_topics[i + 1]
            
            # Current should have higher or equal frequency
            assert current.weekly_frequency >= next_topic.weekly_frequency
            
            # If frequencies are equal, current should have higher or equal time
            if current.weekly_frequency == next_topic.weekly_frequency:
                assert current.total_time_seconds >= next_topic.total_time_seconds
    
    def test_top_topics_are_subset_of_ranked(self, extractor, sample_sessions):
        """Test that top_topics is a subset of ranked_topics"""
        result = extractor.extract_topics(sample_sessions)
        
        top_topic_names = {t.topic for t in result.top_topics}
        ranked_topic_names = {t.topic for t in result.ranked_topics}
        
        assert top_topic_names.issubset(ranked_topic_names)
    
    def test_integration_with_real_data(self, extractor):
        """Test integration with realistic browsing data"""
        sessions = [
            TabAnalyticsRecord(
                session_id=f"s{i}",
                hostname="stackoverflow.com",
                url=f"https://stackoverflow.com/questions/python/question-{i}",
                category="productive",
                content_type="text",
                active_seconds=300 + i * 10,
                timestamp=datetime(2024, 1, 1 + (i % 7), 10, 0, 0)
            )
            for i in range(20)
        ]
        
        result = extractor.extract_topics(sessions)
        
        assert len(result.ranked_topics) > 0
        assert len(result.top_topics) > 0
        
        # Verify all ranked topics have valid data
        for topic in result.ranked_topics:
            assert topic.topic is not None
            assert topic.weekly_frequency > 0
            assert topic.total_time_seconds > 0
            assert topic.rank > 0
            assert len(topic.daily_frequencies) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_single_session(self, extractor):
        """Test with single session"""
        sessions = [
            TabAnalyticsRecord(
                session_id="s1",
                hostname="example.com",
                url="https://example.com/topic/python",
                category="productive",
                content_type="text",
                active_seconds=300,
                timestamp=datetime(2024, 1, 1, 10, 0, 0)
            )
        ]
        
        result = extractor.extract_topics(sessions)
        
        assert len(result.ranked_topics) == 1
        assert result.ranked_topics[0].topic == "python"
        assert result.ranked_topics[0].weekly_frequency == 1
    
    def test_more_topics_than_top_n(self, extractor):
        """Test when there are more topics than top_n"""
        sessions = [
            TabAnalyticsRecord(
                session_id=f"s{i}",
                hostname=f"topic{i}.com",
                url=f"https://topic{i}.com/learn/subject-{i}",
                category="productive",
                content_type="text",
                active_seconds=300,
                timestamp=datetime(2024, 1, 1, 10, i, 0)
            )
            for i in range(10)
        ]
        
        result = extractor.extract_topics(sessions)
        
        assert len(result.ranked_topics) == 10
        assert len(result.top_topics) == extractor.top_n
    
    def test_urls_with_special_characters(self, extractor):
        """Test URLs with special characters"""
        url = "https://example.com/topic/c%2B%2B-programming"
        hostname = "example.com"
        topic = extractor.extract_topic_from_url(url, hostname)
        
        assert topic is not None
        assert isinstance(topic, str)
