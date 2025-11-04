#!/usr/bin/env python3
"""
Centralized Database Connection Manager
Provides connection pooling and centralized database access
"""

import os
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
import logging
import threading
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import time

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database connection manager with connection pooling"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.connection_pool = None
            self.db_config = self._get_db_config()
            self._create_connection_pool()
    
    def _get_db_config(self) -> Dict[str, str]:
        """Get database configuration from environment variables"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'ZGR_AI'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    def _create_connection_pool(self):
        """Create connection pool"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                **self.db_config
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            self.connection_pool = None
    
    @contextmanager
    def get_connection(self, cursor_factory=None):
        """Get database connection from pool"""
        connection = None
        try:
            if self.connection_pool:
                connection = self.connection_pool.getconn()
                if cursor_factory:
                    cursor = connection.cursor(cursor_factory=cursor_factory)
                else:
                    cursor = connection.cursor()
                yield cursor
            else:
                # Fallback to direct connection
                connection = psycopg2.connect(**self.db_config)
                if cursor_factory:
                    cursor = connection.cursor(cursor_factory=cursor_factory)
                else:
                    cursor = connection.cursor()
                yield cursor
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                if self.connection_pool:
                    self.connection_pool.putconn(connection)
                else:
                    connection.close()
    
    @contextmanager
    def get_dict_cursor(self):
        """Get RealDictCursor for easier data access"""
        with self.get_connection(cursor_factory=RealDictCursor) as cursor:
            yield cursor
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = 'all') -> List[Dict[str, Any]]:
        """Execute query and return results"""
        try:
            with self.get_dict_cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch == 'all':
                    return cursor.fetchall()
                elif fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'many':
                    return cursor.fetchmany()
                else:
                    return []
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute update/insert/delete query and return affected rows"""
        try:
            with self.get_connection() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution error: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection pool information"""
        if self.connection_pool:
            return {
                'pool_size': self.connection_pool.maxconn,
                'available_connections': self.connection_pool.maxconn - len(self.connection_pool._used),
                'used_connections': len(self.connection_pool._used)
            }
        return {'pool_size': 0, 'available_connections': 0, 'used_connections': 0}
    
    def close_pool(self):
        """Close connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions
def get_db_connection():
    """Get database connection context manager"""
    return db_manager.get_connection()

def get_db_cursor():
    """Get database cursor context manager"""
    return db_manager.get_dict_cursor()

def execute_query(query: str, params: tuple = None, fetch: str = 'all'):
    """Execute query using global database manager"""
    return db_manager.execute_query(query, params, fetch)

def execute_update(query: str, params: tuple = None):
    """Execute update using global database manager"""
    return db_manager.execute_update(query, params)

def test_db_connection():
    """Test database connection"""
    return db_manager.test_connection()

def get_db_info():
    """Get database connection information"""
    return db_manager.get_connection_info()

# Database utility functions
class DatabaseUtils:
    """Utility functions for common database operations"""
    
    @staticmethod
    def get_opportunity_count() -> int:
        """Get total number of opportunities"""
        try:
            result = execute_query("SELECT COUNT(*) as count FROM opportunities", fetch='one')
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error getting opportunity count: {e}")
            return 0
    
    @staticmethod
    def get_recent_opportunities(limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent opportunities"""
        try:
            query = """
                SELECT opportunity_id, title, posted_date, naics_code, 
                       organization_type as agency
                FROM opportunities 
                ORDER BY posted_date DESC 
                LIMIT %s
            """
            return execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"Error getting recent opportunities: {e}")
            return []
    
  

    @staticmethod
    def get_recent_opportunities_console(limit: int = 25) -> List[Dict[str, Any]]:
        """Get recent opportunities with summary and detail fields for the console view"""
        try:
            query = """
                SELECT
                    opportunity_id,
                    title,
                    posted_date,
                    response_dead_line AS response_deadline,
                    naics_code,
                    organization_type AS agency,
                    LEFT(COALESCE(description, ''), 280) AS summary,
                    description
                FROM opportunities
                ORDER BY posted_date DESC
                LIMIT %s
            """
            return execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"Error getting console opportunities: {e}")
            return []

    @staticmethod
    def search_opportunities(keywords: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search opportunities by keywords"""
        try:
            query = """
                SELECT opportunity_id, title, description, posted_date, 
                       naics_code, organization_type as agency
                FROM opportunities 
                WHERE title ILIKE %s OR description ILIKE %s
                ORDER BY posted_date DESC 
                LIMIT %s
            """
            search_term = f"%{keywords}%"
            return execute_query(query, (search_term, search_term, limit))
        except Exception as e:
            logger.error(f"Error searching opportunities: {e}")
            return []
    
    @staticmethod
    def get_opportunity_by_id(opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Get opportunity by ID"""
        try:
            query = "SELECT * FROM opportunities WHERE opportunity_id = %s"
            result = execute_query(query, (opportunity_id,), fetch='one')
            return result
        except Exception as e:
            logger.error(f"Error getting opportunity by ID: {e}")
            return None
    
    @staticmethod
    def update_opportunity_cache(opportunity_id: str, data: Dict[str, Any]) -> bool:
        """Update opportunity cache data"""
        try:
            # Convert data to JSON string for storage
            import json
            data_json = json.dumps(data, default=str)  # default=str handles datetime objects
            
            query = """
                UPDATE opportunities 
                SET cached_data = %s, cache_updated_at = NOW()
                WHERE opportunity_id = %s
            """
            execute_update(query, (data_json, opportunity_id))
            return True
        except Exception as e:
            logger.error(f"Error updating opportunity cache: {e}")
            return False
    
    @staticmethod
    def get_cached_opportunity_data(opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Get cached opportunity data"""
        try:
            query = """
                SELECT cached_data, cache_updated_at 
                FROM opportunities 
                WHERE opportunity_id = %s AND cached_data IS NOT NULL
            """
            result = execute_query(query, (opportunity_id,), fetch='one')
            return result['cached_data'] if result else None
        except Exception as e:
            logger.error(f"Error getting cached opportunity data: {e}")
            return None
    
    @staticmethod
    def is_cache_valid(opportunity_id: str, max_age_hours: int = 24) -> bool:
        """Check if cached data is still valid"""
        try:
            query = """
                SELECT cache_updated_at 
                FROM opportunities 
                WHERE opportunity_id = %s AND cache_updated_at IS NOT NULL
            """
            result = execute_query(query, (opportunity_id,), fetch='one')
            if not result:
                return False
            
            cache_age = time.time() - result['cache_updated_at'].timestamp()
            return cache_age < (max_age_hours * 3600)
        except Exception as e:
            logger.error(f"Error checking cache validity: {e}")
            return False

# Initialize database manager on import
if __name__ == "__main__":
    # Test the database manager
    print("Testing Database Manager...")
    
    if test_db_connection():
        print("âœ… Database connection successful")
        
        # Test basic operations
        count = DatabaseUtils.get_opportunity_count()
        print(f"ğŸ“Š Total opportunities: {count}")
        
        # Test connection info
        info = get_db_info()
        print(f"ğŸ”— Connection pool info: {info}")
    else:
        print("âŒ Database connection failed")
