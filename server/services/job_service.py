import uuid
import os

from utils.db import create_job as db_create_job, update_job_status, get_job, get_job_updates
from tasks.job_tasks import process_job

def create_job(persona_id, query):
    """Create a new job and start processing in background using Celery"""
    # Generate unique job identifier
    job_id = str(uuid.uuid4())
    
    # Record in database
    db_create_job(job_id, persona_id, query)
    
    # Launch Celery task for processing
    process_job.delay(job_id, persona_id, query)
    
    return job_id

def get_job_info(job_id):
    """Retrieve current job status and all updates"""
    job_data = get_job(job_id)
    
    if not job_data:
        return None
    
    # Collect all status updates
    updates = get_job_updates(job_id)
    
    return {
        "job_details": job_data,
        "status_updates": updates
    }
