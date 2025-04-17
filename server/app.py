from flask import Flask, jsonify, request
from flask_cors import CORS
from server.routes.jobs import jobs_bp

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Register blueprints
app.register_blueprint(jobs_bp)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Flask API"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
