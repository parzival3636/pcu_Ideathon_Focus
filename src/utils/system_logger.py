"""System logger for comprehensive error logging and monitoring"""

import logging
import json
import time
from typing import Any, Optional
from datetime import datetime

from .config import LogConfig


class SystemLogger:
    """
    Comprehensive logging for debugging and monitoring.
    
    Provides structured logging for:
    - Phase timing (start/complete with duration)
    - Database errors with connection details
    - Scraping errors with URL and error type
    - Validation errors with record details
    - Service warnings for high failure rates
    
    Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5
    """
    
    def __init__(self, name: str = "study_content_recommender"):
        """
        Initialize the system logger.
        
        Args:
            name: Logger name (default: "study_content_recommender")
        """
        self.logger = logging.getLogger(name)
        self._configure_logger()
        self._phase_start_times = {}
    
    def _configure_logger(self) -> None:
        """Configure logger based on environment settings"""
        log_level = LogConfig.get_log_level()
        log_format = LogConfig.get_log_format()
        
        # Set log level
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        # Set formatter based on format type
        if log_format.lower() == "json":
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_phase_start(self, phase: str) -> None:
        """
        Log the start of a major processing phase.
        
        Args:
            phase: Name of the phase starting
            
        Validates: Requirement 12.4
        """
        self._phase_start_times[phase] = time.time()
        self.logger.info(
            f"Phase started: {phase}",
            extra={
                "event_type": "phase_start",
                "phase": phase,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_phase_complete(self, phase: str, duration: Optional[float] = None) -> None:
        """
        Log the completion of a major processing phase with duration.
        
        Args:
            phase: Name of the phase completing
            duration: Duration in seconds (if None, calculated from log_phase_start)
            
        Validates: Requirement 12.4
        """
        if duration is None and phase in self._phase_start_times:
            duration = time.time() - self._phase_start_times[phase]
            del self._phase_start_times[phase]
        
        self.logger.info(
            f"Phase completed: {phase} (duration: {duration:.2f}s)",
            extra={
                "event_type": "phase_complete",
                "phase": phase,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_database_error(self, error: Exception, connection_details: str) -> None:
        """
        Log database connection or query errors with connection details.
        
        Args:
            error: The exception that occurred
            connection_details: Connection details (sanitized, no passwords)
            
        Validates: Requirement 12.1
        """
        self.logger.error(
            f"Database error: {str(error)}",
            extra={
                "event_type": "database_error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "connection_details": connection_details,
                "timestamp": datetime.now().isoformat()
            },
            exc_info=True
        )
    
    def log_scraping_error(self, url: str, error_type: str, error: Exception) -> None:
        """
        Log web scraping errors with URL and error type.
        
        Args:
            url: The URL that failed to scrape
            error_type: Type/category of the error (e.g., "timeout", "http_error")
            error: The exception that occurred
            
        Validates: Requirement 12.2
        """
        self.logger.warning(
            f"Scraping error for {url}: {error_type} - {str(error)}",
            extra={
                "event_type": "scraping_error",
                "url": url,
                "error_type": error_type,
                "error_message": str(error),
                "exception_type": type(error).__name__,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_validation_error(self, record: Any, error: str) -> None:
        """
        Log data validation errors with record details.
        
        Args:
            record: The invalid record (will be converted to string)
            error: Description of the validation error
            
        Validates: Requirement 12.3
        """
        # Convert record to string representation, truncate if too long
        record_str = str(record)
        if len(record_str) > 500:
            record_str = record_str[:500] + "..."
        
        self.logger.warning(
            f"Validation error: {error}",
            extra={
                "event_type": "validation_error",
                "error": error,
                "record": record_str,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_service_warning(self, service: str, failure_rate: float) -> None:
        """
        Log warnings about high service failure rates.
        
        Args:
            service: Name of the service experiencing failures
            failure_rate: Failure rate as a decimal (e.g., 0.6 for 60%)
            
        Validates: Requirement 12.5
        """
        percentage = failure_rate * 100
        self.logger.warning(
            f"High failure rate for {service}: {percentage:.1f}%",
            extra={
                "event_type": "service_warning",
                "service": service,
                "failure_rate": failure_rate,
                "failure_percentage": percentage,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message with optional extra fields"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message with optional extra fields"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message with optional extra fields"""
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message with optional extra fields"""
        self.logger.debug(message, extra=kwargs)


class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON for easy parsing and analysis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        
        # Add all extra attributes
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info"
            ]:
                log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


# Global logger instance
_global_logger: Optional[SystemLogger] = None


def get_logger(name: str = "study_content_recommender") -> SystemLogger:
    """
    Get or create a global logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        SystemLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = SystemLogger(name)
    return _global_logger
