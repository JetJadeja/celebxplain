import sqlite3
import os
import datetime
import logging
import contextlib
from dotenv import load_dotenv

load_dotenv()

APP_DATA_BASE_DIR = os.environ.get('APP_DATA_BASE_DIR', 'data')
# Configure logger for this module
logger = logging.getLogger(__name__)
# Basic configuration if no handlers are set for the root logger (common in scripts)
level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
level = logging.getLevelName(level_str)
logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), APP_DATA_BASE_DIR, 'database.db')

@contextlib.contextmanager
def get_db_connection():
    """Create a connection to the SQLite database, managed as a context."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    try:
        yield conn # Provide the connection object to the with block
    finally:
        conn.close() # Ensure connection is closed when exiting the with block

def init_db():
    """Initialize the database with required tables"""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    with get_db_connection() as conn: # Use context manager
        cursor = conn.cursor()
        
        # Create jobs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            persona_id TEXT NOT NULL,
            query TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            result_url TEXT,
            error TEXT,
            original_tweet_id TEXT DEFAULT NULL,
            original_tweet_author_id TEXT DEFAULT NULL,
            reply_posted BOOLEAN DEFAULT 0
        )
        ''')
        
        # Create job_updates table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
        ''')
        
        # Check and add new columns if they don't exist (for existing databases)
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [info[1] for info in cursor.fetchall()]

        if 'original_tweet_id' not in columns:
            cursor.execute('ALTER TABLE jobs ADD COLUMN original_tweet_id TEXT DEFAULT NULL')
            logger.info("Added 'original_tweet_id' column to jobs table.")
        
        if 'original_tweet_author_id' not in columns:
            cursor.execute('ALTER TABLE jobs ADD COLUMN original_tweet_author_id TEXT DEFAULT NULL')
            logger.info("Added 'original_tweet_author_id' column to jobs table.")
            
        if 'reply_posted' not in columns:
            cursor.execute('ALTER TABLE jobs ADD COLUMN reply_posted BOOLEAN DEFAULT 0')
            logger.info("Added 'reply_posted' column to jobs table.")

        conn.commit()
    # conn.close() # No longer needed here, finally block in get_db_connection handles it
    
    print("Database initialized successfully!")

# Job-related database functions
def create_job(job_id, persona_id, query, original_tweet_id=None, original_tweet_author_id=None):
    """Create a new job in the database"""
    with get_db_connection() as conn: # Use context manager
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            'INSERT INTO jobs (id, persona_id, query, status, created_at, original_tweet_id, original_tweet_author_id, reply_posted) VALUES (?, ?, ?, ?, ?, ?, ?, 0)',
            (job_id, persona_id, query, 'created', now, original_tweet_id, original_tweet_author_id)
        )
        
        # Add initial update
        cursor.execute(
            'INSERT INTO job_updates (job_id, status, message, created_at) VALUES (?, ?, ?, ?)',
            (job_id, 'created', f'Job created for persona {persona_id} explaining {query}', now)
        )
        
        conn.commit()
    # conn.close() # No longer needed here

def update_job_status(job_id, status, message=None, result_url=None, error=None):
    """Update job status and add an update entry"""
    with get_db_connection() as conn: # Use context manager
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        
        # Update job status
        if status == 'completed':
            cursor.execute(
                'UPDATE jobs SET status = ?, completed_at = ?, result_url = ? WHERE id = ?',
                (status, now, result_url, job_id)
            )
        elif status == 'error':
            cursor.execute(
                'UPDATE jobs SET status = ?, error = ? WHERE id = ?',
                (status, error, job_id)
            )
        else:
            cursor.execute(
                'UPDATE jobs SET status = ? WHERE id = ?',
                (status, job_id)
            )
        
        # Add job update
        update_message = message if message else f"Status changed to {status}"
        cursor.execute(
            'INSERT INTO job_updates (job_id, status, message, created_at) VALUES (?, ?, ?, ?)',
            (job_id, status, update_message, now)
        )
        
        conn.commit()
    # conn.close() # No longer needed here

def get_job(job_id):
    """Get job details by ID"""
    with get_db_connection() as conn: # Use context manager
        cursor = conn.cursor()
        
        job_row = cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    # conn.close() # No longer needed here
    
    if job_row: # job_row is sqlite3.Row or None
        return dict(job_row)
    return None

def get_job_updates(job_id):
    """Get all updates for a job"""
    with get_db_connection() as conn: # Use context manager
        cursor = conn.cursor()
        
        updates_rows = cursor.execute(
            'SELECT * FROM job_updates WHERE job_id = ? ORDER BY created_at ASC', 
            (job_id,)
        ).fetchall()
    # conn.close() # No longer needed here
    
    return [dict(update) for update in updates_rows]

def get_pending_twitter_replies():
    """Fetches jobs that originated from Twitter and are in 'completed' or 'error' status, 
       and haven't had a reply posted yet.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, original_tweet_id, status, result_url, error, persona_id, query 
            FROM jobs 
            WHERE original_tweet_id IS NOT NULL 
            AND (status = 'completed' OR status = 'error')
            AND reply_posted = 0
        """)
        jobs_for_reply = cursor.fetchall() # Returns list of Row objects
    
    if jobs_for_reply:
        return [dict(job) for job in jobs_for_reply]
    return [] # Return an empty list if no jobs found

def get_job_by_tweet_id(tweet_id):
    """
    Retrieves a job from the database based on the original_tweet_id.
    This is used to check if a job already exists for a given tweet, preventing duplicate job creation.
    
    Args:
        tweet_id: The ID of the tweet to check for existing jobs
        
    Returns:
        A dictionary with job data if found, or None if no job exists for this tweet ID
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM jobs WHERE original_tweet_id = ? LIMIT 1
        """, (tweet_id,))
        job = cursor.fetchone()
    
    if job:
        return dict(job)
    return None

def mark_job_reply_posted(job_id):
    """Mark a job as having had a reply posted to Twitter"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE jobs SET reply_posted = 1 WHERE id = ?',
            (job_id,)
        )
        conn.commit()
        return cursor.rowcount > 0