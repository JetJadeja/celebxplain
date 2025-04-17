from celery import Celery

# Create the Celery app
celery_app = Celery(
    'celebxplain',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,  # Tasks are acknowledged after execution (not before)
    worker_prefetch_multiplier=1,  # Don't prefetch more than one task per worker
    
    # Result backend settings
    result_expires=86400,  # Results expire after 1 day
    
    # Retry settings
    task_default_retry_delay=60,  # Default retry delay (seconds)
    task_max_retries=3,  # Maximum number of retries per task
    
    # Task routes for resource allocation
    task_routes={
        'tasks.create_celebrity_video_task': {'queue': 'video_processing'},
        'tasks.create_visuals_task': {'queue': 'video_processing'},
        'tasks.assemble_video_task': {'queue': 'video_processing'},
        'tasks.generate_script_task': {'queue': 'api_calls'},
        'tasks.generate_speech_task': {'queue': 'api_calls'},
        'tasks.process_video_job': {'queue': 'default'},
    }
)

# Auto-discover tasks in the tasks directory
celery_app.autodiscover_tasks(['tasks'])

# This allows you to call tasks directly when in the same process
# (development convenience)
celery_app.conf.task_always_eager = False

if __name__ == '__main__':
    celery_app.start() 