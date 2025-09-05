import logging
from typing import Optional, Dict, Any
import pymysql
from src.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_TABLE

logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME,
    'charset': 'utf8mb4',
    'autocommit': True,
    'connect_timeout': 10,
    'read_timeout': 10,
    'write_timeout': 10
}

class DatabaseManager:
    def __init__(self):
        self.connection = None
    
    def get_connection(self):
        try:
            if self.connection is None or not self.connection.open:
                self.connection = pymysql.connect(**DB_CONFIG)
                logger.info("Database connected")
            return self.connection
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close_connection(self):
        if self.connection and self.connection.open:
            self.connection.close()
            logger.info("Database disconnected")
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        try:
            connection = self.get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def get_chat_club_mapping(self) -> Dict[int, int]:
        query = f"SELECT chat_id, club_id FROM {DB_TABLE}"
        try:
            results = self.execute_query(query)
            mapping = {row['chat_id']: row['club_id'] for row in results}
            logger.info(f"Loaded {len(mapping)} chat-club mappings")
            return mapping
        except Exception as e:
            logger.error(f"Failed to load chat-club mapping: {e}")
            return {}
    
    def get_club_id_by_chat_id(self, chat_id: int) -> Optional[int]:
        query = f"SELECT club_id FROM {DB_TABLE} WHERE chat_id = %s"
        try:
            results = self.execute_query(query, (chat_id,))
            if results:
                return results[0]['club_id']
            return None
        except Exception as e:
            logger.error(f"Failed to get club_id for chat_id {chat_id}: {e}")
            return None

db_manager = DatabaseManager()