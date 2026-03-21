"""Recommendation generator for creating ranked content recommendations per topic"""

from typing import Dict, List
from dataclasses import dataclass
from datetime import date

from ..analysis.topic_extractor import RankedTopic
from ..filtering.quality_filter import ScoredBlogPost, ScoredResearchPaper


@dataclass
class Recommendation:
    """A single content recommendation with metadata"""
    title: str
    url: str
    source: str
    author: str | None
    content_type: str  # "blog" or "paper"
    quality_score: float
    publication_date: date | None


@dataclass
class TopicRecommendations:
    """Recommendations for a single topic"""
    topic: str
    recommendations: List[Recommendation]
    total_count: int


class RecommendationGenerator:
    """Generates ranked recommendations for each study topic"""
    
    def __init__(self, max_recommendations_per_topic: int = 20):
        """
        Initialize the recommendation generator.
        
        Args:
            max_recommendations_per_topic: Maximum number of recommendations per topic
        """
        self.max_recommendations_per_topic = max_recommendations_per_topic
    
    def generate(
        self,
        topics: List[RankedTopic],
        blogs: Dict[str, List[ScoredBlogPost]],
        papers: Dict[str, List[ScoredResearchPaper]]
    ) -> Dict[str, TopicRecommendations]:
        """
        Generate ranked recommendations for multiple topics.
        
        Processes all topics and continues even if individual topics fail.
        
        Args:
            topics: List of ranked topics to generate recommendations for
            blogs: Dictionary mapping topic to list of scored blog posts
            papers: Dictionary mapping topic to list of scored research papers
            
        Returns:
            Dictionary mapping topic name to TopicRecommendations
        """
        recommendations_by_topic = {}
        
        for topic in topics:
            try:
                # Get blogs and papers for this topic
                topic_blogs = blogs.get(topic.topic, [])
                topic_papers = papers.get(topic.topic, [])
                
                # Merge and rank content
                merged_recommendations = self.merge_and_rank(topic_blogs, topic_papers)
                
                # Create TopicRecommendations object
                topic_recommendations = TopicRecommendations(
                    topic=topic.topic,
                    recommendations=merged_recommendations,
                    total_count=len(merged_recommendations)
                )
                
                recommendations_by_topic[topic.topic] = topic_recommendations
                
            except Exception as e:
                # Log error and continue with remaining topics (Requirement 11.3, 11.4)
                import logging
                logging.error(f"Failed to generate recommendations for topic '{topic.topic}': {e}")
                
                # Create empty recommendations for failed topic
                recommendations_by_topic[topic.topic] = TopicRecommendations(
                    topic=topic.topic,
                    recommendations=[],
                    total_count=0
                )
                continue
        
        return recommendations_by_topic
    
    def merge_and_rank(
        self,
        blogs: List[ScoredBlogPost],
        papers: List[ScoredResearchPaper]
    ) -> List[Recommendation]:
        """
        Merge blogs and papers into a single ranked list.
        
        Combines both content types, orders by quality score descending,
        and limits to top N recommendations.
        
        Args:
            blogs: List of scored blog posts
            papers: List of scored research papers
            
        Returns:
            List of Recommendation objects ordered by quality score
        """
        all_recommendations = []
        
        # Convert blogs to Recommendation objects
        for blog in blogs:
            recommendation = Recommendation(
                title=blog.title,
                url=blog.url,
                source=blog.source,
                author=blog.author,
                content_type="blog",
                quality_score=blog.quality_score,
                publication_date=blog.publication_date
            )
            all_recommendations.append(recommendation)
        
        # Convert papers to Recommendation objects
        for paper in papers:
            # Join authors list for display
            author_str = ", ".join(paper.authors) if paper.authors else None
            
            recommendation = Recommendation(
                title=paper.title,
                url=paper.url,
                source=paper.publication_venue or "Unknown",
                author=author_str,
                content_type="paper",
                quality_score=paper.quality_score,
                publication_date=date(paper.publication_year, 1, 1) if paper.publication_year else None
            )
            all_recommendations.append(recommendation)
        
        # Sort by quality score descending (Requirement 10.4)
        all_recommendations.sort(key=lambda r: r.quality_score, reverse=True)
        
        # Limit to top N recommendations (Requirement 10.5)
        return all_recommendations[:self.max_recommendations_per_topic]
