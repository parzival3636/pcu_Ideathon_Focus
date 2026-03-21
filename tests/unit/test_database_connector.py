"""Unit tests for DatabaseConnector class"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch
import psycopg2
from psycopg2 import OperationalError, DatabaseError

from src.data.database_connector import DatabaseConnector
from src.data.models import TabAnalyticsRecord, ContentPreferenceRecord


@pytest.fixture
def connection_params():
    """Sample connection parameters"""
    return {
        'host': 'localhost',
        'port': 5432,
        'database': 'test_db',
        'user': 'test_user',
        'password': 'test_pass',
        'sslmode': 'prefer'
    }


@pytest.fixture
def db_connector(connection_params):
    """Create DatabaseConnector instance"""
    return DatabaseConnector(connection_params)


class TestDatabaseConnectorInit:
    """Test DatabaseConnector initialization"""
    
    def test_init_stores_connection_params(self, connection_params):
        """Test that connection parameters are stored correctly"""
        connector = DatabaseConnector(connection_params)
        assert connector.connection_params == connection_params
        assert connector.connection is None
        assert connector._is_connected is False


class TestConnect:
    """Test database connection functionality"""
    
    @patch('src.data.database_connector.psycopg2.connect')
    def test_connect_success(self, mock_connect, db_connector):
        """Test successful database connection"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Mock schema validation
        with patch.object(db_connector, 'validate_schema', return_value=True):
            result = db_connector.connect()
        
        assert result is True
        assert db_connector.is_connected() is True
        mock_connect.assert_called_once()
    
    @patch('src.data.database_connector.psycopg2.connect')
    def test_connect_operational_error(self, mock_connect, db_connector):
        """Test connection failure with OperationalError"""
        mock_connect.side_effect = OperationalError("Connection refused")
        
        result = db_connector.connect()
        
        assert result is False
        assert db_connector.is_connected() is False
    
    @patch('src.data.database_connector.psycopg2.connect')
    def test_connect_schema_validation_fails(self, mock_connect, db_connector):
        """Test connection fails when schema validation fails"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        with patch.object(db_connector, 'validate_schema', return_value=False):
            result = db_connector.connect()
        
        assert result is False
        assert db_connector.is_connected() is False


class TestDisconnect:
    """Test database disconnection"""
    
    def test_disconnect_closes_connection(self, db_connector):
        """Test that disconnect closes the connection"""
        mock_conn = MagicMock()
        db_connector.connection = mock_conn
        db_connector._is_connected = True
        
        db_connector.disconnect()
        
        mock_conn.close.assert_called_once()
        assert db_connector.connection is None
        assert db_connector._is_connected is False
    
    def test_disconnect_handles_none_connection(self, db_connector):
        """Test disconnect handles None connection gracefully"""
        db_connector.connection = None
        db_connector._is_connected = False
        
        # Should not raise exception
        db_connector.disconnect()
        
        assert db_connector.connection is None


class TestValidateSchema:
    """Test schema validation"""
    
    def test_validate_schema_not_connected(self, db_connector):
        """Test validation fails when not connected"""
        result = db_connector.validate_schema()
        assert result is False
    
    def test_validate_schema_success(self, db_connector):
        """Test successful schema validation"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock tab_analytics columns
        mock_cursor.fetchall.side_effect = [
            [('session_id',), ('hostname',), ('url',), ('category',), 
             ('content_type',), ('active_seconds',), ('timestamp',)],
            [('date',), ('content_type',), ('total_time_seconds',), 
             ('session_count',), ('productivity_score',)]
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        db_connector.connection = mock_conn
        db_connector._is_connected = True
        
        result = db_connector.validate_schema()
        
        assert result is True
        assert mock_cursor.execute.call_count == 2
    
    def test_validate_schema_missing_table(self, db_connector):
        """Test validation fails when table is missing"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Return empty list (table doesn't exist)
        mock_cursor.fetchall.return_value = []
        
        mock_conn.cursor.return_value = mock_cursor
        db_connector.connection = mock_conn
        db_connector._is_connected = True
        
        result = db_connector.validate_schema()
        
        assert result is False
    
    def test_validate_schema_missing_fields(self, db_connector):
        """Test validation fails when required fields are missing"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Missing 'timestamp' field
        mock_cursor.fetchall.return_value = [
            ('session_id',), ('hostname',), ('url',), ('category',), 
            ('content_type',), ('active_seconds',)
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        db_connector.connection = mock_conn
        db_connector._is_connected = True
        
        result = db_connector.validate_schema()
        
        assert result is False


class TestQueryTabAnalytics:
    """Test querying tab_analytics table"""
    
    def test_query_not_connected(self, db_connector):
        """Test query fails when not connected"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = db_connector.query_tab_analytics(start_date, end_date)
        
        assert result == []
    
    def test_query_success(self, db_connector):
        """Test successful query returns validated records"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            {
                'session_id': 'session1',
                'hostname': 'example.com',
                'url': 'https://example.com/page',
                'category': 'productive',
                'content_type': 'text',
                'active_seconds': 300,
                'timestamp': datetime(2024, 1, 15, 10, 30)
            },
            {
                'session_id': 'session2',
                'hostname': 'test.com',
                'url': 'https://test.com/article',
                'category': 'neutral',
                'content_type': 'video',
                'active_seconds': 600,
                'timestamp': datetime(2024, 1, 16, 14, 20)
            }
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        db_connector.connection = mock_conn
        db_connector._is_connected = True
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = db_connector.query_tab_analytics(start_date, end_date)
        
        assert len(result) == 2
        assert all(isinstance(r, TabAnalyticsRecord) for r in result)
        assert result[0].session_id == 'session1'
        assert result[1].session_id == 'session2'
    
    def test_query_skips_invalid_records(self, db_connector):
        """Test that invalid records are skipped with warning"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # One valid, one invalid record
        mock_cursor.fetchall.return_value = [
            {
                'session_id': 'session1',
                'hostname': 'example.com',
                'url': 'https://example.com/page',
                'category': 'productive',
                'content_type': 'text',
                'active_seconds': 300,
                'timestamp': datetime(2024, 1, 15, 10, 30)
            },
            {
                'session_id': 'session2',
                'hostname': 'test.com',
                'url': 'https://test.com/article',
                'category': 'invalid_category',  # Invalid
                'content_type': 'text',
                'active_seconds': 600,
                'timestamp': datetime(2024, 1, 16, 14, 20)
            }
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        db_connector.connection = mock_conn
        db_connector._is_connected = True
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = db_connector.query_tab_analytics(start_date, end_date)
        
        # Only valid record should be returned
        assert len(result) == 1
        assert result[0].session_id == 'session1'


class TestQueryContentPreferences:
    """Test querying content_preferences table"""
    
    def test_query_not_connected(self, db_connector):
        """Test query fails when not connected"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = db_connector.query_content_preferences(start_date, end_date)
        
        assert result == []
    
    def test_query_success(self, db_connector):
        """Test successful query returns validated records"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            {
                'date': date(2024, 1, 15),
                'content_type': 'text',
                'total_time_seconds': 3600,
                'session_count': 10,
                'productivity_score': 0.75
            },
            {
                'date': date(2024, 1, 16),
                'content_type': 'video',
                'total_time_seconds': 1800,
                'session_count': 5,
                'productivity_score': 0.60
            }
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        db_connector.connection = mock_conn
        db_connector._is_connected = True
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = db_connector.query_content_preferences(start_date, end_date)
        
        assert len(result) == 2
        assert all(isinstance(r, ContentPreferenceRecord) for r in result)
        assert result[0].content_type == 'text'
        assert result[1].content_type == 'video'
    
    def test_query_database_error(self, db_connector):
        """Test query handles database errors gracefully"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_cursor.execute.side_effect = DatabaseError("Query failed")
        mock_conn.cursor.return_value = mock_cursor
        db_connector.connection = mock_conn
        db_connector._is_connected = True
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = db_connector.query_content_preferences(start_date, end_date)
        
        assert result == []


class TestContextManager:
    """Test context manager functionality"""
    
    @patch('src.data.database_connector.psycopg2.connect')
    def test_context_manager(self, mock_connect):
        """Test using DatabaseConnector as context manager"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        connection_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
        
        with patch.object(DatabaseConnector, 'validate_schema', return_value=True):
            with DatabaseConnector(connection_params) as connector:
                assert connector.is_connected() is True
            
            # After exiting context, should be disconnected
            assert connector.is_connected() is False
            mock_conn.close.assert_called_once()
