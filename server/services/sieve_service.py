import os
import json
import sieve

def create_celebrity_video(persona_id, audio_file, output_dir):
    """Create a video of the celebrity lip-syncing to the audio"""
    try:
        # Get the persona data
        with open(os.path.join('server', 'data', 'personas.json'), 'r') as f:
            personas = json.load(f)
        persona = next((p for p in personas["personas"] if p["id"] == persona_id), None)
        
        # Get the base video path
        base_video_path = persona["video_path"]
        if not base_video_path or not os.path.exists(base_video_path):
            print(f"Warning: Base video not found for persona {persona_id}, using placeholder")
            return os.path.join('server', 'data', 'placeholder_celebrity.mp4')
        
        # Output video path - use fixed filename
        output_video = os.path.join(output_dir, "lip_synced_video.mp4")
        
        # Create Sieve file objects
        video_file = sieve.File(path=base_video_path)
        audio_file_obj = sieve.File(path=audio_file)
        
        # Get the lipsync function
        lipsync = sieve.function.get("sieve/lipsync")
        
        # Call the lipsync function
        job = lipsync.push(
            file=video_file,
            audio=audio_file_obj,
            backend="sievesync-1.1",
            enable_multispeaker=False,
            enhance="default",
            downsample=False,
            cut_by="audio"
        )
        
        # Wait for the result
        print("Waiting for lipsync job to complete...")
        result = job.result()
        
        # Save the result to the output path
        return result
    
    except Exception as e:
        print(f"Error creating celebrity video: {e}")
        # Return a placeholder in case of error
        return os.path.join('server', 'data', 'placeholder_celebrity.mp4')

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
            word_level_timestamps=False,
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
