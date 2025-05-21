import os
import json
import requests
from dotenv import load_dotenv

from .sieve_service import transcribe_audio_file

# Load environment variables
load_dotenv()

APP_DATA_BASE_DIR = os.environ.get('APP_DATA_BASE_DIR', 'data')

# Get credentials
user_id = os.getenv("PLAYHT_TTS_USER")
api_key = os.getenv("PLAYHT_TTS_API_KEY")
sieve_api_key = os.getenv("SIEVE_API_KEY")

def generate_speech(job_id, persona_id, script, results_dir):
    """Generate speech audio from the script in the celebrity's voice and transcribe it"""
    
    # Output file path
    output_file = os.path.join(results_dir, "speech.mp3")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Get the persona data
    with open(os.path.join(APP_DATA_BASE_DIR, 'personas.json'), 'r') as f:
        personas = json.load(f)
    
    persona = next((p for p in personas["personas"] if p["id"] == persona_id), None)
    voice_link = persona["tts_voice_link"]

    # Create the speech file
    speech_file = create_speech_file(output_file, script, voice_link)
    
    # Transcribe the speech
    transcription = transcribe_audio_file(speech_file)
    
    return speech_file, transcription

def create_speech_file(output_file, script, voice_link):
    """Helper function to generate speech from text using Play.ht API"""
    # API endpoint
    url = "https://api.play.ht/api/v2/tts/stream"
    
    # Headers - according to Play.ht API docs
    headers = {
        "X-USER-ID": user_id,
        "Authorization": api_key,
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