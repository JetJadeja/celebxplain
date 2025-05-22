import logging
import uuid
import os
import json
import time
import threading # For running poll_job_statuses in a separate thread
from dotenv import load_dotenv

# Imports assuming 'server/' is in sys.path, as configured by main.py
from twitter_bot import twitter_client
from twitter_bot import request_parser
from utils.db import (
    create_job as db_create_job_direct, 
    get_job as db_get_job_direct, 
    update_job_status as db_update_job_status_direct,
    # get_db_connection, # No longer directly used here
    get_pending_twitter_replies, # Import the new helper function
    get_job_by_tweet_id, # New import to check for existing jobs
    mark_job_reply_posted # New import for marking jobs as replied
)
from celery_app import celery_app as celery_app_direct

load_dotenv()
# Configure logging
level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
level = logging.getLevelName(level_str)
logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration & Data Placeholders ---
MAX_REPLY_ATTEMPTS_PER_SESSION = int(os.getenv("MAX_REPLY_ATTEMPTS_PER_SESSION", 2))

APP_DATA_BASE_DIR = os.environ.get('APP_DATA_BASE_DIR', 'data')
# Load personas data once when the module is loaded
PERSONAS_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", APP_DATA_BASE_DIR, "personas.json")
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
    
    # First, check if we already have a job for this tweet ID to prevent duplicates on restart
    existing_job = get_job_by_tweet_id(str(tweet.id))
    if existing_job:
        logger.info(f"Job already exists for Tweet ID {tweet.id}: Job ID {existing_job['id']}, Status: {existing_job['status']}. Skipping job creation.")
        # Update since_id here to mark this tweet as processed, even though we're not creating a new job
        twitter_client.update_since_id_after_reply(str(tweet.id))
        return

    # 2. Parse the tweet to get topic, persona_id, and any error
    # Ensure loaded_personas_data is available
    if not loaded_personas_data or not persona_name_map:
        logger.error("Personas data not loaded. Cannot process tweet.")
        twitter_client.post_reply(tweet.id, "Sorry, there's a configuration issue with my personas. Please try again later.")
        return

    topic, persona_id, error_message = request_parser.parse_tweet(tweet_text, loaded_personas_data)

    # 3. Handle parsing errors
    if error_message:
        logger.warning(f"Error parsing tweet {tweet.id}: {error_message}. No reply will be sent for this error.")
        # Construct a more user-friendly error message
        # reply_error_message = f"Sorry, I couldn't quite understand that. Error: {error_message}. Try format: @BotHandle explain TOPIC by CELEBRITY_NAME"
        # twitter_client.post_reply(tweet.id, reply_error_message)
        return
    
    if not topic or not persona_id:
        logger.warning(f"Parsing tweet {tweet.id} did not yield topic or persona_id. Topic: {topic}, Persona ID: {persona_id}. No reply will be sent.")
        # twitter_client.post_reply(tweet.id, "Sorry, I couldn't identify both a topic and a celebrity. Please be specific!")
        return

    persona_name = persona_name_map.get(persona_id, "the selected celebrity")
    logger.info(f"Parsed request: Topic='{topic}', PersonaID='{persona_id}' ({persona_name}), Original TweetID={tweet.id}")

    # 4. Generate job_id
    job_id = str(uuid.uuid4())

    # 5. Create job in the main database (e.g., Redis/Postgres)
    try:
        # Assuming db_create_job_direct is available and imported
        # create_job in db.py automatically sets initial status to 'created'
        db_create_job_direct(
            job_id=job_id, 
            persona_id=persona_id, 
            query=topic,
            original_tweet_id=str(tweet.id),  # Pass the original tweet ID
            original_tweet_author_id=str(tweet.author_id)  # Pass the original tweet author ID
        )
        logger.info(f"Successfully created job {job_id} in main database for topic '{topic}' by {persona_name} (TweetID: {tweet.id}). Initial status: 'created'.")
    except Exception as e:
        logger.error(f"Failed to create job {job_id} in database: {e}")
        return

    # 6. Send task to Celery
    try:
        # Assuming celery_app_direct is available and imported
        celery_app_direct.send_task('tasks.job_tasks.process_job', args=[job_id, persona_id, topic])
        logger.info(f"Successfully sent task for job {job_id} to Celery.")
        # Update job status to 'processing' or 'pending' after successful dispatch
        db_update_job_status_direct(job_id=job_id, status="processing", message="Task sent to Celery for processing.")
        logger.info(f"Updated job {job_id} status to 'processing' in database.")
    except Exception as e:
        logger.error(f"Failed to send task for job {job_id} to Celery: {e}")
        # Update DB job status to error here
        db_update_job_status_direct(job_id=job_id, status="error", error=f"Celery dispatch failed: {str(e)}", message=f"Celery dispatch failed: {str(e)}")
        logger.error(f"Updated job {job_id} status to 'error' in database due to Celery dispatch failure.")
        return

    # 8. Store job tracking info locally (thread-safe)
    with jobs_cache_lock:
        active_jobs_cache[job_id] = {
            "original_tweet_id": str(tweet.id), # Ensure it's a string, matching DB practice
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

    def get_persona_name_from_id_local(persona_id_local):
        # Accesses the global persona_name_map
        return persona_name_map.get(persona_id_local, "the selected celebrity")

    while True: # Loop indefinitely, or until a shutdown signal
        jobs_to_process_this_cycle = {} # job_id -> {details for reply}

        try:
            # Part 1: Query DB for Twitter-originated jobs that are completed or errored
            # Replace direct DB access with call to helper function
            potential_jobs_for_reply_rows = get_pending_twitter_replies()
            
            with jobs_cache_lock: # Protect access to active_jobs_cache
                for job_row_dict in potential_jobs_for_reply_rows: # It now returns a list of dicts
                    job_id = job_row_dict['id'] 
                    
                    # Check if we've already marked this job for reply attempt in this session
                    if job_id in active_jobs_cache and active_jobs_cache[job_id].get("reply_attempted_this_session", False):
                        # logger.debug(f"Job {job_id} already processed for reply in this session. Skipping.")
                        continue # Skip if already handled in this session

                    # This job is a candidate for replying.
                    # Reconstruct details for the reply.
                    jobs_to_process_this_cycle[job_id] = {
                        "original_tweet_id": job_row_dict["original_tweet_id"],
                        "topic": job_row_dict["query"], # DB 'query' column maps to 'topic'
                        "persona_id": job_row_dict["persona_id"],
                        "persona_name": get_persona_name_from_id_local(job_row_dict["persona_id"]),
                        "db_status": job_row_dict["status"],
                        "video_url": job_row_dict["result_url"], # This is jobs.result_url from DB (likely S3 URL)
                        "db_error_message": job_row_dict["error"],
                        "reply_attempted_this_session": False, # Initialize/reset flag
                        "reply_attempts_in_session": 0 # Initialize reply_attempts_in_session
                    }
                    
                    # Update active_jobs_cache: if job_id exists, update it; otherwise, add it.
                    # This ensures cache reflects what we are about to process for reply.
                    if job_id not in active_jobs_cache:
                        active_jobs_cache[job_id] = {} # Initialize if new to cache
                    
                    active_jobs_cache[job_id].update(jobs_to_process_this_cycle[job_id])
                    logger.info(f"Job {job_id} (Tweet: {job_row_dict['original_tweet_id']}) identified from DB for reply processing. Status: {job_row_dict['status']}.")

            # Part 2: Process jobs identified for reply in this cycle
            if not jobs_to_process_this_cycle:
                # logger.info("No new Twitter jobs found in DB needing immediate reply this cycle.")
                pass
            else:
                logger.info(f"Attempting to process replies for {len(jobs_to_process_this_cycle)} job(s): {list(jobs_to_process_this_cycle.keys())}")

            for job_id, details in jobs_to_process_this_cycle.items():
                original_tweet_id = details["original_tweet_id"]
                topic = details["topic"]
                persona_name = details["persona_name"]
                db_status = details["db_status"]
                video_url = details["video_url"]
                db_error_message = details["db_error_message"]
                reply_attempts_in_session = details.get("reply_attempts_in_session", 0)
                
                reply_action_taken = False # Flag to indicate if a reply attempt (success or fail) was made
                reply_posted_successfully = False # Flag to indicate if Twitter API confirmed post

                try:
                    if reply_attempts_in_session >= MAX_REPLY_ATTEMPTS_PER_SESSION:
                        logger.warning(f"Job {job_id} (Tweet: {original_tweet_id}) has reached max reply attempts ({reply_attempts_in_session}/{MAX_REPLY_ATTEMPTS_PER_SESSION}) in this session. Skipping further reply attempts.")
                        reply_action_taken = True # Mark as action taken to prevent loop, effectively stopping retries this session
                        # Ensure it's marked as "attempted" in the main cache to stop for this session
                        with jobs_cache_lock:
                            if job_id in active_jobs_cache:
                                active_jobs_cache[job_id]["reply_attempted_this_session"] = True
                                active_jobs_cache[job_id]["reply_attempts_in_session"] = reply_attempts_in_session # Persist the count
                        continue # Skip to next job

                    if db_status == 'completed':
                        logger.info(f"Job {job_id} 'completed'. Attempting reply for topic '{topic}' by {persona_name} to tweet {original_tweet_id} (Attempt {reply_attempts_in_session + 1}/{MAX_REPLY_ATTEMPTS_PER_SESSION}).")
                        reply_text_success = f"Here's {persona_name} explaining '{topic}'!"

                        # Construct local path to the generated video file
                        job_result_dir = os.path.join(RESULTS_BASE_DIR, job_id)
                        video_file_path = os.path.join(job_result_dir, "final_video.mp4")
                        
                        # Check if the video file exists locally
                        if os.path.exists(video_file_path):
                            logger.info(f"Found local video file for job {job_id} at: {video_file_path}. Uploading to Twitter.")
                            try:
                                # Attempt to upload the video and get a media_id
                                media_id = twitter_client.upload_video(video_file_path)
                                if media_id:
                                    # Post reply with the uploaded video
                                    logger.info(f"Video for job {job_id} successfully uploaded to Twitter. Media ID: {media_id}")
                                    response = twitter_client.post_reply(original_tweet_id, reply_text_success, media_id)
                                else:
                                    logger.error(f"Failed to upload video for job {job_id} to Twitter. No media_id returned.")
                                    response = twitter_client.post_reply(original_tweet_id, f"Sorry, I finished processing '{topic}' by {persona_name}, but there was an issue uploading the video to Twitter.")
                            except Exception as e:
                                logger.error(f"Error uploading video for job {job_id} to Twitter: {e}", exc_info=True)
                                response = twitter_client.post_reply(original_tweet_id, f"Sorry, I finished processing '{topic}' by {persona_name}, but encountered an error when uploading the video to Twitter.")
                        else:
                            # Neither local file nor URL is available
                            logger.error(f"Job {job_id} completed but neither local video file at {video_file_path} nor video_url found. Cannot post video.")
                            response = twitter_client.post_reply(original_tweet_id, f"Sorry, I finished processing '{topic}' by {persona_name}, but there was an issue retrieving the video.")
                        
                        if response: # twitter_client.post_reply returns a response object on success
                            reply_posted_successfully = True
                            # Mark this job as replied in the database
                            mark_job_reply_posted(job_id)
                            logger.info(f"Job {job_id} marked as replied in the database")
                        reply_action_taken = True

                    elif db_status == 'error':
                        error_message_to_post = db_error_message or 'an unknown error occurred during processing'
                        logger.error(f"Job {job_id} 'error': {error_message_to_post}. Attempting error reply to tweet {original_tweet_id} (Attempt {reply_attempts_in_session + 1}/{MAX_REPLY_ATTEMPTS_PER_SESSION}).")
                        reply_text_error = f"Sorry, I couldn't generate the explanation for '{topic}' by {persona_name}. Error: {error_message_to_post}"
                        response = twitter_client.post_reply(original_tweet_id, reply_text_error)
                        if response:
                            reply_posted_successfully = True
                            # Mark this job as replied in the database
                            mark_job_reply_posted(job_id)
                            logger.info(f"Job {job_id} marked as replied in the database")
                        reply_action_taken = True

                    # After attempting to reply (successfully or not), mark it in the cache for this session.
                    if reply_action_taken:
                        with jobs_cache_lock:
                            if job_id in active_jobs_cache:
                                if reply_posted_successfully:
                                    active_jobs_cache[job_id]["reply_attempted_this_session"] = True
                                    logger.info(f"Successfully posted reply for job {job_id}. Marked as reply_attempted_this_session=True.")
                                else: # post_reply failed despite its internal retries
                                    active_jobs_cache[job_id]["reply_attempts_in_session"] = reply_attempts_in_session + 1
                                    logger.warning(f"Failed to post reply for job {job_id} via twitter_client.post_reply. Attempt count now {active_jobs_cache[job_id]['reply_attempts_in_session']}.")
                                    if active_jobs_cache[job_id]["reply_attempts_in_session"] >= MAX_REPLY_ATTEMPTS_PER_SESSION:
                                        active_jobs_cache[job_id]["reply_attempted_this_session"] = True # Stop trying this session
                                        logger.error(f"Job {job_id} reached max reply attempts for this session. Marking reply_attempted_this_session=True.")
                                # Consider removing from cache if truly done: del active_jobs_cache[job_id]
                                # Or, for more robust multi-instance handling, update DB to a final "replied_to_twitter" status here.

                except Exception as e_reply:
                    logger.error(f"Error during reply processing for job {job_id} (Tweet: {original_tweet_id}): {e_reply}", exc_info=True)
                    # Do not set reply_attempted_this_session to True if the attempt itself failed, to allow retry.
                    # However, if post_reply itself has retries, this might lead to multiple replies.
                    # For now, if an exception occurs here, it implies the twitter_client.post_reply failed, 
                    # so we DON'T mark reply_attempted_this_session as True, allowing a retry in the next cycle.
                    pass # Error already logged

        except Exception as e_outer:
            logger.error(f"Outer error in poll_job_statuses loop: {e_outer}", exc_info=True)
        
        # Sleep for a configured interval
        poll_interval = int(os.getenv("JOB_POLL_INTERVAL_SECONDS", 30))
        time.sleep(poll_interval)
    # pass # End of poll_job_statuses -> This pass is not needed due to while True

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