# CelebXplain

Generate videos of celebrities explaining any concept using AI. This project combines a Next.js frontend with a Python (Flask) backend, utilizing Celery for background task processing (video generation) and Redis as the message broker and result backend. AI services like OpenAI (for script generation) and PlayHT (for text-to-speech) are integrated to create the final video, potentially using Manim for animations.

## Project Overview

- **Frontend (`client/`):** A Next.js application providing the user interface to input a concept and select a celebrity. It communicates with the backend API.

- **Backend (`server/`):** A Flask application that handles API requests from the frontend. It orchestrates the video generation process by dispatching tasks to Celery workers.

- **API (`server/app.py`, `server/routes/`):** Defines the endpoints for frontend communication.

- **Celery (`server/celery_app.py`, `server/tasks/`):** Manages asynchronous tasks like generating scripts, synthesizing speech, and rendering videos.

- **Services (`server/services/`):** Contains logic for interacting with external AI APIs (OpenAI, PlayHT) and video generation tools (Manim).

## Prerequisites

- **Node.js and Yarn:** For the frontend. (Install from [https://nodejs.org/](https://nodejs.org/) and `npm install -g yarn`)

- **Python:** (Version 3.8+ recommended). Manage environments using `venv` or `conda`.

- **Redis:** For Celery message broker and result backend. (Install via package manager like `brew install redis` on macOS or follow instructions on [https://redis.io/](https://redis.io/))

- **API Keys:**

- OpenAI API Key

- PlayHT User ID and API Key

- (Potentially others depending on specific services used in `server/services/`)

## Setup

### 1. **Clone the repository:**

```bash
git clone https://github.com/jetjadeja/celebxplain.git
cd celebxplain
```

### 2. **Setup Backend (`server/`):**

a. **Navigate to server directory:**

```bash
cd server
```

b. **Create and activate Python virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### c. **Install Python dependencies:**

```bash
pip install -r ../requirements.txt
```

### d. **Configure Environment Variables:**

Create a `.env` file in the `server/` directory (you can copy `.env.example` if it exists or create it manually) and add your API keys:

```dotenv
OPENAI_API_KEY=your_openai_api_key
PLAYHT_TTS_USER=your_playht_user_id
PLAYHT_TTS_API_KEY=your_playht_api_key
# Add any other required keys based on services used
```

## 3. **Setup Frontend (`client/`):**

### a. **Navigate to client directory:**

```bash
cd ../client
```

### b. **Install Node.js dependencies:**

```bash
yarn install
```

### c. **(Optional) Configure Environment Variables:**

If the frontend needs to know the backend URL or requires other environment variables, create a `.env.local` file in the `client/` directory and add them (e.g., `NEXT_PUBLIC_API_URL=http://localhost:5000/api`).

## Running the Application

You need to run Redis, the backend server, the Celery worker, and the frontend development server, typically in separate terminals.

### 1. **Start Redis:**

_(Ensure Redis server is installed)_

```bash

redis-server

# Or start it as a service depending on your OS and installation method

```

### 2. **Start the Celery Worker:**

- Open a new terminal in the project root.

- Navigate to the `server` directory and activate the Python environment:

```bash

cd server

source venv/bin/activate

```

- Start the Celery worker:

```bash

celery -A celery_app.celery_app worker --loglevel=info

```

### 3. **Start the Backend Server (Flask):**

- Open a new terminal in the project root.

- Navigate to the `server` directory and activate the Python environment:

```bash

cd server

source venv/bin/activate

```

- Start the Flask app:

```bash

flask run

# By default, it runs on http://127.0.0.1:5000

```

### 4. **Start the Frontend Server (Next.js):**

- Open a new terminal in the project root.

- Navigate to the `client` directory:

```bash

cd client

```

- Start the Next.js development server:

```bash

yarn dev

```

- Open your browser to the address provided (`http://localhost:3000`).

Now you should be able to access the CelebXplain application in your browser and generate videos!
