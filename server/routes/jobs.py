from flask import Blueprint, request, jsonify, send_file, current_app
from services.job_service import create_job, get_job_info
import os

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/api/jobs', methods=['POST'])
def create_job_route():
    """Create a new video explanation job"""
    data = request.get_json()
    
    # Validate request data
    if not data or 'query' not in data or 'persona' not in data:
        return jsonify({'error': 'Missing required fields: query and persona'}), 400
    
    # Extract parameters
    persona_id = data['persona']
    query = data['query']
    
    # Create job and get job ID
    job_id = create_job(persona_id, query)
    
    # Return the job ID
    return jsonify({
        'job_id': job_id,
        'status': 'created'
    }), 201

@jobs_bp.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status_route(job_id):
    """Get status and updates for a specific job"""
    job_data = get_job_info(job_id)
    
    if not job_data:
        return jsonify({'error': 'Job not found'}), 404
    
    video_available = False
    video_url = None
    
    # Check if final video exists
    # Assuming 'final_video.mp4' is the standard name.
    # Adjust if your naming convention is different or stored in job_data
    final_video_path = os.path.join(current_app.root_path, 'data', 'results', job_id, 'final_video.mp4')

    if os.path.exists(final_video_path) and job_data['job_details']['status'] == 'completed':
        video_available = True
        video_url = f'/api/jobs/{job_id}/video' # Use the existing video serving route

    # Restructure the response to match what the client expects
    response = {
        'job': {
            **job_data['job_details'],
            'video_available': video_available,
            'video_url': video_url
        },
        'updates': job_data['status_updates']
    }
    
    return jsonify(response)

@jobs_bp.route('/api/jobs/<job_id>/video', methods=['GET'])
def get_video_route(job_id):
    """Stream the final generated video file"""
    job_data = get_job_info(job_id)
    
    if not job_data:
        return jsonify({'error': 'Job not found'}), 404
        
    if job_data['job_details']['status'] != 'completed':
        return jsonify({'error': 'Video not ready yet'}), 400
    
    # Path to final video file
    video_path = os.path.join(current_app.root_path, 'data', 'results', job_id, 'final_video.mp4')
    
    if not os.path.exists(video_path):
        return jsonify({'error': 'Video file not found'}), 404
    
    return send_file(video_path, mimetype='video/mp4')
