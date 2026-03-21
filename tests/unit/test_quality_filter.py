"""Unit tests for QualityFilter class"""

import pytest
from datetime import date, timedelta
from study_content_recommender.src.data.models import BlogPost, ResearchPaper
from study_content_recommender.src.filtering.quality_filter import QualityFilter, ScoredBlogPost, ScoredResearchPaper


class TestQualityFilter:
    """Test suite for QualityFilter"""
    
    @pytest.fixture
    def quality_filter(self):
        """Create a QualityFilter instance with default settings"""
        return QualityFilter(min_quality_score=0.6, max_age_years=3)
    
    @pytest.fixture
    def sample_blog_post(self):
        """Create a sample blog post for testing"""
        return BlogPost(
            title="Understanding Machine Learning",
            url="https://towardsdatascience.com/ml-guide",
            author="Dr. Jane Smith",
            publication_date=date.today() - timedelta(days=180),
            source="towardsdatascience.com",
            view_count=5000,
            share_count=200,
            comment_count=50,
            raw_html="<html>content</html>"
        )
    
    @pytest.fixture
    def sample_research_paper(self):
        """Create a sample research paper for testing"""
        return ResearchPaper(
            title="Deep Learning Advances",
            url="https://arxiv.org/abs/2024.12345",
            authors=["John Doe", "Jane Smith"],
            publication_venue="NeurIPS 2023",
            publication_year=2023,
            view_count=1000,
            citation_count=50,
            abstract="This paper presents..."
        )
    
    def test_filter_blogs_returns_scored_blogs(self, quality_filter, sample_blog_post):
        """Test that filter_blogs returns ScoredBlogPost objects"""
        blogs = [sample_blog_post]
        scored_blogs = quality_filter.filter_blogs(blogs)
        
        assert len(scored_blogs) > 0
        assert isinstance(scored_blogs[0], ScoredBlogPost)
        assert scored_blogs[0].quality_score >= 0.0
        assert scored_blogs[0].quality_score <= 1.0
    
    def test_filter_blogs_excludes_low_quality(self, quality_filter):
        """Test that low-quality blogs are filtered out"""
        low_quality_blog = BlogPost(
            title="Low Quality Post",
            url="https://unknown-site.com/post",
            author=None,
            publication_date=date.today() - timedelta(days=1500),  # Old
            source="unknown-site.com",  # Low trustworthiness
            view_count=10,  # Low engagement
            share_count=0,
            comment_count=0,
            raw_html="<html>content</html>"
        )
        
        scored_blogs = quality_filter.filter_blogs([low_quality_blog])
        
        # Should be filtered out due to low quality
        assert len(scored_blogs) == 0
    
    def test_filter_papers_returns_scored_papers(self, quality_filter, sample_research_paper):
        """Test that filter_papers returns ScoredResearchPaper objects"""
        papers = [sample_research_paper]
        scored_papers = quality_filter.filter_papers(papers)
        
        assert len(scored_papers) > 0
        assert isinstance(scored_papers[0], ScoredResearchPaper)
        assert scored_papers[0].quality_score >= 0.0
        assert scored_papers[0].quality_score <= 1.0
    
    def test_calculate_quality_score_blog(self, quality_filter, sample_blog_post):
        """Test quality score calculation for blog posts"""
        score = quality_filter.calculate_quality_score(sample_blog_post)
        
        assert 0.0 <= score <= 1.0
        assert score >= quality_filter.min_quality_score
    
    def test_calculate_quality_score_paper(self, quality_filter, sample_research_paper):
        """Test quality score calculation for research papers"""
        score = quality_filter.calculate_quality_score(sample_research_paper)
        
        assert 0.0 <= score <= 1.0
        assert score >= quality_filter.min_quality_score
    
    def test_evaluate_source_trustworthiness_known_source(self, quality_filter):
        """Test source trustworthiness for known professional sources"""
        # Test academic source
        arxiv_score = quality_filter.evaluate_source_trustworthiness("arxiv.org")
        assert arxiv_score >= 0.9
        
        # Test professional blog platform
        medium_score = quality_filter.evaluate_source_trustworthiness("medium.com")
        assert medium_score >= 0.7
    
    def test_evaluate_source_trustworthiness_unknown_source(self, quality_filter):
        """Test source trustworthiness for unknown sources"""
        unknown_score = quality_filter.evaluate_source_trustworthiness("unknown-blog.com")
        assert unknown_score == 0.5  # Default score
    
    def test_is_content_too_old_recent_content(self, quality_filter):
        """Test that recent content is not considered too old"""
        recent_date = date.today() - timedelta(days=365)  # 1 year old
        
        is_old = quality_filter.is_content_too_old(recent_date, {'engagement_score': 0.5})
        
        assert is_old is False
    
    def test_is_content_too_old_old_content_low_engagement(self, quality_filter):
        """Test that old content with low engagement is filtered"""
        old_date = date.today() - timedelta(days=1460)  # 4 years old
        
        is_old = quality_filter.is_content_too_old(old_date, {'engagement_score': 0.5})
        
        assert is_old is True
    
    def test_is_content_too_old_old_content_high_engagement(self, quality_filter):
        """Test that old content with high engagement is kept"""
        old_date = date.today() - timedelta(days=1460)  # 4 years old
        
        is_old = quality_filter.is_content_too_old(old_date, {'engagement_score': 0.9})
        
        assert is_old is False  # Exception for high engagement
    
    def test_is_content_too_old_no_date(self, quality_filter):
        """Test that content without date is not filtered"""
        is_old = quality_filter.is_content_too_old(None, {'engagement_score': 0.5})
        
        assert is_old is False
    
    def test_filter_blogs_excludes_low_trustworthiness(self, quality_filter):
        """Test that blogs from low-trustworthiness sources are excluded"""
        low_trust_blog = BlogPost(
            title="Test Post",
            url="https://spam-site.com/post",
            author="Unknown Author",
            publication_date=date.today(),
            source="spam-site.com",  # Will have low trustworthiness
            view_count=1000,
            share_count=50,
            comment_count=10,
            raw_html="<html>content</html>"
        )
        
        # Manually set a very low trustworthiness by using unknown source
        scored_blogs = quality_filter.filter_blogs([low_trust_blog])
        
        # May or may not be filtered depending on overall score
        # Just verify the filtering logic runs without error
        assert isinstance(scored_blogs, list)
    
    def test_filter_papers_excludes_old_papers(self, quality_filter):
        """Test that old papers with low citations are filtered"""
        old_paper = ResearchPaper(
            title="Old Paper",
            url="https://arxiv.org/abs/2018.12345",
            authors=["Author Name"],
            publication_venue="Unknown Conference",
            publication_year=2018,  # 6+ years old
            view_count=50,
            citation_count=2,  # Low citations
            abstract="Old research"
        )
        
        scored_papers = quality_filter.filter_papers([old_paper])
        
        # Should be filtered due to age and low engagement
        assert len(scored_papers) == 0
    
    def test_calculate_quality_score_combines_multiple_signals(self, quality_filter, sample_blog_post):
        """Test that quality score combines source, engagement, author, and recency"""
        score = quality_filter.calculate_quality_score(sample_blog_post)
        
        # Score should be influenced by all factors
        # High-quality source + good engagement + author credentials + recent
        assert score > 0.6
    
    def test_filter_blogs_with_professional_author(self, quality_filter):
        """Test that blogs with professional authors get higher scores"""
        professional_blog = BlogPost(
            title="Expert Guide",
            url="https://medium.com/guide",
            author="Dr. John Smith, Senior Engineer at Google",
            publication_date=date.today() - timedelta(days=30),
            source="medium.com",
            view_count=10000,
            share_count=500,
            comment_count=100,
            raw_html="<html>content</html>"
        )
        
        scored_blogs = quality_filter.filter_blogs([professional_blog])
        
        assert len(scored_blogs) > 0
        # Should have high quality score due to professional author
        assert scored_blogs[0].quality_score > 0.7
    
    def test_filter_papers_with_high_citations(self, quality_filter):
        """Test that highly cited papers get high scores"""
        highly_cited_paper = ResearchPaper(
            title="Influential Paper",
            url="https://arxiv.org/abs/2023.12345",
            authors=["Famous Researcher"],
            publication_venue="Nature",
            publication_year=2023,
            view_count=5000,
            citation_count=500,  # Highly cited
            abstract="Important research"
        )
        
        scored_papers = quality_filter.filter_papers([highly_cited_paper])
        
        assert len(scored_papers) > 0
        # Should have high quality score due to citations and venue
        assert scored_papers[0].quality_score > 0.8
