import uuid
import os

from utils.db import create_job as db_create_job, update_job_status, get_job, get_job_updates
# Import the Celery app instead of the task directly
from celery_app import celery_app

def create_job(persona_id, query):
    """Create a new job and start processing in background using Celery"""
    # Generate unique job identifier
    job_id = str(uuid.uuid4())
    
    # Record in database
    db_create_job(job_id, persona_id, query)
    
    # Launch Celery task for processing using send_task instead of direct import
    celery_app.send_task('tasks.job_tasks.process_job', args=[job_id, persona_id, query])
    
    return job_id

def get_job_info(job_id):
    """Retrieve current job status and all updates"""
    job_data = get_job(job_id)
    
    if not job_data:
        return None
    
    
    # Collect all status updates
    updates = get_job_updates(job_id)
    
    print(updates)
    
    return {
        "job_details": job_data,
        "status_updates": updates
    }
