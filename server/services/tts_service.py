import os
import json
import requests
import sieve
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
user_id = os.getenv("PLAYHT_TTS_USER")
api_key = os.getenv("PLAYHT_TTS_API_KEY")
sieve_api_key = os.getenv("SIEVE_API_KEY")

def generate_speech(job_id, persona_id, script):
    """Generate speech audio from the script in the celebrity's voice and transcribe it"""
    
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

def transcribe_audio_file(audio_file_path):
    """Helper function to transcribe audio using Sieve API"""
    try:
        # Create Sieve file object from local file
        audio_file = sieve.File(path=audio_file_path)
        
        # Get the transcription function
        transcriber = sieve.function.get("sieve/transcribe")
        
        # Call the transcription function
        print(f"Transcribing audio file: {audio_file_path}")
        job = transcriber.push(
            file=audio_file,
            backend="stable-ts-whisper-large-v3-turbo",
            word_level_timestamps=True,
            source_language="auto"
        )
        
        # Wait for the result
        result = job.result()
        
        # Convert generator to a serializable structure
        serialized_result = {}
        try:
            # Try to convert to a dictionary
            if hasattr(result, '__iter__') and not isinstance(result, dict):
                serialized_result = list(result)
            else:
                # If it's already a dictionary or similar, just use it
                serialized_result = result
            
            # Save transcription to a JSON file for debugging
            transcription_file = os.path.splitext(audio_file_path)[0] + "_transcription.json"
            with open(transcription_file, 'w') as f:
                json.dump(serialized_result, f, indent=2)
            
            print("Transcription completed successfully")
            return serialized_result
        
        except TypeError as e:
            # If conversion fails, return a simplified version
            print(f"Warning: Could not fully serialize transcription result: {e}")
            return {"error": "Transcription completed but result could not be fully serialized",
                    "message": str(e)}
    
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        # Return error as serializable dict
        return {"error": "Transcription failed", "message": str(e)}