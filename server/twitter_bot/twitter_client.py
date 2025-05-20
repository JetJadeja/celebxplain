import tweepy
import os
from dotenv import load_dotenv
import logging
import time # Added for potential use in upload_video status checking

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
# Assuming .env is in the server/ directory, one level up
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_KEY_SECRET = os.getenv("TWITTER_API_KEY_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN") # Needed for StreamingClient with v2
TWITTER_BOT_USERNAME = os.getenv("TWITTER_BOT_USERNAME") # To identify the bot

# Global API objects, initialized by init_client
api_v1 = None
api_v2 = None

def init_client():
    """
    Initialize and authenticate the Twitter client for v1.1 API (for media) and v2 API (for streaming/general use).
    Returns a tuple (api_v1, api_v2) or (None, None) if initialization fails.
    """
    global api_v1, api_v2

    if not all([TWITTER_API_KEY, TWITTER_API_KEY_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN]):
        logger.error("Missing one or more Twitter API credentials. Please check your .env file.")
        return None, None

    try:
        # Initialize v1.1 API (for media uploads, some specific actions)
        auth = tweepy.OAuth1UserHandler(
           TWITTER_API_KEY, TWITTER_API_KEY_SECRET,
           TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
        )
        api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
        logger.info("Twitter API v1.1 client initialized successfully.")

        # Initialize v2 API (for streaming, modern endpoints)
        api_v2 = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_KEY_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        logger.info("Twitter API v2 client initialized successfully.")
        
        # Verify credentials for both clients
        if not api_v1.verify_credentials():
            logger.error("Failed to verify credentials for Twitter API v1.1.")
            api_v1 = None
        if not api_v2.get_me(): # A simple way to test v2 client
             logger.error("Failed to verify credentials for Twitter API v2.")
             api_v2 = None

        if api_v1 and api_v2:
            logger.info("Both Twitter clients authenticated successfully.")
            return api_v1, api_v2
        else:
            logger.error("One or both Twitter clients failed to authenticate.")
            return None, None

    except Exception as e:
        logger.error(f"Error initializing Twitter clients: {e}")
        return None, None

class MentionStreamListener(tweepy.StreamingClient):
    def __init__(self, bearer_token, callback_on_mention, bot_user_id):
        super().__init__(bearer_token)
        self.callback_on_mention = callback_on_mention
        self.bot_user_id = bot_user_id
        logger.info(f"MentionStreamListener initialized for bot ID: {self.bot_user_id}")

    def on_tweet(self, tweet):
        """
        This method is called when a tweet matching the stream's filter rules is received.
        For mentions, the tweet object itself (from v2) contains the mention information.
        """
        logger.info(f"Received tweet: {tweet.id} - {tweet.text}")
        # Check if the bot was mentioned (v2 Tweet object structure)
        # The stream rule `@bot_username` should already filter this,
        # but an explicit check can be useful.
        # Also ensure it's not a reply from the bot itself to avoid loops.
        if tweet.author_id != self.bot_user_id:
            logger.info(f"Tweet is a mention and not from the bot. Calling callback for tweet ID: {tweet.id}")
            try:
                self.callback_on_mention(tweet)
            except Exception as e:
                logger.error(f"Error in mention callback for tweet {tweet.id}: {e}")
        else:
            logger.info(f"Tweet {tweet.id} is from the bot itself or does not mention the bot, ignoring.")


    def on_error(self, status_code):
        logger.error(f"Streaming error occurred: {status_code}")
        if status_code == 420: # Rate limit
            logger.warning("Rate limit exceeded by streaming client. Disconnecting.")
            return False # Disconnect stream
        return True # Keep stream connected for other errors

    def on_exception(self, exception):
        logger.error(f"Streaming exception: {exception}")
        # Decide if you want to disconnect or keep trying
        # return False # to disconnect

def listen_for_mentions(callback_on_mention):
    """
    Stream mentions to the bot's username. The callback will process the tweet.
    Uses Twitter API v2.
    """
    global api_v1, api_v2 # Use the globally initialized clients
    
    if not api_v2:
        logger.error("Twitter API v2 client not initialized. Call init_client() first.")
        return

    if not TWITTER_BOT_USERNAME:
        logger.error("TWITTER_BOT_USERNAME is not set in .env file. Cannot listen for mentions.")
        return

    try:
        # Get bot's user ID using the v2 client
        bot_user_info = api_v2.get_user(username=TWITTER_BOT_USERNAME)
        if not bot_user_info.data:
            logger.error(f"Could not find user ID for username: {TWITTER_BOT_USERNAME}")
            return
        bot_user_id = bot_user_info.data.id
        logger.info(f"Bot User ID for @{TWITTER_BOT_USERNAME} is {bot_user_id}")

        stream_listener = MentionStreamListener(
            bearer_token=TWITTER_BEARER_TOKEN,
            callback_on_mention=callback_on_mention,
            bot_user_id=bot_user_id
        )

        # Clear existing rules (optional, good for ensuring a clean state)
        existing_rules = stream_listener.get_rules()
        if existing_rules.data:
            rule_ids = [rule.id for rule in existing_rules.data]
            logger.info(f"Deleting existing stream rules: {rule_ids}")
            stream_listener.delete_rules(rule_ids)

        # Add a rule to listen for mentions of the bot
        # The rule format `@username` targets mentions of that user.
        rule_value = f"@{TWITTER_BOT_USERNAME}"
        stream_listener.add_rules(tweepy.StreamRule(value=rule_value, tag="mentions-rule"))
        logger.info(f"Added stream rule: '{rule_value}'")

        logger.info(f"Starting to listen for mentions to @{TWITTER_BOT_USERNAME}...")
        # Important: specify tweet_fields to get author_id and other necessary fields
        stream_listener.filter(tweet_fields=["author_id", "created_at", "conversation_id", "in_reply_to_user_id"])

    except tweepy.TweepyException as e:
        logger.error(f"Tweepy error while trying to listen for mentions: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in listen_for_mentions: {e}")

def post_reply(tweet_id, text, media_id=None):
    """
    Reply to a tweet. media_id is for attaching uploaded videos.
    Uses Twitter API v2.
    """
    global api_v2
    if not api_v2:
        logger.error("Twitter API v2 client not initialized. Call init_client() first.")
        return None

    try:
        logger.info(f"Attempting to reply to tweet_id: {tweet_id} with text: '{text}' and media_id: {media_id}")
        response = api_v2.create_tweet(
            text=text,
            in_reply_to_tweet_id=tweet_id,
            media_ids=[media_id] if media_id else None
        )
        if response.data and response.data.get('id'):
            logger.info(f"Successfully posted reply. New tweet ID: {response.data['id']}")
            return response.data['id']
        else:
            logger.error(f"Failed to post reply. Response: {response.errors}")
            return None
    except tweepy.TweepyException as e:
        logger.error(f"Tweepy error while posting reply to {tweet_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while posting reply to {tweet_id}: {e}")
        return None

def upload_video(video_filepath):
    """
    Upload video to Twitter. Handles chunked uploads for supported formats (like MP4).
    Returns media_id string.
    Uses Twitter API v1.1.
    """
    global api_v1
    if not api_v1:
        logger.error("Twitter API v1.1 client not initialized. Call init_client() first.")
        return None

    if not os.path.exists(video_filepath):
        logger.error(f"Video file not found: {video_filepath}")
        return None

    try:
        logger.info(f"Starting video upload for: {video_filepath}")
        # media_upload handles chunking for MP4s and other supported types
        # For large files, this can take some time.
        # media_category must be 'tweet_video' for videos to be attachable to tweets.
        # Max video size is 512MB, max length 140 seconds.
        media = api_v1.media_upload(filename=video_filepath, media_category='tweet_video', chunked=True)
        
        # Check processing status (optional, but good practice for large videos)
        # This part might need more robust handling in a production system
        if media.processing_info and media.processing_info['state'] != 'succeeded':
            logger.info(f"Video uploaded (ID: {media.media_id_string}), but processing is not yet complete. State: {media.processing_info['state']}")
            
            if media.processing_info['state'] == 'pending' or media.processing_info['state'] == 'in_progress':
                logger.info(f"Waiting for video processing (ID: {media.media_id_string})... Check every {media.processing_info.get('check_after_secs', 10)}s")
                time.sleep(media.processing_info.get('check_after_secs', 10)) # Wait suggested time
                
                # Re-check status (simplified loop for example)
                # In a real app, you'd loop this until 'succeeded' or 'failed' with a timeout.
                status = api_v1.get_media_upload_status(media.media_id_string)
                logger.info(f"Video processing status for {media.media_id_string}: {status.processing_info['state']}")
                if status.processing_info['state'] != 'succeeded':
                    logger.warning(f"Video {media.media_id_string} processing did not complete in time or failed. State: {status.processing_info['state']}")
                    # Depending on policy, you might return None or the media_id anyway
                    # if you want to try attaching it. For this example, let's be strict.
                    if status.processing_info['state'] == 'failed':
                         logger.error(f"Video processing failed: {status.processing_info.get('error')}")
                         return None
                    # If still pending/in_progress after one check, for this example we log and continue
                    # but a production app would loop with retries and timeout.

        if media.media_id_string:
            logger.info(f"Video uploaded successfully. Media ID: {media.media_id_string}")
            return media.media_id_string
        else:
            logger.error(f"Video upload failed for {video_filepath}. No media_id returned.")
            return None
            
    except tweepy.TweepyException as e:
        logger.error(f"Tweepy error during video upload for {video_filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during video upload for {video_filepath}: {e}")
        return None

def get_tweet_text(tweet_id):
    """
    Fetch the text of a specific tweet using Twitter API v2.
    """
    global api_v2
    if not api_v2:
        logger.error("Twitter API v2 client not initialized. Call init_client() first.")
        return None
    try:
        logger.info(f"Fetching tweet text for tweet_id: {tweet_id}")
        # You can request more fields using tweet_fields parameter
        response = api_v2.get_tweet(tweet_id) # tweet_fields=['text', 'created_at']
        if response.data:
            logger.info(f"Successfully fetched tweet text for {tweet_id}: '{response.data.text}'")
            return response.data.text
        else:
            logger.error(f"Could not find tweet or failed to fetch tweet {tweet_id}. Errors: {response.errors}")
            return None
    except tweepy.TweepyException as e:
        logger.error(f"Tweepy error fetching tweet {tweet_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching tweet {tweet_id}: {e}")
        return None

if __name__ == '__main__':
    # Example usage (optional, for testing)
    
    # Define a dummy callback for testing
    def handle_mention(tweet_data):
        logger.info(f"--- Mention Callback Triggered ---")
        logger.info(f"Tweet ID: {tweet_data.id}")
        logger.info(f"Text: {tweet_data.text}")
        logger.info(f"Author ID: {tweet_data.author_id}")
        logger.info(f"Conversation ID: {tweet_data.conversation_id}")
        # In a real bot, you might call post_reply here
        # For example:
        # if api_v1 and api_v2: # Ensure clients are available
        # post_reply(tweet_data.id, "Thanks for the mention!", media_id=None)
        # else:
        # logger.error("API clients not available for replying.")

    # Initialize clients
    init_client() # This will set global api_v1 and api_v2

    # Test listening for mentions (this will run indefinitely)
    if api_v1 and api_v2 and TWITTER_BEARER_TOKEN and TWITTER_BOT_USERNAME:
         logger.info(f"Attempting to listen for mentions to @{TWITTER_BOT_USERNAME}. Ensure this user exists and tokens are correct.")
         listen_for_mentions(handle_mention)
    else:
         logger.error("Could not start mention listener. Check credentials and .env settings (TWITTER_BOT_USERNAME, TWITTER_BEARER_TOKEN).")