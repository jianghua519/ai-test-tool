# AI-Powered Web Automation Testing Tool

An intelligent web automation testing platform that features no-code recording, AI-generated test cases, and comprehensive reporting.

## Project Structure

- **backend/**: Microservices for case management, execution, reporting, and AI integration.
  - `case-service`: Manages test cases and recording sessions (FastAPI + SQLite).
  - `exec-service`: Executes test steps using Playwright (Node.js).
  - `report-service`: Handles test results, screenshots, and report generation (FastAPI + Local Storage).
  - `ai-service`: Interface for LLM integration (OpenAI/Ollama).
- **frontend/**: Web management dashboard built with React, Tailwind CSS, and Shadcn UI.
- **browser-extension/**: Chrome extension for recording user interactions.

## Prerequisites

- Docker & Docker Compose (Recommended for deployment)
- Python 3.11+
- Node.js 18+
- Chrome Browser

## Quick Start (Local Development)

### 1. Backend Services

Install dependencies and start services:

```bash
# Case Service
cd backend/case-service
pip install -r requirements.txt
python main.py

# Report Service
cd backend/report-service
pip install -r requirements.txt
python main.py

# AI Service
cd backend/ai-service
pip install -r requirements.txt
python main.py

# Exec Service
cd backend/exec-service
npm install
node src/index.js
```

### 2. Frontend Dashboard

```bash
cd frontend
pnpm install
pnpm dev
```

Access the dashboard at `http://localhost:3000`.

### 3. Browser Extension

1. Open Chrome and navigate to `chrome://extensions/`.
2. Enable "Developer mode".
3. Click "Load unpacked" and select the `browser-extension` directory.
4. Open the extension popup and ensure the server URL is set to `http://localhost:8001` (Case Service).

## Features

- **Multi-language Support**: English, Chinese, Japanese.
- **Theme Support**: Light, Dark, System.
- **AI Integration**: Automatically generates test cases from recorded actions.
- **Visual Reporting**: Detailed HTML reports with screenshots and DOM snapshots.
- **Local Execution**: Runs entirely on your local machine or server without external dependencies.

## License

MIT
