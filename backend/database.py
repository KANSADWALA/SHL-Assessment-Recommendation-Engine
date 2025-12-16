# standard library imports
import sqlite3
import json
import os
import shutil
from contextlib import contextmanager
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabasePersistence:
    """
    DatabasePersistence

    Lightweight persistence layer for storing feedback and interactions in
    a local SQLite database. Provides helper methods to initialize the schema,
    obtain connections, and perform basic CRUD/query operations used by the
    recommender system.
    """

    def __init__(self, db_path='data/recommender.db'):
        """Create the persistence helper and ensure DB validity.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self._ensure_valid_database()
    
    def _ensure_valid_database(self):
        """Ensure the database file exists and has the required schema.

        Attempts to open the database and query sqlite_master. If the file is
        missing or corrupted, `_handle_corrupted_database` will attempt to
        back it up and recreate a clean database schema.
        """
        try:
            # Try to open and validate the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test if we can query sqlite_master
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            
            # If no tables exist, initialize
            if len(tables) == 0:
                logger.info("No tables found, initializing database...")
                self._init_db()
            else:
                logger.info(f"Database valid with {len(tables)} tables")
                
        except sqlite3.DatabaseError as e:
            logger.error(f"Database corruption detected: {e}")
            self._handle_corrupted_database()
        except Exception as e:
            logger.error(f"Database validation error: {e}")
            self._handle_corrupted_database()
    
    def _handle_corrupted_database(self):
        """Backup a corrupted DB file and recreate a clean schema.

        If a corrupted database file is detected this method will copy the
        existing file to a timestamped `.corrupted.*` backup, remove the
        original, and initialize a new database with the expected tables.
        """
        try:
            # Create backup of corrupted file
            if os.path.exists(self.db_path):
                backup_path = f"{self.db_path}.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"Backed up corrupted database to: {backup_path}")
                
                # Remove corrupted file
                os.remove(self.db_path)
                logger.info("Removed corrupted database file")
            
            # Recreate database
            logger.info("Recreating database with fresh schema...")
            self._init_db()
            logger.info("✓ Database successfully recreated")
            
        except Exception as e:
            logger.error(f"Failed to handle corrupted database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager yielding a sqlite3 connection.

        The context manager commits on successful exit and rolls back on
        exceptions. Connections are closed automatically.

        Yields:
            sqlite3.Connection: Active connection object.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """Create required tables and indexes if they are missing.

        The schema includes `feedback` and `interactions` tables and several
        indexes to optimize common queries used by the recommender.
        """
        try:
            with self.get_connection() as conn:
                # Feedback table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        assessment_id TEXT NOT NULL,
                        rating INTEGER NOT NULL,
                        timestamp TEXT NOT NULL,
                        context TEXT
                    )
                ''')
                
                # Interactions table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS interactions (
                        user_id TEXT NOT NULL,
                        assessment_id TEXT NOT NULL,
                        score REAL NOT NULL,
                        last_activity TEXT NOT NULL,
                        PRIMARY KEY (user_id, assessment_id)
                    )
                ''')
                
                # Create indexes for faster queries
                conn.execute('CREATE INDEX IF NOT EXISTS idx_user ON feedback(user_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_assessment ON feedback(assessment_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON feedback(timestamp)')
                
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def verify_database_health(self):
        """Run integrity and schema checks on the database.

        Returns:
            bool: True if the integrity check passes and required tables are
                  present, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Run integrity check
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                
                if result[0] != 'ok':
                    logger.error(f"Database integrity check failed: {result[0]}")
                    return False
                
                # Check if tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                expected_tables = {'feedback', 'interactions'}
                actual_tables = {table[0] for table in tables}
                
                if not expected_tables.issubset(actual_tables):
                    logger.error(f"Missing tables. Expected: {expected_tables}, Found: {actual_tables}")
                    return False
                
                logger.info("Database health check passed")
                return True
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def save_feedback(self, feedback_item):
        """Persist a feedback item into the `feedback` table.

        Args:
            feedback_item (dict): Must contain `user_id`, `assessment_id`,
                `rating` and `timestamp`. Optional `context` may be provided
                and will be stored as JSON.
        """
        try:
            with self.get_connection() as conn:
                conn.execute(
                    'INSERT INTO feedback (user_id, assessment_id, rating, timestamp, context) VALUES (?, ?, ?, ?, ?)',
                    (
                        feedback_item['user_id'],
                        feedback_item['assessment_id'],
                        feedback_item['rating'],
                        feedback_item['timestamp'],
                        json.dumps(feedback_item.get('context'))
                    )
                )
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
            raise
    
    def load_recent_feedback(self, limit=5000):
        """Load the most recent feedback rows from the DB.

        Args:
            limit (int): Maximum number of recent feedback rows to load.

        Returns:
            list[dict]: List of feedback dicts with keys `user_id`,
                `assessment_id`, `rating`, `timestamp`.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT user_id, assessment_id, rating, timestamp FROM feedback ORDER BY id DESC LIMIT ?',
                    (limit,)
                )
                return [
                    {
                        'user_id': row[0],
                        'assessment_id': row[1],
                        'rating': row[2],
                        'timestamp': row[3]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to load feedback: {e}")
            return []
    
    def save_interaction(self, user_id, assessment_id, score, last_activity):
        """Insert or update a user's interaction score for an assessment.

        Uses an upsert to add a new interaction or increment the existing
        `score` and update `last_activity` when the same (user_id,assessment_id)
        pair already exists.
        """
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO interactions (user_id, assessment_id, score, last_activity)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, assessment_id) DO UPDATE SET
                        score = score + ?,
                        last_activity = ?
                ''', (user_id, assessment_id, score, last_activity, score, last_activity))
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
            raise
    
    def get_statistics(self):
        """Return basic usage statistics from the database.

        Returns:
            dict: Counts for feedback entries, interactions and unique users.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Count feedback entries
                cursor.execute("SELECT COUNT(*) FROM feedback")
                feedback_count = cursor.fetchone()[0]
                
                # Count interactions
                cursor.execute("SELECT COUNT(*) FROM interactions")
                interaction_count = cursor.fetchone()[0]
                
                # Get unique users
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM feedback")
                unique_users = cursor.fetchone()[0]
                
                return {
                    'feedback_count': feedback_count,
                    'interaction_count': interaction_count,
                    'unique_users': unique_users
                }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                'feedback_count': 0,
                'interaction_count': 0,
                'unique_users': 0
            }