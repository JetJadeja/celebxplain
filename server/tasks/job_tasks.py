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
        # Define the job output directory
        results_dir = os.path.join('server', 'data', 'results', job_id)
        os.makedirs(results_dir, exist_ok=True)

        # Step 1: Generate explanation content
        explanation = generate_explanation(persona_id, query)
        update_job_status(job_id, "processing", "Generated explanation content")
        
        # Step 2: Text-to-speech conversion
        speech_file, transcription = generate_speech(job_id, persona_id, explanation, results_dir)
        update_job_status(job_id, "processing", "Generated speech")

        # Steps 3 & 4: Parallel processing for efficiency
        update_job_status(job_id, "processing", "Generating visuals content")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Launch both tasks simultaneously
            # celeb_task = executor.submit(
            #     create_celebrity_video,
            #     persona_id,
            #     speech_file,
            #     results_dir
            # )
            
            visuals_task = executor.submit(
                create_explanatory_visuals,
                transcription
            )
            
            # Wait for both to complete
            # celeb_video = celeb_task.result()
            visual_elements = visuals_task.result()
            update_job_status(job_id, "processing", "Generated visuals")
        
        # Step 5: Final video production
        update_job_status(job_id, "processing", "Assembling final video")
        output_path = assemble_final_video(celeb_video, visual_elements, results_dir)
        
        # Set result access path
        result_path = f"/api/jobs/{job_id}/video"
        update_job_status(job_id, "completed", "Video generated successfully")
        return {
            "speech_file": speech_file,
            "transcription": transcription,
            "celeb_video": celeb_video,
            "visuals": visual_elements,
            "final_video": output_path,
            "result_url": result_path
        }
        
    except Exception as e:
        # Handle any failures
        update_job_status(job_id, "error", f"Processing error: {str(e)}", error=str(e))
        raise 