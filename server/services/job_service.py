import uuid
import threading
import os
import concurrent.futures

from utils.db import create_job as db_create_job, update_job_status, get_job, get_job_updates
from services.llm_service import generate_explanation
from services.tts_service import generate_speech
from services.sieve_service import create_celebrity_video, create_explanatory_visuals
from services.video_service import assemble_final_video

# Track ongoing job processes
running_jobs = {}

def create_job(celeb_id, query):
    """Create a new job and start processing in background thread"""
    # Generate unique job identifier
    job_id = str(uuid.uuid4())
    
    # Record in database
    db_create_job(job_id, celeb_id, query)
    
    # Launch background processing
    job_thread = threading.Thread(
        target=_process_job,
        args=(job_id, celeb_id, query)
    )
    job_thread.daemon = True
    job_thread.start()
    
    # Store thread reference
    running_jobs[job_id] = job_thread
    
    return job_id

def get_job_info(job_id):
    """Retrieve current job status and all updates"""
    job_data = get_job(job_id)
    
    if not job_data:
        return None
    
    # Collect all status updates
    updates = get_job_updates(job_id)
    
    return {
        "job_details": job_data,
        "status_updates": updates
    }

def _process_job(job_id, celeb_id, query):
    """Execute all processing steps for celebrity explanation video"""
    try:
        # Step 1: Generate explanation content
        update_job_status(job_id, "generating_explanation", "Creating explanation script...")
        explanation = generate_explanation(celeb_id, query)
        update_job_status(job_id, "explanation_ready", "Explanation script completed")
        
        # Step 2: Text-to-speech conversion
        update_job_status(job_id, "creating_audio", "Converting to speech...")
        speech_file, word_timings = generate_speech(celeb_id, explanation)
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
                celeb_id,
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
        
    except Exception as e:
        # Handle any failures
        update_job_status(job_id, "error", f"Processing error: {str(e)}", error=str(e))
