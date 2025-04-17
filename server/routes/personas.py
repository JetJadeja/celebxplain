from flask import Blueprint, jsonify
import json
import os

personas_bp = Blueprint('personas', __name__)

@personas_bp.route('/api/personas', methods=['GET'])
def get_personas():
    # Define the path to the personas.json file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    personas_file = os.path.join(current_dir, '..', 'data', 'personas.json')
    
    # Read personas from the JSON file
    with open(personas_file, 'r') as f:
        personas_data = json.load(f)
    
    # Filter personas to only include id, name, and icon_url
    filtered_personas = []
    for persona in personas_data['personas']:
        filtered_personas.append({
            'id': persona['id'],
            'name': persona['name'],
            'icon_url': persona['icon_url']
        })
    
    return jsonify(filtered_personas), 200
