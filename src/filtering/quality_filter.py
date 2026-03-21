"""Quality filtering for content based on engagement metrics and source trustworthiness"""

from datetime import date, datetime
from typing import List, Dict, Union
from dataclasses import dataclass

from ..data.models import BlogPost, ResearchPaper
from .professional_source_evaluator import ProfessionalSourceEvaluator


@dataclass
class ScoredBlogPost:
    """Blog post with quality scoring metrics"""
    # Original blog post fields
    title: str
    url: str
    author: str | None
    publication_date: date | None
    source: str
    view_count: int | None
    share_count: int | None
    comment_count: int | None
    raw_html: str
    
    # Quality scoring fields
    quality_score: float
    source_trustworthiness: float
    engagement_score: float


@dataclass
class ScoredResearchPaper:
    """Research paper with quality scoring metrics"""
    # Original research paper fields
    title: str
    url: str
    authors: List[str]
    publication_venue: str | None
    publication_year: int | None
    view_count: int | None
    citation_count: int | None
    abstract: str | None
    
    # Quality scoring fields
    quality_score: float
    venue_reputation: float
    citation_score: float


class QualityFilter:
    """Evaluates and filters content based on quality metrics"""
    
    def __init__(self, min_quality_score: float = 0.6, max_age_years: int = 3):
        """
        Initialize the quality filter.
        
        Args:
            min_quality_score: Minimum quality score threshold (0.0 to 1.0)
            max_age_years: Maximum age in years for content (unless high engagement)
        """
        self.min_quality_score = min_quality_score
        self.max_age_years = max_age_years
        self.professional_evaluator = ProfessionalSourceEvaluator()
    
    def filter_blogs(self, blogs: List[BlogPost]) -> List[ScoredBlogPost]:
        """
        Filter and score blog posts based on quality metrics.
        
        Args:
            blogs: List of blog posts to filter
            
        Returns:
            List of scored blog posts that meet quality threshold
        """
        scored_blogs = []
        
        for blog in blogs:
            # Calculate quality metrics
            source_trustworthiness = self.evaluate_source_trustworthiness(blog.source)
            
            # Skip low-trustworthiness sources (Requirement 8.3)
            if source_trustworthiness < 0.4:
                continue
            
            # Calculate engagement score
            engagement_score = self._calculate_blog_engagement_score(blog)
            
            # Check if content is too old (Requirement 8.5)
            if self.is_content_too_old(
                blog.publication_date,
                {'engagement_score': engagement_score}
            ):
                continue
            
            # Calculate overall quality score (Requirement 8.2)
            quality_score = self.calculate_quality_score(blog)
            
            # Ensure minimum quality threshold (Requirement 8.6)
            if quality_score < self.min_quality_score:
                continue
            
            # Create scored blog post
            scored_blog = ScoredBlogPost(
                title=blog.title,
                url=blog.url,
                author=blog.author,
                publication_date=blog.publication_date,
                source=blog.source,
                view_count=blog.view_count,
                share_count=blog.share_count,
                comment_count=blog.comment_count,
                raw_html=blog.raw_html,
                quality_score=quality_score,
                source_trustworthiness=source_trustworthiness,
                engagement_score=engagement_score
            )
            
            scored_blogs.append(scored_blog)
        
        # Fallback: If no blogs passed filter, return top 10 by quality score
        if not scored_blogs and blogs:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"No blogs passed quality filter, returning top 10 by score")
            
            all_scored = []
            for blog in blogs:
                # Score all blogs with relaxed criteria
                source_trustworthiness = self.evaluate_source_trustworthiness(blog.source)
                engagement_score = self._calculate_blog_engagement_score(blog)
                quality_score = self.calculate_quality_score(blog)
                
                scored_blog = ScoredBlogPost(
                    title=blog.title,
                    url=blog.url,
                    author=blog.author,
                    publication_date=blog.publication_date,
                    source=blog.source,
                    view_count=blog.view_count,
                    share_count=blog.share_count,
                    comment_count=blog.comment_count,
                    raw_html=blog.raw_html,
                    quality_score=quality_score,
                    source_trustworthiness=source_trustworthiness,
                    engagement_score=engagement_score
                )
                all_scored.append(scored_blog)
            
            # Sort by quality_score and return top 10
            all_scored.sort(key=lambda x: x.quality_score, reverse=True)
            return all_scored[:10]
        
        return scored_blogs
    
    def filter_papers(self, papers: List[ResearchPaper]) -> List[ScoredResearchPaper]:
        """
        Filter and score research papers based on quality metrics.
        
        Args:
            papers: List of research papers to filter
            
        Returns:
            List of scored research papers that meet quality threshold
        """
        scored_papers = []
        
        for paper in papers:
            # Calculate venue reputation
            venue_reputation = self._calculate_venue_reputation(paper.publication_venue)
            
            # Skip low-reputation venues
            if venue_reputation < 0.4:
                continue
            
            # Calculate citation score
            citation_score = self._calculate_citation_score(paper)
            
            # Check if content is too old (Requirement 8.5)
            if paper.publication_year:
                paper_date = date(paper.publication_year, 1, 1)
                if self.is_content_too_old(
                    paper_date,
                    {'citation_score': citation_score}
                ):
                    continue
            
            # Calculate overall quality score (Requirement 8.2)
            quality_score = self.calculate_quality_score(paper)
            
            # Ensure minimum quality threshold (Requirement 8.6)
            if quality_score < self.min_quality_score:
                continue
            
            # Create scored research paper
            scored_paper = ScoredResearchPaper(
                title=paper.title,
                url=paper.url,
                authors=paper.authors,
                publication_venue=paper.publication_venue,
                publication_year=paper.publication_year,
                view_count=paper.view_count,
                citation_count=paper.citation_count,
                abstract=paper.abstract,
                quality_score=quality_score,
                venue_reputation=venue_reputation,
                citation_score=citation_score
            )
            
            scored_papers.append(scored_paper)
        
        # Fallback: If no papers passed filter, return top 10 by quality score
        if not scored_papers and papers:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"No papers passed quality filter, returning top 10 by score")
            
            all_scored = []
            for paper in papers:
                # Score all papers with relaxed criteria
                venue_reputation = self._calculate_venue_reputation(paper.publication_venue)
                citation_score = self._calculate_citation_score(paper)
                quality_score = self.calculate_quality_score(paper)
                
                scored_paper = ScoredResearchPaper(
                    title=paper.title,
                    url=paper.url,
                    authors=paper.authors,
                    publication_venue=paper.publication_venue,
                    publication_year=paper.publication_year,
                    view_count=paper.view_count,
                    citation_count=paper.citation_count,
                    abstract=paper.abstract,
                    quality_score=quality_score,
                    venue_reputation=venue_reputation,
                    citation_score=citation_score
                )
                all_scored.append(scored_paper)
            
            # Sort by quality_score and return top 10
            all_scored.sort(key=lambda x: x.quality_score, reverse=True)
            return all_scored[:10]
        
        return scored_papers
    
    def calculate_quality_score(self, content: Union[BlogPost, ResearchPaper]) -> float:
        """
        Calculate overall quality score combining multiple signals.
        
        Combines:
        - Source trustworthiness/venue reputation
        - Engagement metrics (views, citations, shares, comments)
        - Author credentials (for blogs)
        - Recency (newer content gets slight boost)
        
        Args:
            content: Blog post or research paper to score
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if isinstance(content, BlogPost):
            return self._calculate_blog_quality_score(content)
        elif isinstance(content, ResearchPaper):
            return self._calculate_paper_quality_score(content)
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")
    
    def _calculate_blog_quality_score(self, blog: BlogPost) -> float:
        """Calculate quality score for a blog post"""
        # Source trustworthiness (40% weight)
        source_score = self.evaluate_source_trustworthiness(blog.source)
        
        # Engagement metrics (35% weight)
        engagement_score = self._calculate_blog_engagement_score(blog)
        
        # Author credentials (20% weight) - Requirement 8.4, 9.1, 9.2
        author_score = 0.5  # Default
        if blog.author:
            author_score = self.professional_evaluator.evaluate_author_credentials(
                blog.author, blog.source
            )
        
        # Recency bonus (5% weight)
        recency_score = self._calculate_recency_score(blog.publication_date)
        
        # Weighted combination
        quality_score = (
            source_score * 0.40 +
            engagement_score * 0.35 +
            author_score * 0.20 +
            recency_score * 0.05
        )
        
        return min(quality_score, 1.0)
    
    def _calculate_paper_quality_score(self, paper: ResearchPaper) -> float:
        """Calculate quality score for a research paper"""
        # Venue reputation (40% weight)
        venue_score = self._calculate_venue_reputation(paper.publication_venue)
        
        # Citation metrics (40% weight)
        citation_score = self._calculate_citation_score(paper)
        
        # View count (15% weight)
        view_score = self._normalize_view_count(paper.view_count, max_views=10000)
        
        # Recency bonus (5% weight)
        recency_score = 0.5
        if paper.publication_year:
            paper_date = date(paper.publication_year, 1, 1)
            recency_score = self._calculate_recency_score(paper_date)
        
        # Weighted combination
        quality_score = (
            venue_score * 0.40 +
            citation_score * 0.40 +
            view_score * 0.15 +
            recency_score * 0.05
        )
        
        return min(quality_score, 1.0)
    
    def evaluate_source_trustworthiness(self, source: str) -> float:
        """
        Evaluate source trustworthiness using professional evaluator.
        
        Args:
            source: Source domain/hostname
            
        Returns:
            Trustworthiness score between 0.0 and 1.0
        """
        # Get base reputation from professional evaluator
        reputation = self.professional_evaluator.get_source_reputation(source)
        
        # Boost score if source has editorial standards (Requirement 9.3)
        if self.professional_evaluator.evaluate_editorial_standards(source):
            reputation = min(reputation * 1.1, 1.0)
        
        return reputation
    
    def is_content_too_old(
        self,
        publication_date: date | None,
        engagement_metrics: Dict
    ) -> bool:
        """
        Check if content is too old, with exception for high engagement.
        
        Content older than max_age_years is excluded unless it has
        exceptionally high engagement metrics.
        
        Args:
            publication_date: Date of publication
            engagement_metrics: Dict with engagement scores
            
        Returns:
            True if content should be excluded due to age, False otherwise
        """
        # If no publication date, can't determine age
        if not publication_date:
            return False
        
        # Calculate age in years
        today = date.today()
        age_years = (today - publication_date).days / 365.25
        
        # Content within max age is fine
        if age_years <= self.max_age_years:
            return False
        
        # Check for exceptionally high engagement (Requirement 8.5)
        # Exception threshold: engagement score >= 0.85
        engagement_score = engagement_metrics.get('engagement_score', 0.0)
        citation_score = engagement_metrics.get('citation_score', 0.0)
        
        # Use whichever score is available
        max_engagement = max(engagement_score, citation_score)
        
        # High engagement content gets exception
        if max_engagement >= 0.85:
            return False
        
        # Otherwise, content is too old
        return True
    
    def _calculate_blog_engagement_score(self, blog: BlogPost) -> float:
        """Calculate engagement score from blog metrics"""
        # Normalize each metric
        view_score = self._normalize_view_count(blog.view_count, max_views=50000)
        share_score = self._normalize_count(blog.share_count, max_count=1000)
        comment_score = self._normalize_count(blog.comment_count, max_count=500)
        
        # Weighted combination (views most important)
        engagement_score = (
            view_score * 0.5 +
            share_score * 0.3 +
            comment_score * 0.2
        )
        
        return engagement_score
    
    def _calculate_citation_score(self, paper: ResearchPaper) -> float:
        """Calculate citation score for research paper"""
        if not paper.citation_count:
            return 0.3  # Default for papers without citation data
        
        # Normalize citation count (highly cited papers can have 1000+ citations)
        # Use logarithmic scale for citations
        import math
        normalized = math.log10(paper.citation_count + 1) / math.log10(1001)
        
        return min(normalized, 1.0)
    
    def _calculate_venue_reputation(self, venue: str | None) -> float:
        """Calculate reputation score for publication venue"""
        if not venue:
            return 0.5  # Default for unknown venues
        
        venue_lower = venue.lower()
        
        # Top-tier venues
        top_venues = [
            'nature', 'science', 'cell', 'lancet',
            'ieee', 'acm', 'springer', 'elsevier',
            'neurips', 'icml', 'cvpr', 'iccv', 'aaai',
            'sigmod', 'vldb', 'kdd', 'www'
        ]
        
        for top_venue in top_venues:
            if top_venue in venue_lower:
                return 0.95
        
        # Conference/journal indicators
        if any(indicator in venue_lower for indicator in ['conference', 'journal', 'proceedings', 'transactions']):
            return 0.75
        
        # Workshop/symposium
        if any(indicator in venue_lower for indicator in ['workshop', 'symposium']):
            return 0.65
        
        # Default
        return 0.5
    
    def _normalize_view_count(self, view_count: int | None, max_views: int) -> float:
        """Normalize view count to 0.0-1.0 range"""
        if not view_count or view_count <= 0:
            return 0.2  # Default for content without view data
        
        # Use logarithmic scale for views
        import math
        normalized = math.log10(view_count + 1) / math.log10(max_views + 1)
        
        return min(normalized, 1.0)
    
    def _normalize_count(self, count: int | None, max_count: int) -> float:
        """Normalize a count metric to 0.0-1.0 range"""
        if not count or count <= 0:
            return 0.1  # Default for missing data
        
        normalized = count / max_count
        return min(normalized, 1.0)
    
    def _calculate_recency_score(self, publication_date: date | None) -> float:
        """Calculate recency score (newer content gets higher score)"""
        if not publication_date:
            return 0.5  # Default for unknown dates
        
        today = date.today()
        age_days = (today - publication_date).days
        
        # Content less than 6 months old gets full score
        if age_days < 180:
            return 1.0
        
        # Linear decay over 3 years
        age_years = age_days / 365.25
        if age_years <= 3:
            return 1.0 - (age_years / 3) * 0.5  # Decays from 1.0 to 0.5
        
        # Older content gets minimum score
        return 0.3
