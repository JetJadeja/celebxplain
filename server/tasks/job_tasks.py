"""
Celery tasks for handling job processing
"""
import os
import concurrent.futures
from celery import shared_task

from utils.db import update_job_status
from services.llm_service import generate_explanation
from services.tts_service import generate_speech
from services.sieve_service import create_celebrity_video, create_explanatory_visuals
from services.video_service import assemble_final_video

@shared_task
def process_job(job_id, persona_id, query):
    """
    Process a video explanation job
    
    Args:
        job_id (str): The unique identifier for the job
        persona_id (str): The persona/celebrity identifier
        query (str): The explanation query/topic
    """
    try:
        # Step 1: Generate explanation content
        update_job_status(job_id, "generating_explanation", "Creating explanation script...")
        explanation = generate_explanation(persona_id, query)
        update_job_status(job_id, "explanation_ready", "Explanation script completed")
        
        # Step 2: Text-to-speech conversion
        update_job_status(job_id, "creating_audio", "Converting to speech...")
        speech_file, word_timings = generate_speech(persona_id, explanation)
        update_job_status(job_id, "audio_ready", "Voice generation complete")
        
        # Create job output directory
        results_dir = os.path.join('server', 'data', 'results', job_id)
        os.makedirs(results_dir, exist_ok=True)
        
        # Steps 3 & 4: Parallel processing for efficiency
        update_job_status(job_id, "creating_media", "Generating video and visuals...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Launch both tasks simultaneously
            celeb_task = executor.submit(
                create_celebrity_video,
                persona_id,
                speech_file
            )
            
            visuals_task = executor.submit(
                create_explanatory_visuals,
                query,
                word_timings
            )
            
            # Wait for both to complete
            celeb_video = celeb_task.result()
            update_job_status(job_id, "celeb_video_ready", "Celebrity video created")
            
            visual_elements = visuals_task.result()
            update_job_status(job_id, "visuals_ready", "Supporting visuals created")
        
        # Step 5: Final video production
        update_job_status(job_id, "compositing", "Creating final video...")
        output_path = assemble_final_video(celeb_video, visual_elements, results_dir)
        
        # Set result access path
        result_path = f"/api/jobs/{job_id}/video"
        
        # Mark job complete
        update_job_status(
            job_id, 
            "completed", 
            "Celebrity explanation video ready!",
            result_url=result_path
        )
        
        return output_path
        
    except Exception as e:
        # Handle any failures
        update_job_status(job_id, "error", f"Processing error: {str(e)}", error=str(e))
        raise 