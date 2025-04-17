import os
import time
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
        
        # Create output directory - use same structure as TTS service
        output_dir = os.path.dirname(audio_file)
        
        # Output video path - use fixed filename
        output_video = os.path.join(output_dir, "lip_synced_video.mp4")
        
        print(f"Creating lip-sync video for {persona['name']} using audio: {audio_file}")
        print(f"Base video: {base_video_path}")
        print(f"Output will be saved to: {output_video}")
        
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

def create_explanatory_visuals(transcription):
    """Create explanatory visuals based on transcription data"""
    try:
        print("Creating explanatory visuals from transcription...")
        
        # Create output directory for visuals
        output_dir = os.path.join('server', 'data', 'visuals')
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract word timings from transcription
        word_timings = []
        if transcription and not isinstance(transcription, dict) or not transcription.get('error'):
            # Extract word timing information based on the structure of transcription data
            if isinstance(transcription, list) and len(transcription) > 0 and 'words' in transcription[0]:
                word_timings = transcription[0]['words']
                print(f"Extracted {len(word_timings)} word timings from transcription")
        
        # TODO: Implement actual visuals generation using Sieve or other services
        # For now, return placeholder visuals
        
        # Generate placeholder visuals based on word timings
        visual_elements = []
        
        # Create some placeholder visuals - in real implementation, these would be generated based on content
        visual_elements = [
            {
                "type": "image",
                "path": os.path.join(output_dir, 'visual_1.png'),
                "start_time": 1.0,
                "end_time": 3.0
            },
            {
                "type": "image",
                "path": os.path.join(output_dir, 'visual_2.png'),
                "start_time": 3.5,
                "end_time": 6.0
            }
        ]
        
        # Simulate processing time
        time.sleep(1)
        
        print(f"Created {len(visual_elements)} visual elements")
        return visual_elements
        
    except Exception as e:
        print(f"Error creating explanatory visuals: {e}")
        # Return minimal placeholder visuals in case of error
        return [
            {
                "type": "image",
                "path": os.path.join('server', 'data', 'placeholder_visual_1.png'),
                "start_time": 1.0,
                "end_time": 3.0
            }
        ]

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
