"""
Task module for Celery background jobs
""" 

from .job_tasks import process_job

__all__ = ['process_job'] 