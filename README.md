# Lookout - Marketplace Research Agent

An AI-powered marketplace research assistant that helps you evaluate and compare online listings to identify the best deals.

## Overview

Lookout combines a React frontend, FastAPI backend, and Google Gemini AI to provide intelligent analysis of marketplace listings (cars, laptops, electronics, etc.). The agent scores listings from 0-100, provides detailed rationales, asks clarifying questions, and learns your preferences over time.

## Features

- **AI-Powered Evaluation**: Get 0-100 scores and detailed rationales for each listing
- **Smart Questions**: Agent asks clarifying questions only when needed
- **Preference Learning**: System remembers your preferences across sessions
- **Session Requirements**: Capture must-have criteria once per session and let the agent enforce them
- **Manual Re-evaluation**: Re-run the agent on any listing with a single click when details change
- **Listing Clarifications**: View and answer one or more agent questions directly on each listing card
- **Inline Editing**: Update listing details/description at any time and the agent re-evaluates automatically
- **Real-time Chat**: Interactive conversation with the AI agent
- **Session Management**: Organize your searches by category
- **Deal Quality Labels**: Clear "horrible/poor/fair/good/great deal" indicators

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│   React UI  │────▶│  FastAPI API │────▶│ Agent Interface│
│   (Vite)    │     │   + SQLite   │     │   + Gemini AI  │
└─────────────┘     └──────────────┘     └────────────────┘
```

**Components:**
- **Frontend**: React + Vite (port 5173)
- **Backend**: FastAPI + SQLAlchemy (port 8000)
- **Database**: SQLite (file-based)
- **AI**: Google Gemini API
- **Memory**: Agent memory for preferences and session summaries

## Prerequisites

- **Python 3.10-3.12** (recommended)
  - Python 3.13 works but may have dependency compatibility issues
  - Python 3.10, 3.11, or 3.12 recommended for best compatibility
- **Node.js 18+**
- **Google Gemini API Key** - Get one at https://makersuite.google.com/app/apikey

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Lookout

# Run the setup script (installs dependencies, creates venv, initializes DB)
./setup.sh
```

### 2. Configure Environment

Edit `.env` and add your Gemini API key:

```bash
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Launch the Application

```bash
# Start both backend and frontend
./start.sh
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Usage Guide

### 1. Create an Account

- Navigate to http://localhost:5173
- Click "Sign up" and create an account
- You'll be automatically logged in

### 2. Create a Session

- Click "New Session"
- Give it a title (e.g., "Find a used Miata")
- Select a category (cars, laptops, electronics, etc.)
- Add your global requirements (e.g., "manual transmission, hardtop, under 50k miles") so the agent keeps them in mind for every listing

### 3. Add Listings

- Click "+ Add Listing"
- Enter listing details:
  - **Title** (required): e.g., "2014 Mazda Miata Club"
  - **URL**: Link to the listing
  - **Price**: Listing price
  - **Currency**: USD, EUR, GBP, etc.
  - **Marketplace**: Where you found it
  - **Description**: Paste the listing description/details so the agent can read it
- The agent automatically evaluates each new listing once you click "Add"

### 4. Chat with the Agent

- Type a message like "Which of these is the best deal?"
- The agent will:
  - Analyze all listings
  - Assign scores (0-100) and quality labels
  - Provide detailed rationales
  - Ask clarifying questions if needed

### 5. Review Results

Each listing shows:
- **Deal Quality Badge**: Horrible/Poor/Fair/Good/Great deal
- **Score Visualization**: 0-100 score with progress bar
- **Rationale**: Detailed explanation of the score
- **Quick Actions**: View listing, remove from consideration
- **Clarifications**: Any outstanding questions about that listing with inline answer forms

### 6. Re-evaluate a Listing

- Hover over the listing title and click the ⟳ button to ask the agent to re-check just that item
- The listing’s score and rationale refresh after the agent responds

### 7. Answer Clarifying Questions Inline

- When the agent needs more info about a listing, the question appears under that listing’s card. The agent can ask multiple questions at once (one specific detail per question).
- Type your answers directly in the inline forms, in any order. The session resumes automatically once all blocking questions are answered.

### 8. Edit Listings Anytime

- Click the “Edit” button on a listing card to adjust title, URL, price, marketplace, or the pasted description
- Saving changes automatically reruns the evaluation so scores and rationales stay current

### 9. Load Demo Data (optional)

- Start the backend so the database is initialized (`./start_backend.sh` or `./start.sh`)
- Run `./demo.sh` (or `./demo.sh path/to/your.json`) from the repo root to populate sessions/listings defined in `demo.json`
- The script inserts sample users/sessions/listings and automatically runs the agent on each listing so you can explore the UI immediately

## Manual Setup (if scripts fail)

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run backend
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

## Project Structure

```
Lookout/
├── backend/               # FastAPI backend
│   ├── agent/            # Agent Interface (Gemini AI)
│   │   ├── service.py    # Main agent orchestrator
│   │   ├── gemini_client.py  # Gemini API client
│   │   ├── memory.py     # Agent memory management
│   │   ├── prompts.py    # Prompt engineering
│   │   └── schemas.py    # Request/response models
│   ├── routes/           # API endpoints
│   │   ├── auth_routes.py
│   │   ├── session_routes.py
│   │   ├── listing_routes.py
│   │   ├── message_routes.py
│   │   └── agent_routes.py
│   ├── models.py         # Database models
│   ├── crud.py           # Database operations
│   ├── database.py       # DB configuration
│   ├── auth.py           # Authentication
│   ├── config.py         # Settings
│   ├── main.py           # FastAPI app
│   └── requirements.txt
├── frontend/             # React frontend
│   ├── src/
│   │   ├── pages/        # Page components
│   │   ├── context/      # React contexts
│   │   ├── services/     # API services
│   │   ├── App.jsx       # Main app component
│   │   └── App.css       # Styles
│   ├── package.json
│   └── vite.config.js
├── docs/                 # Documentation
│   ├── lookout_design.md # Complete design specification
│   └── lookout_preliminary_ui.png
├── claude/               # Claude Code configuration
│   └── tasks.md         # Implementation task breakdown
├── setup.sh             # One-time setup script
├── start.sh             # Launch full stack
├── .env.example         # Environment template
├── CLAUDE.md            # Claude Code guidance
├── changelog.md         # Implementation progress
└── README.md            # This file
```

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

### Sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions` - List user's sessions
- `GET /api/sessions/{id}` - Get session
- `DELETE /api/sessions/{id}` - Delete session
- `GET /api/sessions/{id}/state` - Get complete session state

### Listings
- `POST /api/sessions/{id}/listings` - Add listing
- `GET /api/sessions/{id}/listings` - Get listings
- `PATCH /api/sessions/{id}/listings/{listing_id}` - Mark removed

### Messages
- `POST /api/sessions/{id}/messages` - Send message (triggers agent)
- `GET /api/sessions/{id}/messages` - Get chat history

## Scoring System

Listings are scored 0-100 and mapped to quality labels:

| Score | Label | Color |
|-------|-------|-------|
| 81-100 | Great deal | Green |
| 61-80 | Good deal | Light Green |
| 41-60 | Fair deal | Yellow |
| 21-40 | Poor deal | Orange |
| 0-20 | Horrible deal | Red |

## Agent Capabilities

The AI agent can:

1. **Evaluate Listings**: Analyze price, condition, features, and market value
2. **Ask Questions**: Request clarification about priorities (e.g., "Is mileage or price more important?")
3. **Learn Preferences**: Remember your priorities across conversations
4. **Provide Context**: Explain scores with detailed rationales
5. **Compare Options**: Highlight trade-offs between listings

## Troubleshooting

### Port Already in Use

If port 8000 or 5173 is already in use:

```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

### Gemini API Errors

- Verify your API key in `.env` and `backend/.env`
- Check API quotas at https://makersuite.google.com
- Ensure `GEMINI_API_KEY` is set correctly

### Database Issues

```bash
# Reset the database
rm backend/data/lookout.db

# Restart the backend - it will recreate the DB
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### Frontend Won't Start

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Python Version Issues

**Python 3.13 Compatibility:**
If you encounter dependency installation errors with Python 3.13:
```bash
# Use Python 3.10-3.12 instead (recommended)
# Install pyenv to manage Python versions:
brew install pyenv
pyenv install 3.12.0
pyenv local 3.12.0

# Then re-run setup
./setup.sh
```

**bcrypt/passlib Errors:**
The project requires `bcrypt==4.1.2` for compatibility with passlib. This is already specified in `requirements.txt`.

## Development

### Run Backend Only

```bash
cd backend
./start_backend.sh
```

### Run Frontend Only

```bash
cd frontend
./start_frontend.sh
```

### View API Documentation

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

### Run Tests

The project includes **95 comprehensive tests** covering all major functionality:

**Backend Tests (46 tests):**
```bash
cd backend
source venv/bin/activate
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_crud.py

# Run specific test class
pytest tests/test_crud.py::TestUserCRUD

# Run with coverage report
pytest --cov=. --cov-report=html
```

**Backend Test Coverage:**
- 19 CRUD unit tests
- 13 API integration tests
- 14 agent interface tests

**Frontend Tests (49 tests):**
```bash
cd frontend
npm test

# Run with UI
npm test -- --ui

# Run specific test file
npm test -- api.test.js
```

**Frontend Test Coverage:**
- 14 API service tests
- 7 AuthContext tests
- 7 LoginPage tests
- 8 SignupPage tests
- 13 SessionsPage tests

**Total: 95 tests across full stack** ✅

## Technical Details

### Agent Memory

The system maintains two types of memory:

1. **User Preferences**: Category-specific preferences (e.g., budget range, important factors)
2. **Session Summaries**: Session requirements, top listings, open questions

Memory is stored in the `agent_memory` table and managed by the Agent Interface.

### Clarifying Questions

When the agent needs clarification:

1. Session status changes to `WAITING_FOR_CLARIFICATION`
2. Question is highlighted in the UI
3. User's next message is treated as the answer
4. Session returns to `ACTIVE` state
5. Agent continues with the answer in context

## Contributing

See `claude/tasks.md` for the complete task breakdown and `docs/lookout_design.md` for the detailed design specification.

## License

MIT License - see LICENSE file for details.

## Support

For issues or questions:
- Check `docs/lookout_design.md` for architecture details
- Review `changelog.md` for implementation notes
- Check the troubleshooting section above

---

**Built with Claude Code** 🤖

Generated with assistance from Claude Code (claude.ai/code)
