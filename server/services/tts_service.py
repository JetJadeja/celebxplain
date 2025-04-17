import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print(os.getenv("PLAYHT_TTS_USER"))
print(os.getenv("PLAYHT_TTS_API_KEY"))

def generate_speech(job_id, persona_id, script):
    """Generate speech audio from the script in the celebrity's voice"""
    
    # Output file path
    output_file = os.path.join('server', 'data', 'generated', job_id, "speech.mp3")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Get the persona data
    with open(os.path.join('server', 'data', 'personas.json'), 'r') as f:
        personas = json.load(f)
    
    persona = next((p for p in personas["personas"] if p["id"] == persona_id), None)
    voice_link = persona["tts_voice_link"]
    
    # API endpoint
    url = "https://api.play.ht/api/v2/tts/stream"
    
    # Get credentials
    user_id = os.getenv("PLAYHT_TTS_USER")
    api_key = os.getenv("PLAYHT_TTS_API_KEY")
    
    # Debug info
    print(f"Using credentials - USER ID: {user_id[:5] if user_id else 'None'}... API KEY: {api_key[:5] if api_key else 'None'}...")
    
    # Headers - according to Play.ht API docs
    # Note: The AUTHORIZATION header might need "Bearer " prefix depending on the API
    headers = {
        "X-USER-ID": user_id,
        "Authorization": api_key,  # Changed from AUTHORIZATION to Authorization
        "accept": "audio/mpeg",
        "content-type": "application/json"
    }
    
    # Alternative headers format to try if the above doesn't work
    alt_headers = {
        "X-USER-ID": user_id,
        "Authorization": f"Bearer {api_key}",  # Try with Bearer prefix
        "accept": "audio/mpeg",
        "content-type": "application/json"
    }
    
    # Payload
    payload = {
        "text": script,
        "voice_engine": "PlayDialog",
        "voice": voice_link,
        "output_format": "mp3"
    }
    
    try:
        # Make the request with standard headers
        print("Making request to Play.ht API...")
        print(f"Request URL: {url}")
        print(f"Request payload: {payload}")
        print(f"Headers (redacted): {headers.keys()}")
        
        response = requests.post(url, headers=headers, json=payload, stream=True)
        
        # If failed, try alternative headers
        if response.status_code == 403:
            print("First attempt failed with 403, trying alternative header format...")
            response = requests.post(url, headers=alt_headers, json=payload, stream=True)
        
        # Raise exception for HTTP errors
        response.raise_for_status()
        
        # Write response to file
        with open(output_file, "wb") as audio_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    audio_file.write(chunk)
        
        print(f"Speech generated and saved to {output_file}")
        return output_file
    except Exception as e:
        print(f"Error generating speech: {e}")
        if hasattr(e, 'response'):
            if hasattr(e.response, 'text'):
                print(f"API response text: {e.response.text}")
            print(f"Status code: {e.response.status_code}")
            print(f"Response headers: {e.response.headers}")
        raise