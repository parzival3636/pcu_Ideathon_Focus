#!/usr/bin/env python3
"""
Main application orchestration for the Intelligent Study Content Recommendation System.

This module orchestrates the complete pipeline:
1. Data Acquisition - Connect to database or generate simulated data
2. Pattern Analysis - Identify study patterns and extract topics
3. Content Scraping - Discover blogs and research papers using ZenRows
4. Quality Filtering - Filter content by quality metrics
5. Recommendation Generation - Generate and output ranked recommendations

Validates: All requirements (1-12)
"""

import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.data.database_connector import DatabaseConnector
from src.data.database_simulator import DatabaseSimulator
from src.analysis.pattern_analyzer import PatternAnalyzer
from src.analysis.topic_extractor import TopicExtractor
from src.scraping.content_scraper import ContentScraper
from src.filtering.quality_filter import QualityFilter
from src.output.recommendation_generator import RecommendationGenerator
from src.output.output_formatter import OutputFormatter
from src.utils.config import DatabaseConfig, SerperConfig, AppConfig
from src.utils.system_logger import get_logger


# Initialize logger
logger = get_logger()


class StudyContentRecommender:
    """Main application class orchestrating the recommendation pipeline"""
    
    def __init__(
        self,
        use_simulator: bool = False,
        date_range_days: int = 7,
        output_file: Optional[str] = None,
        output_format: str = "json"
    ):
        """
        Initialize the recommendation system.
        
        Args:
            use_simulator: Force use of database simulator instead of real database
            date_range_days: Number of days of data to analyze (default: 7)
            output_file: Optional file path to save recommendations
            output_format: Output format - "json" or "markdown" (default: "json")
        """
        self.use_simulator = use_simulator
        self.date_range_days = date_range_days
        self.output_file = output_file
        self.output_format = output_format
        
        # Initialize components
        self.db_connector: Optional[DatabaseConnector] = None
        self.db_simulator: Optional[DatabaseSimulator] = None
        self.pattern_analyzer = PatternAnalyzer(
            min_productive_sessions=AppConfig.get_min_productive_sessions()
        )
        self.topic_extractor = TopicExtractor(
            top_n=AppConfig.get_top_n_topics()
        )
        
        # Initialize scraper if API key is available
        serper_api_key = SerperConfig.get_api_key()
        if not serper_api_key:
            logger.error("Serper API key not found in environment variables")
            raise ValueError("SERPER_API_KEY environment variable is required")
        
        self.content_scraper = ContentScraper(
            serper_api_key=serper_api_key,
            rate_limit_delay=1.0  # Serper doesn't need rate limiting like ZenRows
        )
        
        self.quality_filter = QualityFilter(
            min_quality_score=AppConfig.get_min_quality_score(),
            max_age_years=AppConfig.get_max_content_age_years()
        )
        
        self.recommendation_generator = RecommendationGenerator(
            max_recommendations_per_topic=AppConfig.get_max_recommendations_per_topic()
        )
    
    def run(self) -> Dict:
        """
        Execute the complete recommendation pipeline.
        
        Returns:
            Dictionary mapping topic to TopicRecommendations
        """
        logger.info("=" * 80)
        logger.info("Starting Intelligent Study Content Recommendation System")
        logger.info("=" * 80)
        
        try:
            # Phase 1: Data Acquisition
            tab_analytics = self._acquire_data()
            
            if not tab_analytics:
                logger.error("No data available for analysis")
                return {}
            
            # Phase 2: Pattern Analysis
            pattern_result = self._analyze_patterns(tab_analytics)
            
            if not pattern_result.sufficient_data:
                logger.warning(
                    f"Insufficient productive sessions: {len(pattern_result.productive_sessions)} "
                    f"(minimum: {self.pattern_analyzer.min_productive_sessions})"
                )
                logger.info("Continuing with available data...")
            
            # Phase 3: Topic Extraction
            topic_result = self._extract_topics(pattern_result.productive_sessions)
            
            if not topic_result.top_topics:
                logger.warning("No topics extracted from browsing data")
                return {}
            
            # Phase 4: Content Scraping (multi-topic handling)
            blogs_by_topic, papers_by_topic = self._scrape_content(topic_result.top_topics)
            
            # Phase 5: Quality Filtering
            filtered_blogs, filtered_papers = self._filter_content(blogs_by_topic, papers_by_topic)
            
            # Phase 6: Recommendation Generation
            recommendations = self._generate_recommendations(
                topic_result.top_topics,
                filtered_blogs,
                filtered_papers
            )
            
            # Phase 7: Output
            self._output_recommendations(recommendations)
            
            logger.info("=" * 80)
            logger.info("Recommendation pipeline completed successfully")
            logger.info("=" * 80)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Fatal error in recommendation pipeline: {str(e)}", exc_info=True)
            raise
    
    def _acquire_data(self):
        """
        Phase 1: Data Acquisition
        
        Attempts to connect to PostgreSQL database. Falls back to simulator
        if connection fails or if use_simulator is True.
        
        Validates: Requirements 1.1-1.4, 2.1-2.5, 12.1
        """
        logger.log_phase_start("Data Acquisition")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.date_range_days)
        
        logger.info(f"Analyzing data from {start_date.date()} to {end_date.date()}")
        
        tab_analytics = []
        
        # Try database connection unless simulator is forced
        if not self.use_simulator:
            try:
                logger.info("Attempting to connect to PostgreSQL database...")
                
                db_params = DatabaseConfig.get_connection_params()
                # Sanitize connection details for logging (remove password)
                safe_params = {k: v for k, v in db_params.items() if k != 'password'}
                safe_params['password'] = '***'
                
                self.db_connector = DatabaseConnector(db_params)
                
                if self.db_connector.connect():
                    logger.info("Database connection successful")
                    
                    # Query tab_analytics
                    tab_analytics = self.db_connector.query_tab_analytics(start_date, end_date)
                    
                    if tab_analytics:
                        logger.info(f"Retrieved {len(tab_analytics)} records from database")
                    else:
                        logger.warning("No records found in database, falling back to simulator")
                        self.use_simulator = True
                else:
                    logger.warning("Database connection failed, falling back to simulator")
                    self.use_simulator = True
                    
            except Exception as e:
                logger.log_database_error(e, str(safe_params))
                logger.warning("Falling back to database simulator")
                self.use_simulator = True
        
        # Use simulator if needed
        if self.use_simulator:
            logger.info("Using database simulator to generate test data")
            
            self.db_simulator = DatabaseSimulator(seed=42)
            
            # Generate realistic number of records (50-100 per day)
            num_records = self.date_range_days * 75
            
            tab_analytics = self.db_simulator.generate_tab_analytics(
                num_records=num_records,
                date_range=(start_date, end_date)
            )
            
            logger.info(f"Generated {len(tab_analytics)} simulated records")
        
        logger.log_phase_complete("Data Acquisition")
        return tab_analytics
    
    def _analyze_patterns(self, tab_analytics):
        """
        Phase 2: Pattern Analysis
        
        Identifies study patterns from browsing sessions.
        
        Validates: Requirements 3.1-3.5
        """
        logger.log_phase_start("Pattern Analysis")
        
        try:
            pattern_result = self.pattern_analyzer.analyze(tab_analytics)
            
            logger.info(f"Productive sessions: {len(pattern_result.productive_sessions)}")
            logger.info(f"Total productive time: {pattern_result.total_productive_time} seconds")
            logger.info(f"Unique topics: {len(pattern_result.topic_time_map)}")
            logger.info(f"Peak study hours: {pattern_result.peak_study_hours[:5]}")
            
            logger.log_phase_complete("Pattern Analysis")
            return pattern_result
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {str(e)}", exc_info=True)
            raise
    
    def _extract_topics(self, productive_sessions):
        """
        Phase 3: Topic Extraction
        
        Extracts and ranks study topics from productive sessions.
        
        Validates: Requirements 4.1-4.6
        """
        logger.log_phase_start("Topic Extraction")
        
        try:
            topic_result = self.topic_extractor.extract_topics(productive_sessions)
            
            logger.info(f"Total topics extracted: {len(topic_result.ranked_topics)}")
            logger.info(f"Top {len(topic_result.top_topics)} topics for recommendations:")
            
            for topic in topic_result.top_topics:
                logger.info(
                    f"  {topic.rank}. {topic.topic} "
                    f"(frequency: {topic.weekly_frequency}, time: {topic.total_time_seconds}s)"
                )
            
            logger.log_phase_complete("Topic Extraction")
            return topic_result
            
        except Exception as e:
            logger.error(f"Error in topic extraction: {str(e)}", exc_info=True)
            raise
    
    def _scrape_content(self, topics):
        """
        Phase 4: Content Scraping
        
        Scrapes blogs and research papers for each topic using Serper API.
        Continues processing all topics even if individual topics fail.
        
        Validates: Requirements 5.1-5.5, 6.1-6.5, 7.1-7.5, 11.1-11.4
        """
        logger.log_phase_start("Content Scraping")
        
        blogs_by_topic = {}
        papers_by_topic = {}
        
        min_blogs = AppConfig.get_min_blogs_per_topic()
        min_papers = AppConfig.get_min_papers_per_topic()
        
        # Process each topic
        for topic in topics:
            topic_name = topic.topic
            logger.info(f"Scraping content for topic: {topic_name}")
            
            try:
                # Scrape blogs
                logger.info(f"  Scraping blogs (min: {min_blogs})...")
                blogs = self.content_scraper.scrape_blogs(topic_name, min_count=min_blogs)
                blogs_by_topic[topic_name] = blogs
                logger.info(f"  Retrieved {len(blogs)} blogs")
                
                # Scrape research papers
                logger.info(f"  Scraping research papers (min: {min_papers})...")
                papers = self.content_scraper.scrape_research_papers(topic_name, min_count=min_papers)
                papers_by_topic[topic_name] = papers
                logger.info(f"  Retrieved {len(papers)} papers")
                
                # Log if topic yielded no results (Requirement 11.4)
                if not blogs and not papers:
                    logger.warning(f"Topic '{topic_name}' yielded no results")
                
            except Exception as e:
                # Log error and continue with remaining topics (Requirement 11.3)
                logger.error(f"Error scraping content for topic '{topic_name}': {str(e)}")
                blogs_by_topic[topic_name] = []
                papers_by_topic[topic_name] = []
                continue
        
        # Calculate total scraping statistics
        total_blogs = sum(len(blogs) for blogs in blogs_by_topic.values())
        total_papers = sum(len(papers) for papers in papers_by_topic.values())
        
        logger.info(f"Total content scraped: {total_blogs} blogs, {total_papers} papers")
        
        logger.log_phase_complete("Content Scraping")
        return blogs_by_topic, papers_by_topic
    
    def _filter_content(self, blogs_by_topic, papers_by_topic):
        """
        Phase 5: Quality Filtering
        
        Filters content based on quality metrics, source trustworthiness,
        and professional source prioritization.
        
        Validates: Requirements 8.1-8.6, 9.1-9.4
        """
        logger.log_phase_start("Quality Filtering")
        
        filtered_blogs = {}
        filtered_papers = {}
        
        # Filter blogs for each topic
        for topic, blogs in blogs_by_topic.items():
            try:
                scored_blogs = self.quality_filter.filter_blogs(blogs)
                filtered_blogs[topic] = scored_blogs
                
                logger.info(
                    f"Topic '{topic}': {len(scored_blogs)}/{len(blogs)} blogs passed quality filter"
                )
                
            except Exception as e:
                logger.error(f"Error filtering blogs for topic '{topic}': {str(e)}")
                filtered_blogs[topic] = []
        
        # Filter papers for each topic
        for topic, papers in papers_by_topic.items():
            try:
                scored_papers = self.quality_filter.filter_papers(papers)
                filtered_papers[topic] = scored_papers
                
                logger.info(
                    f"Topic '{topic}': {len(scored_papers)}/{len(papers)} papers passed quality filter"
                )
                
            except Exception as e:
                logger.error(f"Error filtering papers for topic '{topic}': {str(e)}")
                filtered_papers[topic] = []
        
        # Calculate total filtering statistics
        total_filtered_blogs = sum(len(blogs) for blogs in filtered_blogs.values())
        total_filtered_papers = sum(len(papers) for papers in filtered_papers.values())
        
        logger.info(
            f"Quality filtering complete: {total_filtered_blogs} blogs, "
            f"{total_filtered_papers} papers passed"
        )
        
        logger.log_phase_complete("Quality Filtering")
        return filtered_blogs, filtered_papers
    
    def _generate_recommendations(self, topics, filtered_blogs, filtered_papers):
        """
        Phase 6: Recommendation Generation
        
        Generates ranked recommendations for each topic by merging and
        ranking blogs and papers by quality score.
        
        Validates: Requirements 10.1-10.6, 11.1-11.4
        """
        logger.log_phase_start("Recommendation Generation")
        
        try:
            recommendations = self.recommendation_generator.generate(
                topics=topics,
                blogs=filtered_blogs,
                papers=filtered_papers
            )
            
            # Log recommendation statistics
            for topic_name, topic_recs in recommendations.items():
                logger.info(
                    f"Topic '{topic_name}': {topic_recs.total_count} recommendations generated"
                )
            
            total_recommendations = sum(
                topic_recs.total_count for topic_recs in recommendations.values()
            )
            
            logger.info(f"Total recommendations generated: {total_recommendations}")
            
            logger.log_phase_complete("Recommendation Generation")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
            raise
    
    def _output_recommendations(self, recommendations):
        """
        Phase 7: Output
        
        Formats and outputs recommendations in the specified format.
        Optionally saves to file.
        
        Validates: Requirement 10.6
        """
        logger.log_phase_start("Output")
        
        try:
            # Format recommendations
            if self.output_format == "json":
                output = OutputFormatter.format_json(recommendations)
            elif self.output_format == "markdown":
                output = OutputFormatter.format_markdown(recommendations)
            else:
                raise ValueError(f"Unsupported output format: {self.output_format}")
            
            # Print to console
            print("\n" + "=" * 80)
            print("RECOMMENDATIONS")
            print("=" * 80)
            print(output)
            print("=" * 80 + "\n")
            
            # Save to file if specified
            if self.output_file:
                OutputFormatter.save_to_file(
                    recommendations,
                    self.output_file,
                    self.output_format
                )
                logger.info(f"Recommendations saved to: {self.output_file}")
            
            logger.log_phase_complete("Output")
            
        except Exception as e:
            logger.error(f"Error outputting recommendations: {str(e)}", exc_info=True)
            raise
    
    def cleanup(self):
        """Clean up resources (close database connections, etc.)"""
        if self.db_connector:
            try:
                self.db_connector.disconnect()
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing database connection: {str(e)}")


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Intelligent Study Content Recommendation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with database connection
  python main.py

  # Run with simulator (for testing)
  python main.py --simulator

  # Analyze last 14 days of data
  python main.py --days 14

  # Save output to file
  python main.py --output recommendations.json

  # Generate markdown output
  python main.py --output recommendations.md --format markdown
        """
    )
    
    parser.add_argument(
        '--simulator',
        action='store_true',
        help='Use database simulator instead of real database'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days of data to analyze (default: 7)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (optional)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'markdown'],
        default='json',
        help='Output format (default: json)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the application"""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Create recommender instance
    recommender = StudyContentRecommender(
        use_simulator=args.simulator,
        date_range_days=args.days,
        output_file=args.output,
        output_format=args.format
    )
    
    try:
        # Run the recommendation pipeline
        recommendations = recommender.run()
        
        # Exit with success if we got recommendations
        if recommendations:
            sys.exit(0)
        else:
            logger.warning("No recommendations generated")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Application failed: {str(e)}", exc_info=True)
        sys.exit(1)
        
    finally:
        # Clean up resources
        recommender.cleanup()


if __name__ == "__main__":
    main()
