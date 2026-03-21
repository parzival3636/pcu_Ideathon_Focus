"""Unit tests for data models"""

import sys
sys.path.insert(0, 'src')

from datetime import datetime, date
import pytest
from data.models import (
    TabAnalyticsRecord,
    ContentPreferenceRecord,
    BlogPost,
    ResearchPaper
)


class TestTabAnalyticsRecord:
    """Tests for TabAnalyticsRecord model"""
    
    def test_valid_record_creation(self):
        """Test creating a valid TabAnalyticsRecord"""
        record = TabAnalyticsRecord(
            session_id="session_123",
            hostname="example.com",
            url="https://example.com/article",
            category="productive",
            content_type="text",
            active_seconds=300,
            timestamp=datetime.now()
        )
        assert record.session_id == "session_123"
        assert record.category == "productive"
        assert record.active_seconds == 300
    
    def test_invalid_category(self):
        """Test that invalid category raises validation error"""
        with pytest.raises(ValueError, match="category must be one of"):
            TabAnalyticsRecord(
                session_id="session_123",
                hostname="example.com",
                url="https://example.com/article",
                category="invalid_category",
                content_type="text",
                active_seconds=300,
                timestamp=datetime.now()
            )
    
    def test_invalid_content_type(self):
        """Test that invalid content_type raises validation error"""
        with pytest.raises(ValueError, match="content_type must be one of"):
            TabAnalyticsRecord(
                session_id="session_123",
                hostname="example.com",
                url="https://example.com/article",
                category="productive",
                content_type="invalid_type",
                active_seconds=300,
                timestamp=datetime.now()
            )
    
    def test_negative_active_seconds(self):
        """Test that negative active_seconds raises validation error"""
        with pytest.raises(ValueError):
            TabAnalyticsRecord(
                session_id="session_123",
                hostname="example.com",
                url="https://example.com/article",
                category="productive",
                content_type="text",
                active_seconds=-100,
                timestamp=datetime.now()
            )


class TestContentPreferenceRecord:
    """Tests for ContentPreferenceRecord model"""
    
    def test_valid_record_creation(self):
        """Test creating a valid ContentPreferenceRecord"""
        record = ContentPreferenceRecord(
            date=date.today(),
            content_type="video",
            total_time_seconds=3600,
            session_count=10,
            productivity_score=0.75
        )
        assert record.content_type == "video"
        assert record.productivity_score == 0.75
    
    def test_invalid_productivity_score(self):
        """Test that productivity_score outside 0-1 range raises error"""
        with pytest.raises(ValueError):
            ContentPreferenceRecord(
                date=date.today(),
                content_type="video",
                total_time_seconds=3600,
                session_count=10,
                productivity_score=1.5
            )


class TestBlogPost:
    """Tests for BlogPost model"""
    
    def test_valid_blog_post_creation(self):
        """Test creating a valid BlogPost"""
        post = BlogPost(
            title="Test Article",
            url="https://example.com/article",
            author="John Doe",
            publication_date=date.today(),
            source="example.com",
            view_count=1000,
            share_count=50,
            comment_count=10,
            raw_html="<html>content</html>"
        )
        assert post.title == "Test Article"
        assert post.view_count == 1000
    
    def test_optional_fields(self):
        """Test that optional fields can be None"""
        post = BlogPost(
            title="Test Article",
            url="https://example.com/article",
            source="example.com",
            raw_html="<html>content</html>"
        )
        assert post.author is None
        assert post.view_count is None


class TestResearchPaper:
    """Tests for ResearchPaper model"""
    
    def test_valid_paper_creation(self):
        """Test creating a valid ResearchPaper"""
        paper = ResearchPaper(
            title="Research Paper Title",
            url="https://arxiv.org/paper",
            authors=["Author One", "Author Two"],
            publication_venue="Conference 2023",
            publication_year=2023,
            view_count=5000,
            citation_count=100,
            abstract="This is the abstract"
        )
        assert paper.title == "Research Paper Title"
        assert len(paper.authors) == 2
        assert paper.citation_count == 100
    
    def test_invalid_publication_year(self):
        """Test that invalid publication year raises error"""
        with pytest.raises(ValueError):
            ResearchPaper(
                title="Research Paper Title",
                url="https://arxiv.org/paper",
                authors=["Author One"],
                publication_year=1800
            )
