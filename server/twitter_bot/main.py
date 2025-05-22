import logging
import threading
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path to resolve imports properly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import after sys.path is set
from utils.db import init_db
from utils.migration import migrate_add_reply_posted_column
from twitter_bot import bot_logic
from twitter_bot import twitter_client

# Initialize logging
level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
level = logging.getLevelName(level_str)
logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file in the server/ directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    logger.info(f"Loaded .env file from: {dotenv_path}")
else:
    logger.warning(f".env file not found at {dotenv_path}. Will rely on environment variables set in the system.")

def main():
    """Main function to start the CelebXplain Twitter Bot"""
    logger.info("Starting CelebXplain Twitter Bot...")
    
    # 1. Initialize database (will create if doesn't exist)
    try:
        init_db()
        logger.info("Database initialized.")
        
        # Run migration to add reply_posted column if needed
        migrate_add_reply_posted_column()
        logger.info("Database migration completed.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return 1 # Exit with error code
    
    # 2. Initialize Twitter Client(s)
    try:
        api_v1, api_v2 = twitter_client.init_client()
        if not api_v1 or not api_v2:
            logger.critical("Failed to initialize Twitter API clients. Bot cannot start. Check credentials in .env")
            return 1
        bot_user_response = api_v2.get_me(user_fields=["username"])
        bot_username = bot_user_response.data.username if bot_user_response and bot_user_response.data else None
        logger.info(f"Twitter clients initialized successfully. Bot User: @{bot_username}")
    except Exception as e:
        logger.critical(f"Failed to initialize Twitter clients: {e}")
        return 1
    
    # 3. Start the job status polling thread
    try:
        polling_thread = threading.Thread(target=bot_logic.poll_job_statuses, daemon=True)
        polling_thread.start()
        logger.info("Job status polling thread started.")
    except Exception as e:
        logger.critical(f"Failed to start job status polling thread: {e}")
        return 1
    
    # 4. Start the Twitter mention listener (blocking)
    try:
        logger.info(f"Starting to listen for mentions to @{twitter_client.TWITTER_BOT_USERNAME}...")
        twitter_client.listen_for_mentions(callback_on_mention=bot_logic.handle_mention)
    except Exception as e:
        logger.critical(f"Twitter mention listener failed: {e}")
        return 1
    finally:
        logger.info("Twitter bot has shut down.")
    
    return 0 # Exit successfully

if __name__ == "__main__":
    sys.exit(main()) 