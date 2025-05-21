import logging
import threading
import os
import sys

# Adjust sys.path to allow running main.py directly from its subdirectory
# while still enabling relative imports for modules within the 'twitter_bot' package.
# This adds the parent directory of 'twitter_bot' (i.e., 'server') to sys.path.
_main_dir = os.path.dirname(os.path.abspath(__file__))
_package_root = os.path.dirname(_main_dir) # This should be 'server/'
if _package_root not in sys.path:
    sys.path.insert(0, _package_root)

# Now relative imports should work, assuming 'twitter_bot' is the package name.
# We expect to be in 'server/twitter_bot/main.py', so the imports become
# from twitter_bot import twitter_client, bot_logic

# Assuming main.py is in server/twitter_bot/
# Ensure other bot modules are in the same directory or accessible via Python path
from twitter_bot import twitter_client
from twitter_bot import bot_logic

# Configure basic logging for the main entry point
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__) # Use __name__ for the logger of this specific file

# Set higher level logging for noisy libraries if needed, e.g.:
# logging.getLogger('tweepy').setLevel(logging.WARNING)

def main():
    logger.info("Starting CelebXplain Twitter Bot...")

    # 1. Initialize Twitter Client (from twitter_client.py)
    # This function should load credentials from .env as configured in twitter_client.py
    # and set up the global api_v1 and api_v2 in that module.
    api_v1, api_v2 = twitter_client.init_client()

    if not api_v1 or not api_v2:
        logger.critical("Failed to initialize Twitter API clients. Bot cannot start.")
        logger.critical("Please check credentials in .env and configurations in twitter_client.py.")
        return # Exit if clients aren't initialized

    # Check for essential configurations needed by twitter_client.listen_for_mentions
    if not twitter_client.TWITTER_BOT_USERNAME or not twitter_client.TWITTER_BEARER_TOKEN:
        logger.critical("TWITTER_BOT_USERNAME or TWITTER_BEARER_TOKEN not set.")
        logger.critical("These are required for the mention listener. Check .env and twitter_client.py.")
        return
    
    logger.info(f"Twitter clients initialized successfully. Bot User: @{twitter_client.TWITTER_BOT_USERNAME}")

    # 2. Start the job status polling thread (from bot_logic.py)
    # The poll_job_statuses function in bot_logic is designed to run in an infinite loop.
    # Running it in a daemon thread allows the main program to exit even if the thread is running.
    polling_thread = threading.Thread(target=bot_logic.poll_job_statuses, daemon=True)
    polling_thread.start()
    logger.info("Job status polling thread started.")

    # 3. Start listening for mentions (from twitter_client.py)
    # This function will use api_v2 (and TWITTER_BEARER_TOKEN) from twitter_client module.
    # It will call bot_logic.handle_mention for each relevant tweet.
    # This is typically a blocking call.
    logger.info(f"Starting to listen for mentions to @{twitter_client.TWITTER_BOT_USERNAME}...")
    try:
        twitter_client.listen_for_mentions(callback_on_mention=bot_logic.handle_mention)
    except KeyboardInterrupt:
        logger.info("Bot manually interrupted. Shutting down...")
    except Exception as e:
        logger.critical(f"Mention listener encountered a critical error: {e}", exc_info=True)
    finally:
        logger.info("Mention listener has stopped.")
        # Add any other cleanup logic here if needed when the bot stops.
        # Since the polling thread is a daemon, it will exit when the main thread exits.

if __name__ == '__main__':
    # Load .env file from the server directory (one level up from twitter_bot)
    # This ensures environment variables are available for all modules if not already loaded.
    # Modules like twitter_client.py and request_parser.py also try to load .env,
    # but doing it here ensures it's loaded early.
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        logger.info(f"Loaded .env file from: {dotenv_path}")
    else:
        logger.warning(f".env file not found at {dotenv_path}. Ensure it exists and is configured.")
    
    main()
    logger.info("CelebXplain Twitter Bot has shut down.") 