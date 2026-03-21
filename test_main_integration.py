#!/usr/bin/env python3
"""
Simple integration test for main.py to verify the pipeline works.
This test uses the simulator and mocks the ZenRows API to avoid external dependencies.
"""

import os
import sys
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Set up environment variables for testing
os.environ['ZENROWS_API_KEY'] = 'test_api_key'
os.environ['LOG_LEVEL'] = 'WARNING'  # Reduce log noise during testing

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import StudyContentRecommender


def test_main_pipeline_with_simulator():
    """Test the complete pipeline using simulator and mocked scraping"""
    
    print("Testing main pipeline with simulator...")
    
    # Mock the ZenRows client to avoid actual API calls
    with patch('main.ContentScraper') as MockScraper:
        # Create mock scraper instance
        mock_scraper = Mock()
        MockScraper.return_value = mock_scraper
        
        # Mock scrape_blogs to return empty list (simulating no results)
        mock_scraper.scrape_blogs.return_value = []
        
        # Mock scrape_research_papers to return empty list
        mock_scraper.scrape_research_papers.return_value = []
        
        # Create recommender with simulator
        recommender = StudyContentRecommender(
            use_simulator=True,
            date_range_days=3,
            output_file=None,
            output_format="json"
        )
        
        try:
            # Run the pipeline
            recommendations = recommender.run()
            
            # Verify we got a result (even if empty due to mocked scraping)
            assert isinstance(recommendations, dict), "Recommendations should be a dictionary"
            
            print(f"✓ Pipeline completed successfully")
            print(f"✓ Generated recommendations for {len(recommendations)} topics")
            
            return True
            
        except Exception as e:
            print(f"✗ Pipeline failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            recommender.cleanup()


def test_data_acquisition():
    """Test just the data acquisition phase"""
    
    print("\nTesting data acquisition phase...")
    
    with patch('main.ContentScraper'):
        recommender = StudyContentRecommender(
            use_simulator=True,
            date_range_days=3
        )
        
        try:
            # Test data acquisition
            tab_analytics = recommender._acquire_data()
            
            assert tab_analytics is not None, "Should return data"
            assert len(tab_analytics) > 0, "Should have at least some records"
            
            print(f"✓ Data acquisition successful: {len(tab_analytics)} records")
            
            return True
            
        except Exception as e:
            print(f"✗ Data acquisition failed: {str(e)}")
            return False
            
        finally:
            recommender.cleanup()


def test_pattern_analysis():
    """Test pattern analysis phase"""
    
    print("\nTesting pattern analysis phase...")
    
    with patch('main.ContentScraper'):
        recommender = StudyContentRecommender(
            use_simulator=True,
            date_range_days=3
        )
        
        try:
            # Get data
            tab_analytics = recommender._acquire_data()
            
            # Test pattern analysis
            pattern_result = recommender._analyze_patterns(tab_analytics)
            
            assert pattern_result is not None, "Should return pattern result"
            assert hasattr(pattern_result, 'productive_sessions'), "Should have productive_sessions"
            assert hasattr(pattern_result, 'topic_time_map'), "Should have topic_time_map"
            
            print(f"✓ Pattern analysis successful")
            print(f"  - Productive sessions: {len(pattern_result.productive_sessions)}")
            print(f"  - Topics found: {len(pattern_result.topic_time_map)}")
            
            return True
            
        except Exception as e:
            print(f"✗ Pattern analysis failed: {str(e)}")
            return False
            
        finally:
            recommender.cleanup()


if __name__ == "__main__":
    print("=" * 80)
    print("INTEGRATION TESTS FOR MAIN.PY")
    print("=" * 80)
    
    results = []
    
    # Run tests
    results.append(("Data Acquisition", test_data_acquisition()))
    results.append(("Pattern Analysis", test_pattern_analysis()))
    results.append(("Full Pipeline", test_main_pipeline_with_simulator()))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 80)
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)
