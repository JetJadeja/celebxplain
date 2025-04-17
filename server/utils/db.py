import sqlite3
import os
import datetime

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'database.db')

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def init_db():
    """Initialize the database with required tables"""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create jobs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        celeb_id TEXT NOT NULL,
        query TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        completed_at TIMESTAMP,
        result_url TEXT,
        error TEXT
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
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

# Job-related database functions
def create_job(job_id, celebrity, topic):
    """Create a new job in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.datetime.now().isoformat()
    
    cursor.execute(
        'INSERT INTO jobs (id, celebrity, topic, status, created_at) VALUES (?, ?, ?, ?, ?)',
        (job_id, celebrity, topic, 'created', now)
    )
    
    # Add initial update
    cursor.execute(
        'INSERT INTO job_updates (job_id, status, message, created_at) VALUES (?, ?, ?, ?)',
        (job_id, 'created', f'Job created for {celebrity} explaining {topic}', now)
    )
    
    conn.commit()
    conn.close()

def update_job_status(job_id, status, message=None, result_url=None, error=None):
    """Update job status and add an update entry"""
    conn = get_db_connection()
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
    conn.close()

def get_job(job_id):
    """Get job details by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    job = cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    
    conn.close()
    
    if job:
        return dict(job)
    return None

def get_job_updates(job_id):
    """Get all updates for a job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = cursor.execute(
        'SELECT * FROM job_updates WHERE job_id = ? ORDER BY created_at ASC', 
        (job_id,)
    ).fetchall()
    
    conn.close()
    
    return [dict(update) for update in updates]