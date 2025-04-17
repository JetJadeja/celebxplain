from flask import Blueprint, request, jsonify
from server.services.job_service import create_job

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/api/jobs', methods=['POST'])
def create_job_route():
    data = request.get_json()
    
    # Validate request data
    if not data or 'query' not in data or 'persona' not in data:
        return jsonify({'error': 'Missing required fields: query and persona'}), 400
    
    # Get the query and persona from the request
    # query = data['query']
    # persona = data['persona']
    
    # Create job and get job ID
    job_id = create_job()
    
    # Return the job ID
    return jsonify({'job_id': job_id}), 201

@jobs_bp.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    # For now, just return an empty list
    return jsonify([]), 200
