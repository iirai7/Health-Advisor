import mysql.connector
from mysql.connector import Error
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    """Database connection handler"""
    
    _connection = None
    
    @classmethod
    def get_connection(cls):
        """Get database connection — reconnects if dropped"""
        try:
            if cls._connection is None or not cls._connection.is_connected():
                cls._connection = mysql.connector.connect(
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    port=Config.DB_PORT,
                    autocommit=True,
                    connection_timeout=10,
                    pool_reset_session=True,
                )
                logger.info("Database connected successfully")
        except Error as e:
            logger.error(f"Error while connecting to MySQL: {e}")
            raise
        return cls._connection

    @classmethod
    def get_cursor(cls):
        """Get fresh cursor for every request"""
        connection = cls.get_connection()
        return connection.cursor(dictionary=True)
    
    @classmethod
    def commit(cls):
        """Commit transaction"""
        if cls._connection:
            cls._connection.commit()
    
    @classmethod
    def rollback(cls):
        """Rollback transaction"""
        if cls._connection:
            cls._connection.rollback()
    
    @classmethod
    def close(cls):
        """Close database connection"""
        if cls._connection:
            cls._connection.close()
        cls._connection = None

# Create a singleton instance
db = Database()