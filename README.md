# Oracle

Generate videos of celebrities explaining any concept using AI. This application takes a user-provided concept and a chosen celebrity, then leverages artificial intelligence to create a short video where the celebrity appears to explain that concept. The process involves generating a script, synthesizing the celebrity's voice, using Sieve for video processing, and potentially sharing it via a Twitter bot.

## Project Overview

- **Frontend (`client/`):** A Next.js application providing the user interface to input a concept and select a celebrity. It communicates with the backend API.

- **Backend (`server/`):** A Flask application that handles API requests from the frontend. It orchestrates the video generation process by dispatching tasks to Celery workers.

- **API (`server/app.py`, `server/routes/`):** Defines the endpoints for frontend communication.

- **Celery (`server/celery_app.py`, `server/tasks/`):** Manages asynchronous tasks like generating scripts, synthesizing speech, and rendering videos. The use of Celery allows for decoupling long-running tasks from the main application thread, improving responsiveness and scalability.

- **Redis:** Serves as the message broker and result backend for Celery. It facilitates communication between the Flask application and Celery workers, ensuring reliable task queuing and result storage.

- **Services (`server/services/`):** Contains logic for interacting with external AI APIs (OpenAI, PlayHT), video generation tools (Sieve), and social media platforms (Twitter).

- **Sieve (`server/services/sieve_service.py`):** A crucial component for video processing. Authentication is handled via the Sieve CLI.

- **Twitter Bot (`server/twitter_bot/`):** An optional component that can be configured to automatically tweet generated videos or related content. Its main script is `server/twitter_bot/main.py`.

## Features

- **Concept Explanation:** Users can input any concept they want a celebrity to explain.
- **Celebrity Selection:** A predefined list of celebrities is available for users to choose from.
- **AI-Powered Script Generation:** The system uses OpenAI's GPT models to generate a script for the celebrity.
- **Realistic Voice Synthesis:** PlayHT API is used to synthesize the celebrity's voice.
- **Video Generation:** Sieve is used to create a video of the celebrity speaking the generated script.
- **Asynchronous Task Processing:** Celery and Redis handle long-running tasks in the background, ensuring the application remains responsive.
- **(Optional) Twitter Integration:** Automatically share generated videos on Twitter using the `server/twitter_bot/main.py` script.

## Prerequisites

- **Node.js and Yarn:** For the frontend. (Install from [https://nodejs.org/](https://nodejs.org/) and `npm install -g yarn`)

- **Python:** (Version 3.8+ recommended). Manage environments using `venv` or `conda`.

- **Redis:** For Celery message broker and result backend. (Install via package manager like `brew install redis` on macOS or follow instructions on [https://redis.io/](https://redis.io/))

- **Sieve Account & CLI Authentication:**

  - Sign up for a Sieve account at [https://sieve.com/](https://sieve.com/) (or relevant Sieve website).
  - You will authenticate with Sieve using their CLI tool.

- **API Keys & Credentials:**

  - OpenAI API Key
  - PlayHT User ID and API Key
  - **(Optional) Twitter Developer Account & API Keys:** If you plan to use the Twitter bot, you'll need a Twitter Developer account and the associated API Key, API Secret Key, Access Token, and Access Token Secret. These are configured in `server/.env`.

- **`sievedata` Python package:** For Sieve CLI authentication.

## Setup

### 1. **Clone the repository:**

```bash
git clone https://github.com/jetjadeja/oracle.git
cd oracle
```

### 2. **Setup Backend (`server/`):**

a. **Create and activate Python virtual environment (Recommended):**
It's highly recommended to use a virtual environment for Python projects. From the project root:

```bash
python3 -m venv server/venv # Create venv inside server directory
source server/venv/bin/activate # On macOS/Linux
# server\venv\Scripts\activate # On Windows
```

Subsequently, ensure this virtual environment is activated in any terminal where you run backend Python scripts (Flask, Celery, Twitter Bot).

b. **Install Python dependencies:**
With the virtual environment activated, from the project root:

```bash
pip install -r requirements.txt
```

This file should include `sievedata` and all other backend dependencies.

c. **Authenticate with Sieve:**
This is a critical step for video processing. Ensure your virtual environment is active:

```bash
sieve login
```

Follow the on-screen prompts to enter your Sieve API key and complete the login process.

d. **Configure Environment Variables:**
Navigate to the `server/` directory and create a `.env` file (you can copy `server/.env.example` if it exists).

```bash
cd server
# Create or edit .env file here
```

Populate `server/.env` with your API keys and configurations as shown below:

```dotenv
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development # or production
SECRET_KEY=your_very_secret_key # Change this in production!
DEBUG=True # Set to False in production

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Redis Configuration (if different from Celery defaults)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# PlayHT API Credentials
PLAYHT_TTS_USER=your_playht_user_id
PLAYHT_TTS_API_KEY=your_playht_api_key

# Twitter Bot Credentials (Optional - fill these if you want to use the Twitter bot)
# Ensure these are correctly set if you intend to run the twitter_bot/main.py script
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET_KEY=your_twitter_api_secret_key
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token # May be needed for some Twitter API v2 endpoints

# Logging Configuration
LOG_LEVEL=INFO # e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=app.log # Path to the log file
```

Return to the project root directory after configuring: `cd ..`

**Important Sieve Note:** The application relies on you being logged in via the `sieve login` command. Sieve authentication is tied to your user environment and the active Python environment where `sievedata` is installed.

### 3. **Setup Frontend (`client/`):**

a. **Navigate to client directory:**
From the project root:

```bash
cd client
```

b. **Install Node.js dependencies:**

```bash
yarn install
```

c. **(Optional) Configure Environment Variables (Frontend):**
If the frontend needs to know the backend URL, create a `.env.local` file in the `client/` directory and add `NEXT_PUBLIC_API_URL=http://localhost:5000/api` (or your backend URL).

Return to the project root directory: `cd ..`

## Running the Application

To run the Oracle application, you will need to have at least four terminal windows/tabs open simultaneously (five if running the Twitter bot). Each terminal will run a separate component of the system.

**Crucial First Steps for Backend Terminals:**

1.  **Open a new terminal for each backend service** (Celery, Flask, Twitter Bot).
2.  **Navigate to the project root directory** in each of these terminals.
3.  **Activate the Python virtual environment** in each of these terminals:
    ```bash
    source server/venv/bin/activate # On macOS/Linux
    # server\venv\Scripts\activate # On Windows
    ```
4.  **Verify Sieve Login:** Ensure you have successfully run `sieve login` (as per Setup 2.c) in a terminal with the virtual environment activated. This authentication should persist.

---

**Terminal 1: Start Redis**

_(Ensure Redis server is installed. This command might run in the foreground or you might have it running as a background service depending on your OS.)_

```bash
redis-server
# Or start it as a service depending on your OS and installation method
```

If `redis-server` runs in the foreground, leave this terminal open.

---

**Terminal 2: Start the Celery Worker**

1.  Open a new terminal.
2.  Navigate to the project root: `cd path/to/your/project/oracle`
3.  Activate the Python virtual environment: `source server/venv/bin/activate`
4.  Navigate to the server directory: `cd server`
5.  Start the Celery worker:
    `bash
celery -A celery_app.celery_app worker --loglevel=info
`
    Leave this terminal open. It processes background tasks.

---

**Terminal 3: Start the Backend Server (Flask)**

1.  Open a new terminal.
2.  Navigate to the project root: `cd path/to/your/project/oracle`
3.  Activate the Python virtual environment: `source server/venv/bin/activate`
4.  Navigate to the server directory: `cd server`
5.  Start the Flask app:
    `bash
    flask run
    # By default, it runs on http://127.0.0.1:5000
    `
    Leave this terminal open. It serves the API.

---

**Terminal 4: Start the Frontend Development Server (Next.js)**

1.  Open a new terminal.
2.  Navigate to the project root: `cd path/to/your/project/oracle`
3.  Navigate to the client directory: `cd client`
4.  Start the Next.js development server:
    `bash
    yarn dev
    # By default, it runs on http://localhost:3000
    `
    Leave this terminal open. This is where you access the application in your browser.

---

**(Optional) Terminal 5: Start the Twitter Bot**

If you have configured the Twitter API credentials in `server/.env` and want to run the bot:

1.  Open a new terminal.
2.  Navigate to the project root: `cd path/to/your/project/oracle`
3.  Activate the Python virtual environment: `source server/venv/bin/activate`
4.  Navigate to the server directory: `cd server`
5.  Run the Twitter bot's main script:
    `bash
python twitter_bot/main.py
`
    Leave this terminal open if the bot is designed to run continuously.

---

## Configuration Deep Dive

### Environment Variables

The application relies heavily on environment variables for configuration. This approach is a best practice for several reasons:

- **Security:** Keeps sensitive information like API keys out of the codebase.
- **Flexibility:** Allows for different configurations across environments (development, staging, production) without code changes.
- **Portability:** Makes it easier to deploy the application in different environments.

All backend environment variables are managed in the `server/.env` file. Ensure this file is present and correctly populated before running the application. Refer to the example in the "Setup Backend" section for a comprehensive list of variables.

### Celery and Redis: The Why

- **Celery:** Used for distributed task queuing. Video generation involves multiple steps (scripting, voice synthesis, video rendering) that can be time-consuming. Celery allows these tasks to be executed asynchronously by separate worker processes. This means:
  - The main web application (Flask) remains responsive to user requests.
  - Tasks can be scaled independently by running more Celery workers.
  - If a task fails, Celery can retry it automatically.
- **Redis:** Acts as the message broker for Celery. When the Flask app wants to run a task, it sends a message to Redis. Celery workers monitor Redis for new messages, pick them up, and execute the corresponding tasks. Redis also serves as the result backend, storing the status and output of completed tasks, which the Flask app can then retrieve. This combination provides a robust and efficient way to handle background processing.

## Project Structure

```
oracle/
├── client/                 # Frontend Next.js application
│   ├── components/
│   ├── pages/
│   ├── public/
│   ├── styles/
│   ├── .env.local          # Frontend environment variables (optional)
│   └── ...
├── server/                 # Backend Flask application
│   ├── data/               # Data files (e.g., celebrity info)
│   ├── results/            # Output directory for generated videos
│   ├── routes/             # API route definitions
│   ├── services/           # Logic for external APIs (OpenAI, PlayHT, Sieve, Twitter)
│   ├── static/             # Static assets for the backend (if any)
│   ├── tasks/              # Celery task definitions
│   ├── twitter_bot/        # Modules related to Twitter bot functionality (e.g., main.py)
│   ├── utils/              # Utility functions
│   ├── venv/               # Python virtual environment (created here, add to .gitignore)
│   ├── app.py              # Main Flask application file
│   ├── celery_app.py       # Celery application setup
│   ├── .env                # Backend environment variables (IMPORTANT!)
│   ├── .env.example        # Example environment file
│   ├── .gitignore          # Specific to server if needed, else use root .gitignore
│   └── ...
├── .gitignore              # Project root .gitignore (ensure server/venv/ is listed)
├── requirements.txt        # Python dependencies for the backend
└── README.md
```

## Usage Instructions

1.  **Access the Application:** Once all necessary services are running (Redis, Celery Worker, Flask Backend, Frontend), open your web browser and navigate to the frontend URL (typically `http://localhost:3000`).
2.  **Enter a Concept:** In the input field, type the concept you want the celebrity to explain.
3.  **Choose a Celebrity:** Select a celebrity from the provided list.
4.  **Generate Video:** Click the "Generate Video" button.
5.  **Wait for Processing:** The request is sent to the backend. Celery workers handle video generation in the background. This may take some time.
6.  **View Video:** Once ready, the video will be displayed or a link provided.
7.  **(Optional) Twitter Sharing:** If the Twitter bot (`server/twitter_bot/main.py`) is running and configured, generated content may be automatically tweeted.

## Troubleshooting

- **Python Virtual Environment Issues:**
  - Ensure you've created the virtual environment inside the `server` directory (`server/venv`).
  - Activate it (`source server/venv/bin/activate`) in each backend terminal _before_ running any Python, Flask, or Celery commands.
  - If `pip install` or script execution fails, verify the virtual environment is active and contains the necessary packages (`pip list`).
- **Sieve Authentication Issues (`sieve login`):**
  - Must be run after activating the virtual environment where `sievedata` is installed.
  - Ensure `sievedata` is listed in `requirements.txt` and installed correctly in `server/venv`.
  - Run `sieve login` again if issues persist.
- **Twitter Bot Issues (`python server/twitter_bot/main.py`):**
  - Verify `TWITTER_*` environment variables in `server/.env`.
  - Ensure `server/twitter_bot/main.py` exists.
  - Run from the project root after activating the virtual environment: `python server/twitter_bot/main.py`.
- **Celery worker not starting / Task issues:**
  - Verify Redis is running and accessible (check `CELERY_BROKER_URL` in `server/.env`).
  - Ensure the virtual environment is active in the Celery terminal.
  - Check Celery worker logs for errors.
- **API Key errors (OpenAI, PlayHT):** Double-check keys in `server/.env`.
- **Video generation fails:** Check Celery worker logs and Sieve authentication.
- **Frontend cannot connect to backend:** Ensure Flask server is running and `NEXT_PUBLIC_API_URL` in `client/.env.local` is correct.

Feel free to open an issue if you encounter problems not covered here.
