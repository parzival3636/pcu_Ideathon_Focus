"""Database connector for PostgreSQL operations"""

import logging
from datetime import datetime
from typing import List, Optional
import psycopg2
from psycopg2 import sql, OperationalError, DatabaseError
from psycopg2.extras import RealDictCursor

from .models import TabAnalyticsRecord, ContentPreferenceRecord

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Manages PostgreSQL connections and query execution"""
    
    def __init__(self, connection_params: dict):
        """
        Initialize database connector with connection parameters
        
        Args:
            connection_params: Dictionary with keys: host, port, database, user, password, sslmode
        """
        self.connection_params = connection_params
        self.connection: Optional[psycopg2.extensions.connection] = None
        self._is_connected = False
    
    def connect(self) -> bool:
        """
        Establish connection to PostgreSQL database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Attempting to connect to database at {self.connection_params['host']}:{self.connection_params['port']}")
            
            self.connection = psycopg2.connect(
                host=self.connection_params['host'],
                port=self.connection_params['port'],
                database=self.connection_params['database'],
                user=self.connection_params['user'],
                password=self.connection_params['password'],
                sslmode=self.connection_params.get('sslmode', 'prefer'),
                connect_timeout=10
            )
            
            self._is_connected = True
            logger.info("Database connection established successfully")
            
            # Validate schema after successful connection
            if not self.validate_schema():
                logger.error("Schema validation failed")
                self.disconnect()
                return False
            
            return True
            
        except OperationalError as e:
            logger.error(
                f"Database connection failed - Host: {self.connection_params['host']}, "
                f"Port: {self.connection_params['port']}, "
                f"Database: {self.connection_params['database']}, "
                f"Error: {str(e)}"
            )
            self._is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error during database connection: {str(e)}")
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing database connection: {str(e)}")
            finally:
                self.connection = None
                self._is_connected = False
    
    def validate_schema(self) -> bool:
        """
        Validate that required tables and fields exist in the database
        
        Returns:
            bool: True if schema is valid, False otherwise
        """
        if not self._is_connected or not self.connection:
            logger.error("Cannot validate schema: not connected to database")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Validate tab_analytics table
            required_tab_analytics_fields = [
                'session_id', 'hostname', 'url', 'category', 
                'content_type', 'active_seconds', 'timestamp'
            ]
            
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tab_analytics'
            """)
            
            tab_analytics_columns = [row[0] for row in cursor.fetchall()]
            
            if not tab_analytics_columns:
                logger.error("Table 'tab_analytics' does not exist")
                cursor.close()
                return False
            
            missing_fields = set(required_tab_analytics_fields) - set(tab_analytics_columns)
            if missing_fields:
                logger.error(f"Missing required fields in tab_analytics: {missing_fields}")
                cursor.close()
                return False
            
            # Validate content_preferences table
            required_content_preferences_fields = [
                'date', 'content_type', 'total_time_seconds', 
                'session_count', 'productivity_score'
            ]
            
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'content_preferences'
            """)
            
            content_preferences_columns = [row[0] for row in cursor.fetchall()]
            
            if not content_preferences_columns:
                logger.error("Table 'content_preferences' does not exist")
                cursor.close()
                return False
            
            missing_fields = set(required_content_preferences_fields) - set(content_preferences_columns)
            if missing_fields:
                logger.error(f"Missing required fields in content_preferences: {missing_fields}")
                cursor.close()
                return False
            
            cursor.close()
            logger.info("Schema validation successful")
            return True
            
        except DatabaseError as e:
            logger.error(f"Database error during schema validation: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during schema validation: {str(e)}")
            return False
    
    def query_tab_analytics(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[TabAnalyticsRecord]:
        """
        Query tab_analytics table for records within date range
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
        
        Returns:
            List of TabAnalyticsRecord objects
        """
        if not self._is_connected or not self.connection:
            logger.error("Cannot query: not connected to database")
            return []
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            query = sql.SQL("""
                SELECT session_id, hostname, url, category, content_type, 
                       active_seconds, timestamp
                FROM tab_analytics
                WHERE timestamp >= %s AND timestamp <= %s
                ORDER BY timestamp ASC
            """)
            
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            cursor.close()
            
            logger.info(f"Retrieved {len(rows)} records from tab_analytics")
            
            # Convert to TabAnalyticsRecord objects with validation
            records = []
            for row in rows:
                try:
                    record = TabAnalyticsRecord(**dict(row))
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Skipping invalid record: {str(e)}, Record: {dict(row)}")
                    continue
            
            logger.info(f"Successfully validated {len(records)} tab_analytics records")
            return records
            
        except DatabaseError as e:
            logger.error(f"Database error querying tab_analytics: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error querying tab_analytics: {str(e)}")
            return []
    
    def query_content_preferences(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ContentPreferenceRecord]:
        """
        Query content_preferences table for records within date range
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
        
        Returns:
            List of ContentPreferenceRecord objects
        """
        if not self._is_connected or not self.connection:
            logger.error("Cannot query: not connected to database")
            return []
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            query = sql.SQL("""
                SELECT date, content_type, total_time_seconds, 
                       session_count, productivity_score
                FROM content_preferences
                WHERE date >= %s AND date <= %s
                ORDER BY date ASC
            """)
            
            cursor.execute(query, (start_date.date(), end_date.date()))
            rows = cursor.fetchall()
            cursor.close()
            
            logger.info(f"Retrieved {len(rows)} records from content_preferences")
            
            # Convert to ContentPreferenceRecord objects with validation
            records = []
            for row in rows:
                try:
                    record = ContentPreferenceRecord(**dict(row))
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Skipping invalid record: {str(e)}, Record: {dict(row)}")
                    continue
            
            logger.info(f"Successfully validated {len(records)} content_preferences records")
            return records
            
        except DatabaseError as e:
            logger.error(f"Database error querying content_preferences: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error querying content_preferences: {str(e)}")
            return []
    
    def is_connected(self) -> bool:
        """Check if database connection is active"""
        return self._is_connected and self.connection is not None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
