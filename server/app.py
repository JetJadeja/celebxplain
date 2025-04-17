from flask import Flask, jsonify, request
from flask_cors import CORS
from routes import jobs_bp, personas_bp
from utils import init_db
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # Enable CORS for all routes

# Register blueprints
app.register_blueprint(jobs_bp)
app.register_blueprint(personas_bp)

# Initialize database on startup
init_db()

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Flask API"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
