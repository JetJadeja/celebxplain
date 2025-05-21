import tweepy
import os
from dotenv import load_dotenv
import logging
import time
import math # For ceiling in video upload
from typing import Optional, Tuple, Callable # Added Optional and Tuple for type hints

# Configure logging for the module
load_dotenv()
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
level = logging.getLevelName(level_str)
logging.basicConfig(level=level, format=log_format)
logger = logging.getLogger(__name__)

# --- Configuration Loading ---
# Load environment variables from .env file, assuming .env is in the parent (server/) directory.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')

APP_DATA_BASE_DIR = os.environ.get('APP_DATA_BASE_DIR', 'data')
# Define the path for storing the since_id
SINCE_ID_FILE = os.path.join(os.path.dirname(__file__), '..', APP_DATA_BASE_DIR, 'since_id.txt')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    logger.info(f"Loaded .env file from: {dotenv_path}")
else:
    logger.warning(
        f".env file not found at {dotenv_path}. Critical Twitter credentials might be missing. "
        "Ensure TWITTER_API_KEY, TWITTER_API_KEY_SECRET, TWITTER_ACCESS_TOKEN, "
        "TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN, and TWITTER_BOT_USERNAME are set."
    )

# Twitter API Credentials and Bot Configuration from Environment Variables
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_KEY_SECRET = os.getenv("TWITTER_API_KEY_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN") # Primarily for v2 App Context or StreamingClient
TWITTER_BOT_USERNAME = os.getenv("TWITTER_BOT_USERNAME") # Bot's own @handle

# Polling interval for checking new mentions (in seconds)
# Twitter API v2 rate limit for GET /2/users/:id/mentions is generous (e.g., 180 reqs / 15 min for user auth).
# Setting this to be configurable via environment variable.
DEFAULT_MENTIONS_POLLING_INTERVAL = 30
MENTIONS_POLLING_INTERVAL = int(os.getenv("MENTIONS_POLLING_INTERVAL_SECONDS", DEFAULT_MENTIONS_POLLING_INTERVAL))

# Global API client objects, initialized by init_client()
# These are intended to be singletons for the application's lifecycle.
api_v1: Optional[tweepy.API] = None
api_v2: Optional[tweepy.Client] = None

# --- Client Initialization ---

def init_client() -> Tuple[Optional[tweepy.API], Optional[tweepy.Client]]:
    """
    Initializes and authenticates Twitter API v1.1 and v2 clients.

    API v1.1 (tweepy.API) is used primarily for media uploads (videos) due to current Twitter API capabilities.
    API v2 (tweepy.Client) is used for most other operations, including fetching mentions and posting tweets.
    
    Credentials are read from environment variables.
    This function should be called once at application startup.

    Returns:
        A tuple (api_v1, api_v2). Each element can be None if its respective initialization failed.
    """
    global api_v1, api_v2

    # Check for essential OAuth 1.0a User Context credentials (used by both v1 and v2 for user actions)
    if not all([TWITTER_API_KEY, TWITTER_API_KEY_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        logger.critical(
            "Missing one or more core Twitter API credentials (API Key, Secret, Access Token, Secret). "
            "These are required for both API v1.1 and v2 user context operations. Bot cannot operate."
        )
        return None, None
    
    if not TWITTER_BEARER_TOKEN:
        # Bearer token is for App Context. While user mentions polling uses User Context,
        # tweepy.Client can accept it, and it might be useful for other v2 endpoints used with App Context.
        logger.warning("TWITTER_BEARER_TOKEN is not set. While not strictly needed for all User Context v2 calls, it might be required for some App Context v2 endpoints.")

    initialized_v1 = False
    try:
        logger.info("Initializing Twitter API v1.1 client...")
        auth_v1 = tweepy.OAuth1UserHandler(
           TWITTER_API_KEY, TWITTER_API_KEY_SECRET,
           TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
        )
        api_v1 = tweepy.API(auth_v1, wait_on_rate_limit=True)
        # Verify v1.1 credentials
        v1_user = api_v1.verify_credentials()
        if v1_user:
            logger.info(f"Twitter API v1.1 client initialized and verified for user: @{v1_user.screen_name}")
            initialized_v1 = True
        else:
            logger.error("Failed to verify credentials for Twitter API v1.1 (verify_credentials returned None/False).")
            api_v1 = None # Nullify on verification failure
    except tweepy.TweepyException as e:
        logger.error(f"Error initializing or verifying Twitter API v1.1 client: {e}", exc_info=True)
        api_v1 = None
    except Exception as e:
        logger.critical(f"Unexpected critical error during Twitter API v1.1 client setup: {e}", exc_info=True)
        api_v1 = None

    initialized_v2 = False
    try:
        logger.info("Initializing Twitter API v2 client...")
        # tweepy.Client uses OAuth 1.0a credentials for User Context if provided (preferred for mentions),
        # can also use bearer_token for App Context or if OAuth 1.0a is missing for some calls.
        api_v2 = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN, # Required for some v2 endpoints, or as primary for App Context
            consumer_key=TWITTER_API_KEY,              # For User Context
            consumer_secret=TWITTER_API_KEY_SECRET,    # For User Context
            access_token=TWITTER_ACCESS_TOKEN,        # For User Context
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET, # For User Context
            wait_on_rate_limit=True
        )
        # Verify v2 credentials by fetching authenticated user's info
        me_response = api_v2.get_me(user_fields=["username"])
        if me_response and me_response.data:
            logger.info(f"Twitter API v2 client initialized and verified for user: @{me_response.data.username} (ID: {me_response.data.id})")
            initialized_v2 = True
        else:
            logger.error(f"Failed to verify credentials for Twitter API v2 (get_me returned no data or error). Response: {me_response}")
            api_v2 = None # Nullify on verification failure
    except tweepy.TweepyException as e:
        logger.error(f"Error initializing or verifying Twitter API v2 client: {e}", exc_info=True)
        api_v2 = None
    except Exception as e:
        logger.critical(f"Unexpected critical error during Twitter API v2 client setup: {e}", exc_info=True)
        api_v2 = None

    if initialized_v1 and initialized_v2:
        logger.info("Both Twitter API v1.1 and v2 clients initialized successfully.")
    elif initialized_v1:
        logger.warning("Twitter API v1.1 client initialized, but API v2 client FAILED. Bot functionality will be limited.")
    elif initialized_v2:
        logger.warning("Twitter API v2 client initialized, but API v1.1 client FAILED. Media uploads will not work.")
    else:
        logger.critical("FAILED to initialize BOTH Twitter API v1.1 and v2 clients. Bot cannot operate effectively.")
        return None, None # Explicitly return None, None if both failed critical setup

    return api_v1, api_v2

# --- Core Twitter Interactions ---

def _read_since_id() -> Optional[int]:
    """Reads the since_id from the SINCE_ID_FILE."""
    if not os.path.exists(SINCE_ID_FILE):
        logger.info(f"Since ID file not found at {SINCE_ID_FILE}. Will fetch latest mention as baseline.")
        return None
    try:
        with open(SINCE_ID_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                logger.info(f"Successfully read since_id {content} from {SINCE_ID_FILE}")
                return int(content)
            else:
                logger.warning(f"Since ID file {SINCE_ID_FILE} is empty.")
                return None
    except ValueError:
        logger.error(f"Invalid content in since_id file {SINCE_ID_FILE}. Could not parse to int.")
        return None
    except IOError as e:
        logger.error(f"IOError reading since_id file {SINCE_ID_FILE}: {e}")
        return None

def _write_since_id(since_id: int) -> None:
    """Writes the since_id to the SINCE_ID_FILE."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(SINCE_ID_FILE), exist_ok=True)
        with open(SINCE_ID_FILE, 'w') as f:
            f.write(str(since_id))
        logger.info(f"Successfully wrote since_id {since_id} to {SINCE_ID_FILE}")
    except IOError as e:
        logger.error(f"IOError writing since_id to file {SINCE_ID_FILE}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error writing since_id {since_id} to {SINCE_ID_FILE}: {e}", exc_info=True)

def listen_for_mentions(callback_on_mention: Callable):
    """
    Periodically polls for new mentions to the bot's authenticated user using Twitter API v2.

    It fetches mentions since the last processed mention to avoid duplicates.
    For each new valid mention, it invokes the `callback_on_mention` function.

    Args:
        callback_on_mention: A function to call for each new mention. 
                             It will receive the Tweepy Tweet object (v2) as an argument.
    Raises:
        RuntimeError: If the API v2 client is not initialized or bot user ID cannot be fetched.
    """
    if not api_v2:
        logger.critical("listen_for_mentions: Twitter API v2 client not initialized. Cannot listen.")
        raise RuntimeError("Twitter API v2 client must be initialized before listening for mentions.")

    if not TWITTER_BOT_USERNAME: # Should also be caught by main.py, but good for client integrity
        logger.critical("listen_for_mentions: TWITTER_BOT_USERNAME is not set. Cannot determine which user to monitor.")
        # While get_me() below uses the authenticated user, TWITTER_BOT_USERNAME is used for logging and consistency checks.
        raise RuntimeError("TWITTER_BOT_USERNAME is not configured.")

    try:
        logger.info("Attempting to retrieve bot's user ID for mention listening...")
        bot_user_response = api_v2.get_me(user_fields=["id", "username"])
        if not bot_user_response or not bot_user_response.data:
            logger.error(f"Could not retrieve bot user information using get_me(). Response: {bot_user_response}")
            raise RuntimeError("Failed to retrieve bot user ID. Cannot listen for mentions.")
        
        bot_user_id = bot_user_response.data.id
        bot_username_from_api = bot_user_response.data.username
        logger.info(f"Successfully fetched bot user details: ID={bot_user_id}, Username=@{bot_username_from_api}. This is the authenticated user.")

        if TWITTER_BOT_USERNAME.lower() != bot_username_from_api.lower():
            logger.warning(
                f"TWITTER_BOT_USERNAME from .env ('{TWITTER_BOT_USERNAME}') does not match authenticated user from API ('{bot_username_from_api}'). "
                f"Will listen for mentions to @{bot_username_from_api} (the authenticated user)."
            )
        # The listener will inherently listen for mentions to the authenticated user (bot_user_id).

    except tweepy.TweepyException as e:
        logger.critical(f"Tweepy error while getting bot user ID: {e}", exc_info=True)
        raise RuntimeError(f"API error getting bot user ID: {e}")
    except Exception as e:
        logger.critical(f"Unexpected error getting bot user ID: {e}", exc_info=True)
        raise RuntimeError(f"Unexpected error getting bot user ID: {e}")

    # Initialize since_id: Try to read from file first.
    last_processed_mention_id = _read_since_id()

    if last_processed_mention_id is None:
        logger.info(f"No valid since_id found in {SINCE_ID_FILE} or file doesn't exist. Fetching initial latest mention ID for @{bot_username_from_api} to set processing baseline...")
        try:
            initial_mentions_response = api_v2.get_users_mentions(
                id=bot_user_id,
                max_results=5, # Only need the very latest one, if any
                tweet_fields=["author_id", "created_at", "conversation_id", "in_reply_to_user_id", "referenced_tweets"]
            )
            if initial_mentions_response.data and len(initial_mentions_response.data) > 0:
                last_processed_mention_id = initial_mentions_response.data[0].id # Newest one is first
                logger.info(f"Initial baseline mention ID set to: {last_processed_mention_id} from Twitter API.")
                _write_since_id(last_processed_mention_id) # Write this new baseline ID
            elif initial_mentions_response.errors:
                for error in initial_mentions_response.errors:
                     logger.error(f"API error during initial mention fetch: {error.get('title', '')} - {error.get('detail', '')}")
                logger.warning("Could not establish baseline due to API errors. Will fetch all new mentions on first poll if no since_id is loaded.") # Clarified log
            else:
                logger.info(f"No recent mentions found for @{bot_username_from_api}. Will process mentions from this point forward if no since_id is loaded.") # Clarified log
        except tweepy.TweepyException as e:
            logger.error(f"Tweepy error fetching initial mentions: {e}. Will proceed without an initial since_id if none was loaded from file.", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error fetching initial mentions: {e}. Will proceed without an initial since_id if none was loaded from file.", exc_info=True)
    else: # A since_id was successfully loaded from the file
        logger.info(f"Successfully loaded last_processed_mention_id {last_processed_mention_id} from {SINCE_ID_FILE}.")

    logger.info(f"Starting to poll for mentions to @{bot_username_from_api} (ID: {bot_user_id}) every {MENTIONS_POLLING_INTERVAL} seconds...")
    
    # Brief pause before starting the loop, e.g., if main thread is also starting up.
    time.sleep(2)

    while True:
        logger.info(f"Mention polling cycle START for @{bot_username_from_api} (ID: {bot_user_id}). Since_id: {last_processed_mention_id}")
        try:
            # logger.debug(f"Polling for new mentions for user ID {bot_user_id} (since_id: {last_processed_mention_id})...")
            logger.info(f"Attempting to fetch mentions for user ID {bot_user_id} (since_id: {last_processed_mention_id})...")
            
            mentions_response = api_v2.get_users_mentions(
                id=bot_user_id,
                since_id=last_processed_mention_id,
                tweet_fields=["author_id", "created_at", "text", "conversation_id", "in_reply_to_user_id", "referenced_tweets"],
                expansions=["author_id"], # To get user object for author_id (e.g., username)
                max_results=25  # Fetch a batch of new mentions (max 100)
            )

            if mentions_response.errors:
                logger.info(f"Received errors from get_users_mentions API: {mentions_response.errors}")
                for error in mentions_response.errors:
                    logger.error(f"Twitter API error when fetching mentions: {error.get('title', '')} - {error.get('detail', '')} (Value: {error.get('value', '')})")
                # Continue to next polling cycle after logging errors.
                # Specific error codes (e.g., 429) are handled by wait_on_rate_limit=True in client.

            new_mentions_processed_this_cycle = 0
            if mentions_response.data:
                # Mentions are returned newest first when since_id is used.
                # To process them chronologically (oldest of the new batch first), reverse the list.
                tweets_to_process = reversed(mentions_response.data)
                logger.info(f"Found {len(mentions_response.data)} new mention(s) to process.")
                
                for tweet in tweets_to_process:
                    # Basic check: ensure the tweet is not from the bot itself replying to something.
                    # Note: `get_users_mentions` should ideally not return self-mentions if properly a mention to the bot.
                    # However, checking tweet.author_id against bot_user_id can prevent processing self-replies if they slip through.
                    if str(tweet.author_id) == str(bot_user_id):
                        logger.info(f"Skipping mention from bot itself (Tweet ID: {tweet.id}, Author ID: {tweet.author_id}, Bot ID: {bot_user_id})")
                        # Update last_processed_mention_id even for skipped self-mentions to advance past them
                        if tweet.id > (last_processed_mention_id or 0): # Ensure it's greater
                             last_processed_mention_id = tweet.id
                        continue # Skip processing this tweet further

                    logger.info(f"Processing mention: Tweet ID {tweet.id}, Author ID {tweet.author_id}, Text: \"{tweet.text}\"") # Corrected logging parenthesis
                    
                    try:
                        # Invoke the callback function passed to listen_for_mentions
                        # This function (e.g., bot_logic.handle_mention) is responsible for the core logic
                        callback_on_mention(tweet)
                        
                        # If callback was successful, update last_processed_mention_id
                        # We use the ID of the current tweet as it's the latest one processed in this iteration.
                        if tweet.id > (last_processed_mention_id or 0): # Ensure it's greater, handles initial None
                            last_processed_mention_id = tweet.id
                        
                        new_mentions_processed_this_cycle += 1
                    except Exception as e:
                        # Log error from callback processing, but continue loop to process other mentions
                        # and to ensure the polling doesn't die from one bad tweet.
                        logger.error(f"Error processing mention (Tweet ID: {tweet.id}) with callback: {e}", exc_info=True)
                        # Decide if last_processed_mention_id should be updated even on callback error.
                        # Generally, yes, to avoid reprocessing a problematic tweet indefinitely.
                        if tweet.id > (last_processed_mention_id or 0):
                             last_processed_mention_id = tweet.id

                if new_mentions_processed_this_cycle > 0:
                    logger.info(f"Successfully processed {new_mentions_processed_this_cycle} new mention(s) in this cycle.")
                    if last_processed_mention_id: # Make sure we have a valid ID to write
                        _write_since_id(last_processed_mention_id)
                else:
                    if mentions_response.data : # Found mentions but all were skipped (e.g. self-mentions)
                        logger.info("No new, actionable mentions processed this cycle (e.g., all were self-mentions or skipped).")
                        if last_processed_mention_id: # Still, if last_processed_mention_id was updated (e.g. by skipping self-mentions), write it
                            _write_since_id(last_processed_mention_id)
                    else: # No mentions data at all
                         logger.info("No new mentions found in this polling cycle.")
                         # No need to write since_id if it hasn't changed and no mentions were fetched.
                         # However, if it was initialized to None and then set from API, it would have been written already.

            else: # No mentions_response.data
                logger.info("No new mentions found in this polling cycle.")

        except tweepy.TweepyException as e:
            logger.error(f"Tweepy API error during mention polling loop: {e}", exc_info=True)
            # wait_on_rate_limit=True in Client handles rate limit sleeps.
            # If other critical API errors occur, they are logged here. Consider specific error code handling if needed.
        except Exception as e:
            logger.error(f"Unexpected error in mention polling loop: {e}", exc_info=True)
            # For unexpected errors, a slightly longer sleep might prevent rapid failure loops.
            time.sleep(MENTIONS_POLLING_INTERVAL * 2) # Double sleep on unexpected error
        
        # logger.debug(f"Mention polling cycle complete. Sleeping for {MENTIONS_POLLING_INTERVAL} seconds.")
        logger.info(f"Mention polling cycle for @{bot_username_from_api} COMPLETE. Sleeping for {MENTIONS_POLLING_INTERVAL} seconds.")
        time.sleep(MENTIONS_POLLING_INTERVAL)

# Define retry parameters for posting replies
MAX_POST_RETRIES = int(os.getenv("TWITTER_POST_MAX_RETRIES", 3))
POST_RETRY_DELAY_SECONDS = int(os.getenv("TWITTER_POST_RETRY_DELAY_SECONDS", 5))
# Define specific HTTP status codes that should not be retried (e.g., auth issues, bad requests)
NON_RETRYABLE_STATUS_CODES = [400, 401, 403, 404] # Bad Request, Unauthorized, Forbidden, Not Found

def post_reply(tweet_id: str, text: str, media_id: Optional[str] = None) -> Optional[tweepy.Response]:
    """
    Posts a reply to a given tweet_id. Optionally attaches media (e.g., a video).
    Uses Twitter API v2.

    Args:
        tweet_id: The ID of the tweet to reply to.
        text: The text content of the reply.
        media_id: Optional. The media ID of an uploaded media file (e.g., video) to attach.

    Returns:
        A tweepy.Response object if successful, None otherwise.
    """
    if not api_v2:
        logger.error("post_reply: Twitter API v2 client not initialized. Cannot post reply.")
        return None

    reply_params = {"in_reply_to_tweet_id": tweet_id, "text": text}
    if media_id:
        reply_params["media_ids"] = [media_id]

    for attempt in range(MAX_POST_RETRIES):
        try:
            logger.info(f"Attempt {attempt + 1}/{MAX_POST_RETRIES} to post reply to tweet_id: {tweet_id}. Text: '{text[:100]}...', Media ID: {media_id}")
            response = api_v2.create_tweet(**reply_params)
            
            if response.data and response.data.get("id"):
                logger.info(f"Successfully posted reply. New Tweet ID: {response.data['id']} in reply to {tweet_id} on attempt {attempt + 1}.")
                return response
            else:
                # This case might indicate a non-exception failure from Twitter, or unexpected response structure
                logger.error(f"Failed to post reply to tweet {tweet_id} on attempt {attempt + 1}. Response data missing ID. Errors: {response.errors or response}")
                # Check if there are specific errors in response.errors that might be non-retryable
                if response.errors:
                    for error in response.errors:
                        # Example: Twitter API v2 often returns errors with a 'status' field in the error object for some endpoints
                        # For create_tweet, error details might be in 'title' or by inspecting the structure.
                        # This is a heuristic. The actual error structure for create_tweet might need specific handling.
                        # For now, if there are errors, we treat it as a potentially retryable failure unless caught by TweepyException status codes.
                        logger.warning(f"Error detail from Twitter: {error}") 
                # Consider this a failure for this attempt, will retry if attempts remain.
                # If we want to break early for certain response.errors, add logic here.

        except tweepy.TweepyException as e:
            logger.warning(f"Tweepy API error on attempt {attempt + 1}/{MAX_POST_RETRIES} posting reply to tweet {tweet_id}: {e}")
            
            # Check for non-retryable status codes from the exception's response object
            status_code = getattr(e.response, 'status_code', None)
            if status_code in NON_RETRYABLE_STATUS_CODES:
                logger.error(f"Non-retryable error (HTTP {status_code}) for tweet {tweet_id}. Aborting retries. Error: {e}")
                if hasattr(e, 'api_codes') and hasattr(e, 'api_messages'): # Log more details if available
                     logger.error(f"API Error Codes: {e.api_codes}, Messages: {e.api_messages}")
                return None # Do not retry for these errors

            # Log specific error details if available from the exception itself
            if hasattr(e, 'api_codes') and hasattr(e, 'api_messages'):
                logger.error(f"API Error Codes: {e.api_codes}, Messages: {e.api_messages}")
            else:
                logger.error(f"Full error details: {e}") # Fallback to generic error string

            if attempt < MAX_POST_RETRIES - 1:
                logger.info(f"Waiting {POST_RETRY_DELAY_SECONDS} seconds before next retry...")
                time.sleep(POST_RETRY_DELAY_SECONDS)
            else:
                logger.error(f"All {MAX_POST_RETRIES} attempts failed for tweet {tweet_id}.")
                return None # All retries exhausted
                
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}/{MAX_POST_RETRIES} posting reply to tweet {tweet_id}: {e}", exc_info=True)
            if attempt < MAX_POST_RETRIES - 1:
                logger.info(f"Waiting {POST_RETRY_DELAY_SECONDS} seconds before next retry due to unexpected error...")
                time.sleep(POST_RETRY_DELAY_SECONDS)
            else:
                logger.error(f"All {MAX_POST_RETRIES} attempts failed due to unexpected errors for tweet {tweet_id}.")
                return None # All retries exhausted

    logger.error(f"Failed to post reply to tweet {tweet_id} after {MAX_POST_RETRIES} attempts.") # Should be reached if loop finishes without returning
    return None


def upload_video(video_filepath: str, max_retries_status_check=int(os.getenv("TWITTER_UPLOAD_MAX_RETRIES_STATUS_CHECK", 24)), status_check_interval=int(os.getenv("TWITTER_UPLOAD_STATUS_CHECK_INTERVAL_SECONDS", 5))) -> Optional[str]:
    """
    Uploads a video to Twitter using the v1.1 chunked media upload API.
    This is necessary as API v2 does not yet fully support large video uploads in the same manner.

    Args:
        video_filepath: Absolute path to the video file.
        max_retries_status_check: Max number of times to check video processing status.
        status_check_interval: Seconds to wait between status checks.

    Returns:
        The Twitter media_id string if upload and processing are successful, None otherwise.
    """
    if not api_v1:
        logger.error("upload_video: Twitter API v1.1 client not initialized. Cannot upload video.")
        return None

    if not os.path.exists(video_filepath):
        logger.error(f"upload_video: Video file not found at {video_filepath}")
        return None

    try:
        file_size = os.path.getsize(video_filepath)
        logger.info(f"Starting video upload for: {video_filepath} (Size: {file_size / (1024*1024):.2f} MB)")

        # 1. INIT Phase: Initialize the upload
        # Max video size for Twitter is 512MB. Max duration 140s. MP4 recommended.
        # tweepy.Media.media_category can be 'tweet_video' for videos attached to tweets.
        logger.debug("Video Upload - INIT phase")
        media_upload_response = api_v1.media_upload(
            filename=video_filepath, 
            media_category='tweet_video', 
            chunked=True # Explicitly use chunked for clarity, though media_upload handles it.
        )
        media_id = media_upload_response.media_id_string
        logger.info(f"Video Upload - INIT successful. Media ID: {media_id}")

        # api_v1.media_upload with chunked=True and wait_for_completion=False handles INIT, APPENDs, and FINALIZE internally
        # when you pass the filename directly. It doesn't return until FINALIZE is at least attempted.
        # However, the processing might still be ongoing.

        # 2. STATUS Phase: Check processing status until success or failure
        logger.info(f"Video Upload - STATUS phase. Checking processing status for media_id: {media_id}")
        retries = 0
        while retries < max_retries_status_check:
            try:
                upload_status = api_v1.get_media_upload_status(media_id)
                state = upload_status.processing_info.get('state')
                progress_percent = upload_status.processing_info.get('progress_percent', 0)
                
                logger.info(f"Media ID {media_id} processing status: {state}, Progress: {progress_percent}%")

                if state == 'succeeded':
                    logger.info(f"Video processing for media_id {media_id} SUCCEEDED.")
                    return media_id
                elif state == 'failed':
                    error_name = upload_status.processing_info.get('error', {}).get('name', 'Unknown Error')
                    error_message = upload_status.processing_info.get('error', {}).get('message', 'No details provided.')
                    logger.error(f"Video processing for media_id {media_id} FAILED. Error: {error_name} - {error_message}")
                    return None
                elif state == 'in_progress' or state == 'pending':
                    logger.info(f"Video processing for media_id {media_id} is '{state}'. Waiting {status_check_interval}s...")
                    time.sleep(status_check_interval)
                    retries += 1
                else: # Unknown state
                    logger.warning(f"Media ID {media_id} in unexpected processing state: '{state}'. Retrying... Details: {upload_status.processing_info}")
                    time.sleep(status_check_interval)
                    retries += 1
            except tweepy.TweepyException as status_exc:
                logger.error(f"Tweepy error checking upload status for media_id {media_id}: {status_exc}. Retrying...")
                time.sleep(status_check_interval * 2) # Longer sleep on API error during status check
                retries += 1 # Count as a retry
            except Exception as e_stat:
                logger.error(f"Unexpected error checking upload status for media ID {media_id}: {e_stat}", exc_info=True)
                time.sleep(status_check_interval * 2)
                retries += 1

        logger.error(f"Video processing for media_id {media_id} timed out after {max_retries_status_check * status_check_interval}s. Last state was likely pending/in_progress.")
        return None

    except tweepy.TweepyException as e_upload:
        logger.error(f"Tweepy API error during video upload process for {video_filepath}: {e_upload}", exc_info=True)
        if hasattr(e_upload, 'api_codes') and hasattr(e_upload, 'api_messages'):
            logger.error(f"API Error Codes: {e_upload.api_codes}, Messages: {e_upload.api_messages}")
        return None
    except Exception as e_final:
        logger.error(f"Unexpected critical error during video upload for {video_filepath}: {e_final}", exc_info=True)
        return None

# --- Other Utility Functions ---

def get_tweet_details(tweet_id: str) -> Optional[tweepy.Tweet]:
    """
    Fetches detailed information for a specific tweet using API v2.

    Args:
        tweet_id: The ID of the tweet to fetch.

    Returns:
        A tweepy.Tweet object if found, None otherwise.
    """
    if not api_v2:
        logger.error("get_tweet_details: Twitter API v2 client not initialized.")
        return None
    try:
        logger.info(f"Fetching details for tweet_id: {tweet_id}")
        # Common fields: attachments, author_id, context_annotations, conversation_id, created_at,
        # entities, geo, id, in_reply_to_user_id, lang, public_metrics, possibly_sensitive,
        # referenced_tweets, reply_settings, source, text, withheld
        response = api_v2.get_tweet(
            id=tweet_id,
            tweet_fields=["author_id", "created_at", "text", "public_metrics", "conversation_id", "in_reply_to_user_id", "referenced_tweets"],
            expansions=["author_id"]
        )
        if response.data:
            logger.info(f"Successfully fetched details for tweet {tweet_id}.")
            return response.data
        else:
            logger.warning(f"Could not find tweet or no data returned for tweet_id {tweet_id}. Errors: {response.errors}")
            return None
    except tweepy.TweepyException as e:
        logger.error(f"Tweepy API error fetching tweet details for {tweet_id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching tweet details for {tweet_id}: {e}", exc_info=True)
        return None

# Note: get_tweet_text, get_user_profile, search_tweets, follow_user can be added similarly
# if they are essential to the core bot logic being refactored now. For brevity, focusing on core loop.
# Example for one more to show pattern:

def get_user_profile(user_id: Optional[str] = None, username: Optional[str] = None) -> Optional[tweepy.User]:
    """
    Fetches a user's profile using API v2, by user_id or username.
    At least one identifier must be provided.

    Args:
        user_id: The ID of the user.
        username: The username (handle) of the user.

    Returns:
        A tweepy.User object if found, None otherwise.
    """
    if not api_v2:
        logger.error("get_user_profile: Twitter API v2 client not initialized.")
        return None
    
    if not user_id and not username:
        logger.error("get_user_profile: Must provide either user_id or username.")
        return None

    try:
        if user_id:
            logger.info(f"Fetching user profile for user_id: {user_id}")
            response = api_v2.get_user(id=user_id, user_fields=["created_at", "description", "location", "public_metrics", "verified"])
        else: # username must be provided
            logger.info(f"Fetching user profile for username: @{username}")
            response = api_v2.get_user(username=username, user_fields=["created_at", "description", "location", "public_metrics", "verified"])
        
        if response.data:
            logger.info(f"Successfully fetched profile for: {response.data.username} (ID: {response.data.id})")
            return response.data
        else:
            logger.warning(f"Could not find user or no data returned. User ID: {user_id}, Username: {username}. Errors: {response.errors}")
            return None
    except tweepy.TweepyException as e:
        logger.error(f"Tweepy API error fetching user profile (ID: {user_id}, User: {username}): {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching user profile (ID: {user_id}, User: {username}): {e}", exc_info=True)
        return None