import logging
import uuid
import os
import json
import time
import threading # For running poll_job_statuses in a separate thread

# Attempt to import project-specific modules
# These paths assume bot_logic.py is in server/twitter_bot/
try:
    from . import twitter_client
    from . import request_parser
    from ..utils.db import create_job as db_create_job_direct, get_job as db_get_job_direct
    from ..celery_app import celery_app as celery_app_direct
except ImportError as e:
    logging.error(f"Error importing modules: {e}. Ensure paths are correct and __init__.py files exist.")
    # Fallback for cases where direct execution might be attempted or structure is different
    # This is not ideal for production but helps if running script directly for tests initially
    import twitter_client
    import request_parser
    # For utils.db and celery_app, direct relative imports are tricky if not run as part of a package
    # We will assume for now they are correctly imported when run in the main application context
    pass 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration & Data Placeholders ---

# Load personas data once when the module is loaded
PERSONAS_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "personas.json")
loaded_personas_data = {}
persona_name_map = {} # For quick lookup of name by id

try:
    with open(PERSONAS_FILE_PATH, 'r') as f:
        loaded_personas_data = json.load(f)
        for p in loaded_personas_data.get("personas", []):
            if p.get("id") and p.get("name"):
                persona_name_map[p["id"]] = p["name"]
    logger.info(f"Successfully loaded personas data from {PERSONAS_FILE_PATH}")
except FileNotFoundError:
    logger.error(f"Personas data file not found at {PERSONAS_FILE_PATH}. Bot may not function correctly.")
except json.JSONDecodeError:
    logger.error(f"Error decoding JSON from {PERSONAS_FILE_PATH}. Bot may not function correctly.")
except Exception as e:
    logger.error(f"An unexpected error occurred loading personas data: {e}")

# Base directory for job results (e.g., where videos are stored)
# This should ideally be configured via environment variables or a config file
RESULTS_BASE_DIR = os.getenv("RESULTS_BASE_DIR", os.path.join(os.path.dirname(__file__), "..", "results"))
if not os.path.exists(RESULTS_BASE_DIR):
    try:
        os.makedirs(RESULTS_BASE_DIR)
        logger.info(f"Created RESULTS_BASE_DIR at {RESULTS_BASE_DIR}")
    except Exception as e:
        logger.error(f"Failed to create RESULTS_BASE_DIR at {RESULTS_BASE_DIR}: {e}")

# Public URL for accessing Flask video endpoint
# This should be configured via environment variables
YOUR_PUBLIC_FLASK_URL = os.getenv("YOUR_PUBLIC_FLASK_URL", "http://localhost:5001") # Example

# In-memory cache for tracking jobs. For persistence, consider SQLite or Redis.
# Structure: { "job_id": { "original_tweet_id": str, "topic": str, "persona_name": str, "status": "pending" } }
active_jobs_cache = {}

# Lock for thread-safe access to active_jobs_cache if poll_job_statuses runs in a thread
jobs_cache_lock = threading.Lock()

# --- Bot Logic Functions ---

def handle_mention(tweet):
    """
    Callback function to process incoming mentions to the bot.
    This function is triggered by the twitter_client.listen_for_mentions stream.

    Args:
        tweet: The tweet object from Tweepy (likely v2 Tweet object).
    """
    logger.info(f"Received mention. Tweet ID: {tweet.id}, Text: '{tweet.text}', Author ID: {tweet.author_id}")

    # 1. Get tweet text (the tweet object from stream usually has .text)
    tweet_text = tweet.text 
    # If for some reason text isn't directly available or you need to re-fetch for full text:
    # if not tweet_text:
    #     logger.info(f"Tweet text not directly in payload for {tweet.id}, attempting to fetch.")
    #     tweet_text = twitter_client.get_tweet_text(tweet.id)
    #     if not tweet_text:
    #         logger.error(f"Failed to fetch text for tweet {tweet.id}. Aborting.")
    #         twitter_client.post_reply(tweet.id, "Sorry, I couldn't retrieve the text of your tweet.")
    #         return

    # 2. Parse the tweet to get topic, persona_id, and any error
    # Ensure loaded_personas_data is available
    if not loaded_personas_data or not persona_name_map:
        logger.error("Personas data not loaded. Cannot process tweet.")
        twitter_client.post_reply(tweet.id, "Sorry, there's a configuration issue with my personas. Please try again later.")
        return

    topic, persona_id, error_message = request_parser.parse_tweet(tweet_text, loaded_personas_data)

    # 3. Handle parsing errors
    if error_message:
        logger.warning(f"Error parsing tweet {tweet.id}: {error_message}")
        # Construct a more user-friendly error message
        reply_error_message = f"Sorry, I couldn't quite understand that. Error: {error_message}. Try format: @BotHandle explain TOPIC by CELEBRITY_NAME"
        twitter_client.post_reply(tweet.id, reply_error_message)
        return
    
    if not topic or not persona_id:
        logger.warning(f"Parsing tweet {tweet.id} did not yield topic or persona_id. Topic: {topic}, Persona ID: {persona_id}")
        twitter_client.post_reply(tweet.id, "Sorry, I couldn't identify both a topic and a celebrity. Please be specific!")
        return

    persona_name = persona_name_map.get(persona_id, "the selected celebrity")
    logger.info(f"Parsed request: Topic='{topic}', PersonaID='{persona_id}' ({persona_name}), Original TweetID={tweet.id}")

    # 4. Generate job_id
    job_id = str(uuid.uuid4())

    # 5. Create job in the main database (e.g., Redis/Postgres)
    try:
        # Assuming db_create_job_direct is available and imported
        db_create_job_direct(job_id=job_id, persona_id=persona_id, query=topic, status="pending")
        logger.info(f"Successfully created job {job_id} in main database for topic '{topic}' by {persona_name}.")
    except Exception as e:
        logger.error(f"Failed to create job {job_id} in database: {e}")
        twitter_client.post_reply(tweet.id, f"Sorry, I had an issue setting up your request for '{topic}' by {persona_name}. Please try again.")
        return

    # 6. Send task to Celery
    try:
        # Assuming celery_app_direct is available and imported
        celery_app_direct.send_task('tasks.job_tasks.process_job', args=[job_id, persona_id, topic])
        logger.info(f"Successfully sent task for job {job_id} to Celery.")
    except Exception as e:
        logger.error(f"Failed to send task for job {job_id} to Celery: {e}")
        # Potentially update DB job status to error here, or handle retry logic
        db_create_job_direct(job_id=job_id, persona_id=persona_id, query=topic, status="error", error_message=f"Celery dispatch failed: {str(e)}")
        twitter_client.post_reply(tweet.id, f"Sorry, I had an issue processing your request for '{topic}' by {persona_name} with our backend. Please try again.")
        return

    # 7. Post initial reply to Twitter
    reply_text = f"Got it! I'll have {persona_name} explain '{topic}'. This might take a few minutes. Your Job ID is: {job_id}"
    twitter_client.post_reply(tweet.id, reply_text)

    # 8. Store job tracking info locally (thread-safe)
    with jobs_cache_lock:
        active_jobs_cache[job_id] = {
            "original_tweet_id": tweet.id,
            "topic": topic,
            "persona_name": persona_name,
            "persona_id": persona_id, # Store persona_id as well
            "status": "processing" # Or "pending_celery_completion"
        }
    logger.info(f"Job {job_id} (original tweet {tweet.id}) added to active_jobs_cache.")

def get_job_tracking_info(job_id):
    """Helper to retrieve job tracking info from the cache, thread-safe."""
    with jobs_cache_lock:
        return active_jobs_cache.get(job_id)

def remove_job_from_tracking(job_id):
    """Helper to remove a job from the cache, thread-safe."""
    with jobs_cache_lock:
        if job_id in active_jobs_cache:
            del active_jobs_cache[job_id]
            logger.info(f"Job {job_id} removed from active_jobs_cache.")
        else:
            logger.warning(f"Attempted to remove job {job_id} from cache, but it was not found.")

def poll_job_statuses():
    """
    Periodically polls the status of active jobs from the database
    and posts results (videos or errors) back to Twitter.
    This function is intended to be run in a separate thread or as a periodic task.
    """
    logger.info("Starting poll_job_statuses thread/task...")
    while True: # Loop indefinitely, or until a shutdown signal
        # Create a snapshot of job IDs to iterate over to avoid issues if cache is modified during iteration by another thread.
        current_job_ids = []
        with jobs_cache_lock:
            current_job_ids = list(active_jobs_cache.keys())
        
        if not current_job_ids:
            # logger.info("No active jobs to poll. Sleeping...")
            pass # Will sleep at the end of the loop
        else:
            logger.info(f"Polling statuses for {len(current_job_ids)} active job(s): {current_job_ids}")

        for job_id in current_job_ids:
            job_tracking_info = get_job_tracking_info(job_id)
            if not job_tracking_info: # Job might have been removed by another thread/process already
                logger.warning(f"Job {job_id} was in current_job_ids but not found in cache. Skipping.")
                continue

            original_tweet_id = job_tracking_info["original_tweet_id"]
            topic = job_tracking_info["topic"]
            persona_name = job_tracking_info["persona_name"]

            try:
                # 1. Fetch job details from the main database
                # Assuming db_get_job_direct is available
                job_details = db_get_job_direct(job_id)

                if not job_details:
                    logger.warning(f"Job {job_id} not found in the main database. Might be an issue or already processed/cleaned up.")
                    # Decide if to remove from local cache or wait longer
                    # For now, let's assume it might appear later or was cleaned up externally.
                    # Consider adding a timestamp to active_jobs_cache entries and removing very old ones.
                    continue
                
                job_status = job_details.get('status')
                logger.info(f"Job {job_id} status from DB: {job_status}")

                # 2. Handle 'completed' status
                if job_status == 'completed':
                    logger.info(f"Job {job_id} completed. Preparing to post video for topic '{topic}' by {persona_name} to tweet {original_tweet_id}.")
                    video_filename = job_details.get("video_filename", "final_video.mp4") # Get actual filename if stored
                    video_file_path = os.path.join(RESULTS_BASE_DIR, job_id, video_filename)
                    
                    media_id = None
                    reply_text_success = f"Here's {persona_name} explaining '{topic}'!"
                    public_video_url = f"{YOUR_PUBLIC_FLASK_URL}/api/jobs/{job_id}"

                    if os.path.exists(video_file_path):
                        try:
                            logger.info(f"Attempting to upload video: {video_file_path} for job {job_id}")
                            media_id = twitter_client.upload_video(video_file_path)
                            if media_id:
                                logger.info(f"Successfully uploaded video for job {job_id}, media_id: {media_id}")
                                twitter_client.post_reply(original_tweet_id, reply_text_success, media_id=media_id)
                            else:
                                logger.warning(f"Failed to upload video {video_file_path} for job {job_id} directly. Posting link instead.")
                                twitter_client.post_reply(original_tweet_id, f"{reply_text_success} Watch it here: {public_video_url}")
                        except Exception as e:
                            logger.error(f"Error uploading video for job {job_id} or posting reply: {e}. Posting link instead.")
                            twitter_client.post_reply(original_tweet_id, f"{reply_text_success} Watch it here: {public_video_url}")
                    else:
                        logger.error(f"Video file not found for job {job_id} at {video_file_path}. Posting link instead.")
                        twitter_client.post_reply(original_tweet_id, f"{reply_text_success} (Video file was not found, but you can try the link): {public_video_url}")
                    
                    remove_job_from_tracking(job_id)

                # 3. Handle 'error' status
                elif job_status == 'error':
                    error_msg_from_db = job_details.get('error_message', 'an unknown error occurred during processing')
                    logger.error(f"Job {job_id} failed with error: {error_msg_from_db}. Notifying user of tweet {original_tweet_id}.")
                    reply_text_error = f"Sorry, I couldn't generate the explanation for '{topic}' by {persona_name}. Error: {error_msg_from_db}"
                    twitter_client.post_reply(original_tweet_id, reply_text_error)
                    remove_job_from_tracking(job_id)
                
                # Other statuses like 'pending', 'processing' are just logged, no action until they become 'completed' or 'error'
                elif job_status in ['pending', 'processing']:
                    logger.info(f"Job {job_id} is still {job_status}. Will check again later.")
                else:
                    logger.warning(f"Job {job_id} has an unexpected status: '{job_status}'. Reviewing.")
                    # Potentially remove from cache if status is unrecoverable or unknown after a while

            except Exception as e:
                logger.error(f"Error processing job {job_id} in poll_job_statuses: {e}. Original tweet: {original_tweet_id}")
                # Decide if to remove from cache or retry. For now, it will be retried on next poll.
                # Consider a retry counter in active_jobs_cache.
        
        # 4. Sleep for a configured interval
        poll_interval = int(os.getenv("JOB_POLL_INTERVAL_SECONDS", 30))
        # logger.info(f"Polling complete. Sleeping for {poll_interval} seconds.")
        time.sleep(poll_interval)
    pass # End of poll_job_statuses

# --- Main Bot Execution (Example) ---
if __name__ == '__main__':
    # This is for example purposes. In a real application, you'd integrate this with your main app.
    
    # 1. Initialize Twitter Client (ensure .env is set up for twitter_client)
    api_v1, api_v2 = twitter_client.init_client()
    if not api_v1 or not api_v2:
        logger.critical("Failed to initialize Twitter API clients. Bot cannot start. Check credentials in .env and twitter_client.py")
        exit(1)
    
    if not twitter_client.TWITTER_BOT_USERNAME or not twitter_client.TWITTER_BEARER_TOKEN:
        logger.critical("TWITTER_BOT_USERNAME or TWITTER_BEARER_TOKEN not set in .env. Cannot start mention listener.")
        exit(1)

    logger.info("Twitter clients initialized.")

    # 2. Start the polling thread for job statuses
    # Make sure poll_job_statuses handles exceptions gracefully within its loop
    polling_thread = threading.Thread(target=poll_job_statuses, daemon=True) # daemon=True allows main program to exit
    polling_thread.start()
    logger.info("Job status polling thread started.")

    # 3. Start listening for mentions (this will block the main thread here)
    logger.info(f"Starting to listen for mentions to @{twitter_client.TWITTER_BOT_USERNAME}...")
    try:
        twitter_client.listen_for_mentions(callback_on_mention=handle_mention)
    except Exception as e:
        logger.critical(f"Mention listener failed: {e}", exc_info=True)
    finally:
        logger.info("Mention listener has stopped.")
        # Signal the polling thread to stop if it doesn't use daemon=True, or handle cleanup.

    # Note: If listen_for_mentions is blocking, code here might not be reached until it stops.
    # For a more robust setup, consider asyncio or a more managed threading/process model. 