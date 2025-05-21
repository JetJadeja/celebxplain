import os
import json
from openai import OpenAI
from pydantic import BaseModel
import dotenv
import logging
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables (e.g., OPENAI_API_KEY)
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize OpenAI client
# The API key will be read from the OPENAI_API_KEY environment variable
try:
    client = OpenAI()
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}. Make sure OPENAI_API_KEY is set.")
    client = None

class TweetExtract(BaseModel):
    """
    Pydantic model for structured LLM output.
    The LLM should extract the main topic and the celebrity mentioned.
    """
    topic: Optional[str]
    celebrity_mention: Optional[str]

def parse_tweet(tweet_text: str, personas_data: dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse tweet text to extract a topic and a mentioned celebrity.

    Args:
        tweet_text: The full text of the tweet.
        personas_data: Loaded personas data (from personas.json).

    Returns:
        A tuple (topic, persona_id, error_message).
        - topic: The extracted topic.
        - persona_id: The ID of the matched persona.
        - error_message: A string containing an error message if parsing fails
                         or celebrity is not found, otherwise None.
    """
    if not client:
        return None, None, "OpenAI client not initialized. Check API key."

    if not tweet_text:
        return None, None, "Tweet text is empty."

    if not personas_data or "personas" not in personas_data:
        return None, None, "Personas data is invalid or missing."

    try:
        logger.info(f"Parsing tweet: \"{tweet_text}\"")
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": """You are an expert tweet analyst.
Your task is to identify two key pieces of information from a user's tweet:
1. The main **topic** or question the user wants explained.
2. The full **celebrity_mention** of a person the user wants to explain the topic.

If the user doesn't explicitly mention a celebrity to do the explaining, or if the celebrity is not clearly identifiable, return null for `celebrity_mention`.
The topic should be a concise summary of what needs to be explained.
The celebrity name should be the full name as accurately as possible based on the tweet.
Do not infer a celebrity if not mentioned.
"""},
                {"role": "user", "content": f"Here's the tweet: \"{tweet_text}\""},
            ],
            response_format=TweetExtract,
        )

        if not completion.choices or not completion.choices[0].message.parsed:
            logger.error("LLM parsing failed to return expected structure.")
            return None, None, "Error: Could not parse tweet structure from LLM."

        extracted_data: TweetExtract = completion.choices[0].message.parsed
        topic = extracted_data.topic
        celebrity_mention = extracted_data.celebrity_mention

        logger.info(f"LLM extracted: Topic='{topic}', Celebrity='{celebrity_mention}'")

        if not topic:
            return None, None, "Error: Could not determine the topic from the tweet."

        if not celebrity_mention:
            # If LLM explicitly returns no celebrity, it's not an error in parsing itself,
            # but the request can't be fulfilled without a celebrity.
            # The calling function can decide how to handle this (e.g., prompt user for celebrity).
            return topic, None, "No celebrity mentioned or identified in the tweet."

        # Match celebrity_mention against persona['name'] (case-insensitive)
        matched_persona_id = None
        for persona in personas_data.get("personas", []):
            if celebrity_mention.strip().lower() == persona.get("name", "").strip().lower():
                matched_persona_id = persona.get("id")
                logger.info(f"Matched celebrity '{celebrity_mention}' to persona ID: '{matched_persona_id}' (Name: {persona.get('name')})")
                break
        
        if not matched_persona_id:
            logger.warning(f"Celebrity '{celebrity_mention}' not found in personas data.")
            return topic, None, f"Error: Celebrity '{celebrity_mention}' is not a recognized persona."

        return topic, matched_persona_id, None

    except Exception as e:
        logger.error(f"Error during tweet parsing or LLM call: {e}")
        return None, None, f"An unexpected error occurred: {str(e)}"

if __name__ == '__main__':
    # Example Usage (requires a personas.json file and OPENAI_API_KEY)
    
    # Load actual personas_data for testing
    current_dir = os.path.dirname(__file__)
    personas_path = os.path.join(current_dir, "..", "data", "personas.json")
    actual_personas_data = {"personas": []} # Default to empty if loading fails

    if os.path.exists(personas_path):
        try:
            with open(personas_path, "r") as f:
                actual_personas_data = json.load(f)
            logger.info(f"Successfully loaded personas.json from {personas_path}")
        except Exception as e:
            logger.error(f"Error loading {personas_path}: {e}. Using empty personas data.")
    else:
        logger.warning(f"personas.json not found at {personas_path}. Using empty personas data. Tests may not run as expected.")

    test_tweets = [
        "Explain black holes like I'm five, by Elon Musk.",
        "Tell me about quantum physics, but make it Steve Jobs.",
        "Kanye West, what's the deal with general relativity?",
        "who is donald trump? explain the theory of evolution", # Celebrity and topic order swapped
        "Why is the sky blue?", # No celebrity
        "Explain the meaning of life by The Rock.", # Celebrity not in our dummy list (probably)
        "What are large language models? by kanye" # Case variation for celebrity
    ]

    if not client:
        logger.error("OpenAI client is not initialized. Cannot run tests. Ensure OPENAI_API_KEY is set in .env.")
    elif not actual_personas_data.get("personas"):
        logger.error("Personas data is empty or invalid. Cannot run tests effectively.")
    else:
        logger.info("\n--- Running parse_tweet tests ---")
        for tweet in test_tweets:
            topic, persona_id, error = parse_tweet(tweet, actual_personas_data)
            print(f"\nTweet: \"{tweet}\"")
            if error:
                print(f"  Error: {error}")
                if topic:
                    print(f"  Topic (still extracted): {topic}")
            else:
                print(f"  Topic: {topic}")
                print(f"  Persona ID: {persona_id}")
        logger.info("\n--- Tests finished ---") 