"""Configuration management using environment variables"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseConfig:
    """PostgreSQL database configuration"""
    
    @staticmethod
    def get_connection_string() -> str:
        """Build PostgreSQL connection string from environment variables"""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "study_analytics")
        user = os.getenv("POSTGRES_USER", "app_user")
        password = os.getenv("POSTGRES_PASSWORD", "")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    @staticmethod
    def get_connection_params() -> dict:
        """Get database connection parameters as dictionary"""
        return {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "study_analytics"),
            "user": os.getenv("POSTGRES_USER", "app_user"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "sslmode": os.getenv("POSTGRES_SSLMODE", "prefer")
        }


class SerperConfig:
    """Serper API configuration"""
    
    @staticmethod
    def get_api_key() -> Optional[str]:
        """Get Serper API key from environment"""
        return os.getenv("SERPER_API_KEY")
    
    @staticmethod
    def get_base_url() -> str:
        """Get Serper API base URL"""
        return os.getenv("SERPER_BASE_URL", "https://google.serper.dev")
    
    @staticmethod
    def get_timeout() -> int:
        """Get request timeout in seconds"""
        return int(os.getenv("SERPER_TIMEOUT", "30"))
    
    @staticmethod
    def get_retry_attempts() -> int:
        """Get number of retry attempts for failed requests"""
        return int(os.getenv("SERPER_RETRY_ATTEMPTS", "3"))


class ZenRowsConfig:
    """ZenRows API configuration (DEPRECATED - kept for reference)"""
    
    @staticmethod
    def get_api_key() -> Optional[str]:
        """Get ZenRows API key from environment"""
        return os.getenv("ZENROWS_API_KEY")
    
    @staticmethod
    def get_base_url() -> str:
        """Get ZenRows API base URL"""
        return os.getenv("ZENROWS_BASE_URL", "https://api.zenrows.com/v1/")
    
    @staticmethod
    def get_timeout() -> int:
        """Get request timeout in seconds"""
        return int(os.getenv("ZENROWS_TIMEOUT", "30"))
    
    @staticmethod
    def get_retry_attempts() -> int:
        """Get number of retry attempts for failed requests"""
        return int(os.getenv("ZENROWS_RETRY_ATTEMPTS", "3"))
    
    @staticmethod
    def get_rate_limit_delay() -> float:
        """Get delay between requests in seconds"""
        return float(os.getenv("ZENROWS_RATE_LIMIT_DELAY", "1.0"))


class AppConfig:
    """Application-level configuration"""
    
    @staticmethod
    def get_min_productive_sessions() -> int:
        """Minimum productive sessions required for pattern analysis"""
        return int(os.getenv("MIN_PRODUCTIVE_SESSIONS", "10"))
    
    @staticmethod
    def get_top_n_topics() -> int:
        """Number of top topics to extract"""
        return int(os.getenv("TOP_N_TOPICS", "5"))
    
    @staticmethod
    def get_min_blogs_per_topic() -> int:
        """Minimum number of blogs to retrieve per topic"""
        return int(os.getenv("MIN_BLOGS_PER_TOPIC", "10"))
    
    @staticmethod
    def get_min_papers_per_topic() -> int:
        """Minimum number of research papers to retrieve per topic"""
        return int(os.getenv("MIN_PAPERS_PER_TOPIC", "5"))
    
    @staticmethod
    def get_max_recommendations_per_topic() -> int:
        """Maximum recommendations to return per topic"""
        return int(os.getenv("MAX_RECOMMENDATIONS_PER_TOPIC", "20"))
    
    @staticmethod
    def get_min_quality_score() -> float:
        """Minimum quality score threshold for content"""
        return float(os.getenv("MIN_QUALITY_SCORE", "0.6"))
    
    @staticmethod
    def get_max_content_age_years() -> int:
        """Maximum age of content in years"""
        return int(os.getenv("MAX_CONTENT_AGE_YEARS", "3"))


class LogConfig:
    """Logging configuration"""
    
    @staticmethod
    def get_log_level() -> str:
        """Get logging level"""
        return os.getenv("LOG_LEVEL", "INFO")
    
    @staticmethod
    def get_log_format() -> str:
        """Get log format (json or text)"""
        return os.getenv("LOG_FORMAT", "json")
