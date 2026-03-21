"""Content scraper for discovering educational blogs and research papers"""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import re

from .serper_client import SerperClient, SerperSearchResult, SerperScholarResult
from ..data.models import BlogPost, ResearchPaper
from ..utils.config import SerperConfig, AppConfig


logger = logging.getLogger(__name__)


class ContentScraper:
    """Scrapes educational content from blogs and research paper sources using Serper API"""
    
    def __init__(self, serper_api_key: str, rate_limit_delay: float = 1.0):
        """
        Initialize ContentScraper
        
        Args:
            serper_api_key: API key for Serper service
            rate_limit_delay: Delay between requests in seconds (default: 1.0)
        """
        if not serper_api_key:
            raise ValueError("Serper API key is required")
        
        self.serper_client = SerperClient(
            api_key=serper_api_key,
            base_url=SerperConfig.get_base_url(),
            timeout=SerperConfig.get_timeout(),
            retry_attempts=SerperConfig.get_retry_attempts()
        )
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: Optional[datetime] = None
        self._failed_scrapes = 0
        self._total_scrapes = 0
        
        logger.info(f"ContentScraper initialized with Serper API, rate_limit_delay={rate_limit_delay}s")
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting delay between requests"""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self._last_request_time = datetime.now()
    
    def scrape_url(self, url: str) -> Optional[str]:
        """
        DEPRECATED: Legacy method kept for backward compatibility.
        Serper API returns structured JSON data, not HTML.
        
        Args:
            url: Target URL to scrape
            
        Returns:
            None (deprecated)
        """
        logger.warning("scrape_url() is deprecated with Serper API - use search methods instead")
        return None
    
    def handle_scraping_error(self, context: str, error: Exception) -> None:
        """
        Handle and log scraping errors
        
        Args:
            context: Context description (e.g., topic name)
            error: Exception that occurred
        """
        error_type = type(error).__name__
        logger.error(f"Scraping error for {context}: {error_type} - {str(error)}")
        
        # Check if failure rate is too high
        if self._total_scrapes > 0:
            failure_rate = self._failed_scrapes / self._total_scrapes
            if failure_rate > 0.5 and self._total_scrapes >= 10:
                logger.warning(
                    f"High scraping failure rate: {failure_rate:.1%} "
                    f"({self._failed_scrapes}/{self._total_scrapes} failed)"
                )
    
    def scrape_blogs(self, topic: str, min_count: int = 10) -> List[BlogPost]:
        """
        Scrape blog posts for a given topic using Serper Google Search API
        
        Args:
            topic: Study topic to search for
            min_count: Minimum number of blog posts to retrieve
            
        Returns:
            List of BlogPost objects with metadata and engagement metrics
        """
        if not topic:
            logger.warning("Empty topic provided to scrape_blogs")
            return []
        
        logger.info(f"Scraping blogs for topic: {topic} (min_count={min_count})")
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Track scraping attempt
        self._total_scrapes += 1
        
        blogs: List[BlogPost] = []
        
        try:
            # Search Google for blog posts about the topic
            # Add keywords to focus on educational content
            search_query = f"{topic} tutorial blog article guide"
            
            logger.debug(f"Searching Google for: {search_query}")
            
            response = self.serper_client.search_google(search_query, num_results=min_count)
            
            if not response.success:
                self._failed_scrapes += 1
                self.handle_scraping_error(f"topic '{topic}'", Exception(response.error_message or "Unknown error"))
                return []
            
            # Convert search results to BlogPost objects
            for result in response.results:
                if isinstance(result, SerperSearchResult):
                    try:
                        # Extract domain as source
                        source = self._extract_domain(result.link)
                        
                        # Parse date if available
                        pub_date = self._parse_date(result.date) if result.date else None
                        
                        blog = BlogPost(
                            title=result.title,
                            url=result.link,
                            author=None,  # Not provided by Serper
                            publication_date=pub_date,
                            source=source,
                            view_count=None,  # Not provided by Serper
                            share_count=None,  # Not provided by Serper
                            comment_count=None,  # Not provided by Serper
                            raw_html=result.snippet  # Store snippet as raw_html
                        )
                        blogs.append(blog)
                        
                    except Exception as e:
                        logger.debug(f"Error creating BlogPost from result: {str(e)}")
                        continue
            
            logger.info(f"Total blogs scraped for topic '{topic}': {len(blogs)}")
            
            if len(blogs) < min_count:
                logger.warning(
                    f"Failed to meet minimum blog count for topic '{topic}': "
                    f"got {len(blogs)}, needed {min_count}"
                )
            
        except Exception as e:
            self._failed_scrapes += 1
            self.handle_scraping_error(f"topic '{topic}'", e)
            return []
        
        return blogs
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else url
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse date string to date object
        
        Args:
            date_str: Date string (e.g., "2 days ago", "Jan 15, 2024")
            
        Returns:
            date object or None if parsing fails
        """
        if not date_str:
            return None
        
        try:
            # Handle relative dates like "2 days ago"
            if 'ago' in date_str.lower():
                # For now, return today's date for recent posts
                return datetime.now().date()
            
            # Try to parse absolute dates
            # This is a simple implementation - could be enhanced with dateutil
            from datetime import datetime as dt
            
            # Try common formats
            for fmt in ['%b %d, %Y', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    return dt.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing date '{date_str}': {str(e)}")
            return None
    
    def scrape_research_papers(self, topic: str, min_count: int = 5) -> List[ResearchPaper]:
        """
        Scrape research papers for a given topic using Serper Google Scholar API
        
        Args:
            topic: Study topic to search for
            min_count: Minimum number of research papers to retrieve
            
        Returns:
            List of ResearchPaper objects with metadata and engagement metrics
        """
        if not topic:
            logger.warning("Empty topic provided to scrape_research_papers")
            return []
        
        logger.info(f"Scraping research papers for topic: {topic} (min_count={min_count})")
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Track scraping attempt
        self._total_scrapes += 1
        
        papers: List[ResearchPaper] = []
        
        try:
            # Search Google Scholar for research papers
            logger.debug(f"Searching Google Scholar for: {topic}")
            
            response = self.serper_client.search_scholar(topic, num_results=min_count)
            
            if not response.success:
                self._failed_scrapes += 1
                self.handle_scraping_error(f"topic '{topic}'", Exception(response.error_message or "Unknown error"))
                return []
            
            # Convert scholar results to ResearchPaper objects
            for result in response.results:
                if isinstance(result, SerperScholarResult):
                    try:
                        # Parse year to int
                        year = None
                        if result.year:
                            try:
                                year = int(result.year)
                            except ValueError:
                                logger.debug(f"Could not parse year: {result.year}")
                        
                        # Extract authors from publication info if available
                        authors = []
                        if result.publication:
                            # Try to extract author names (simple heuristic)
                            # Usually format is "Author1, Author2 - Publication"
                            parts = result.publication.split('-')
                            if len(parts) > 0:
                                author_part = parts[0].strip()
                                authors = [a.strip() for a in author_part.split(',')[:3]]  # Limit to 3 authors
                        
                        paper = ResearchPaper(
                            title=result.title,
                            url=result.link,
                            authors=authors,
                            publication_venue=result.publication,
                            publication_year=year,
                            view_count=None,  # Not provided by Serper
                            citation_count=result.cited_by,
                            abstract=result.snippet  # Use snippet as abstract
                        )
                        papers.append(paper)
                        
                    except Exception as e:
                        logger.debug(f"Error creating ResearchPaper from result: {str(e)}")
                        continue
            
            logger.info(f"Total papers scraped for topic '{topic}': {len(papers)}")
            
            if len(papers) < min_count:
                logger.warning(
                    f"Failed to meet minimum paper count for topic '{topic}': "
                    f"got {len(papers)}, needed {min_count}"
                )
            
        except Exception as e:
            self._failed_scrapes += 1
            self.handle_scraping_error(f"topic '{topic}'", e)
            return []
        
        return papers
