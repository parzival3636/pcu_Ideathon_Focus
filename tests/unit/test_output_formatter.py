"""Unit tests for OutputFormatter"""

import json
import pytest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from src.output.output_formatter import OutputFormatter
from src.output.recommendation_generator import TopicRecommendations, Recommendation


@pytest.fixture
def sample_recommendations():
    """Create sample recommendations for testing"""
    rec1 = Recommendation(
        title="Introduction to Python",
        url="https://example.com/python-intro",
        source="Example Blog",
        author="John Doe",
        content_type="blog",
        quality_score=0.85,
        publication_date=date(2023, 1, 15)
    )
    
    rec2 = Recommendation(
        title="Advanced Python Techniques",
        url="https://example.com/python-advanced",
        source="Tech Journal",
        author="Jane Smith",
        content_type="paper",
        quality_score=0.92,
        publication_date=date(2022, 6, 10)
    )
    
    rec3 = Recommendation(
        title="Python Best Practices",
        url="https://example.com/python-best",
        source="Dev Community",
        author=None,
        content_type="blog",
        quality_score=0.78,
        publication_date=None
    )
    
    topic_recs = TopicRecommendations(
        topic="Python Programming",
        recommendations=[rec1, rec2, rec3],
        total_count=3
    )
    
    return {"Python Programming": topic_recs}


def test_format_json_with_complete_metadata(sample_recommendations):
    """Test JSON formatting includes all required fields"""
    json_output = OutputFormatter.format_json(sample_recommendations)
    
    # Parse JSON to verify structure
    data = json.loads(json_output)
    
    assert "Python Programming" in data
    topic_data = data["Python Programming"]
    
    assert topic_data["topic"] == "Python Programming"
    assert topic_data["total_count"] == 3
    assert len(topic_data["recommendations"]) == 3
    
    # Check first recommendation has all fields
    rec = topic_data["recommendations"][0]
    assert rec["title"] == "Introduction to Python"
    assert rec["url"] == "https://example.com/python-intro"
    assert rec["source"] == "Example Blog"
    assert rec["author"] == "John Doe"
    assert rec["content_type"] == "blog"
    assert rec["quality_score"] == 0.85
    assert rec["publication_date"] == "2023-01-15"
    
    # Check handling of None values
    rec_with_none = topic_data["recommendations"][2]
    assert rec_with_none["author"] is None
    assert rec_with_none["publication_date"] is None


def test_format_markdown_readability(sample_recommendations):
    """Test Markdown formatting for readability"""
    markdown_output = OutputFormatter.format_markdown(sample_recommendations)
    
    # Check main structure
    assert "# Study Content Recommendations" in markdown_output
    assert "## Python Programming" in markdown_output
    assert "**Total Recommendations:** 3" in markdown_output
    
    # Check individual recommendations
    assert "### 1. Introduction to Python" in markdown_output
    assert "- **URL:** https://example.com/python-intro" in markdown_output
    assert "- **Author:** John Doe" in markdown_output
    assert "- **Quality Score:** 0.85" in markdown_output
    
    # Check handling of None author
    assert "- **Author:** Unknown" in markdown_output


def test_format_markdown_empty_recommendations():
    """Test Markdown formatting with empty recommendations"""
    empty_recs = TopicRecommendations(
        topic="Empty Topic",
        recommendations=[],
        total_count=0
    )
    
    markdown_output = OutputFormatter.format_markdown({"Empty Topic": empty_recs})
    
    assert "## Empty Topic" in markdown_output
    assert "**Total Recommendations:** 0" in markdown_output
    assert "*No recommendations available for this topic.*" in markdown_output


def test_save_to_file_json(sample_recommendations):
    """Test saving recommendations to JSON file"""
    with TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "recommendations.json"
        
        OutputFormatter.save_to_file(
            sample_recommendations,
            str(filepath),
            format="json"
        )
        
        # Verify file exists and contains valid JSON
        assert filepath.exists()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "Python Programming" in data


def test_save_to_file_markdown(sample_recommendations):
    """Test saving recommendations to Markdown file"""
    with TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "recommendations.md"
        
        OutputFormatter.save_to_file(
            sample_recommendations,
            str(filepath),
            format="markdown"
        )
        
        # Verify file exists and contains expected content
        assert filepath.exists()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# Study Content Recommendations" in content
        assert "## Python Programming" in content


def test_save_to_file_creates_parent_directories(sample_recommendations):
    """Test that save_to_file creates parent directories if needed"""
    with TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "subdir" / "nested" / "recommendations.json"
        
        OutputFormatter.save_to_file(
            sample_recommendations,
            str(filepath),
            format="json"
        )
        
        assert filepath.exists()


def test_save_to_file_invalid_format(sample_recommendations):
    """Test that invalid format raises ValueError"""
    with TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "recommendations.txt"
        
        with pytest.raises(ValueError, match="Unsupported format"):
            OutputFormatter.save_to_file(
                sample_recommendations,
                str(filepath),
                format="txt"
            )


def test_format_json_multiple_topics():
    """Test JSON formatting with multiple topics"""
    rec1 = Recommendation(
        title="Python Basics",
        url="https://example.com/python",
        source="Blog",
        author="Author 1",
        content_type="blog",
        quality_score=0.8,
        publication_date=date(2023, 1, 1)
    )
    
    rec2 = Recommendation(
        title="JavaScript Guide",
        url="https://example.com/js",
        source="Blog",
        author="Author 2",
        content_type="blog",
        quality_score=0.75,
        publication_date=date(2023, 2, 1)
    )
    
    recommendations = {
        "Python": TopicRecommendations("Python", [rec1], 1),
        "JavaScript": TopicRecommendations("JavaScript", [rec2], 1)
    }
    
    json_output = OutputFormatter.format_json(recommendations)
    data = json.loads(json_output)
    
    assert "Python" in data
    assert "JavaScript" in data
    assert data["Python"]["total_count"] == 1
    assert data["JavaScript"]["total_count"] == 1
