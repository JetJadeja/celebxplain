from celery import Celery
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create the Celery app
celery_app = Celery(
    'oracle',
    broker=os.environ.get('REDIS_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_BACKEND_URL', 'redis://localhost:6379/0')
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
    result_expires=int(os.environ.get('CELERY_RESULT_EXPIRES_SECONDS', 86400)),  # Results expire after 1 day
    
    # Retry settings
    task_default_retry_delay=int(os.environ.get('CELERY_TASK_DEFAULT_RETRY_DELAY_SECONDS', 60)),  # Default retry delay (seconds)
    task_max_retries=int(os.environ.get('CELERY_TASK_MAX_RETRIES', 3)),  # Maximum number of retries per task
)

# Auto-discover tasks in the server/tasks directory
celery_app.autodiscover_tasks(['tasks'])

# This allows you to call tasks directly when in the same process
# (development convenience)
celery_app.conf.task_always_eager = os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'False').lower() == 'true'

if __name__ == '__main__':
    celery_app.start() 