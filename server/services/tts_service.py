import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
user_id = os.getenv("PLAYHT_TTS_USER")
api_key = os.getenv("PLAYHT_TTS_API_KEY")

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

    # Create the speech file
    create_speech_file(output_file, script, voice_link)

def create_speech_file(output_file, script, voice_link):
    # API endpoint
    url = "https://api.play.ht/api/v2/tts/stream"
    
    # Headers - according to Play.ht API docs
    # Note: The AUTHORIZATION header might need "Bearer " prefix depending on the API
    headers = {
        "X-USER-ID": user_id,
        "Authorization": api_key,  # Changed from AUTHORIZATION to Authorization
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
        # Call the API        
        response = requests.post(url, headers=headers, json=payload, stream=True)
        
        # Raise exception for HTTP errors
        response.raise_for_status()
        
        # Write response to file
        with open(output_file, "wb") as audio_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    audio_file.write(chunk)
        
        return output_file
    
    except Exception as e:
        print(f"Error generating speech: {e}")
        if hasattr(e, 'response'):
            if hasattr(e.response, 'text'):
                print(f"API response text: {e.response.text}")
            print(f"Status code: {e.response.status_code}")
            print(f"Response headers: {e.response.headers}")
        raise