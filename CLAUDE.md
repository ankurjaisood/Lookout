# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Lookout** is a marketplace research agent MVP that helps users evaluate and compare online listings (cars, laptops, etc.) to identify good deals. The system uses an LLM-powered agent to analyze listings, ask clarifying questions, and provide scored evaluations with rationales.

**Technology Stack:**
- Backend: Python + FastAPI
- Frontend: React
- Database: SQLite
- LLM: Google Gemini API
- Structure: Monorepo

## Architecture

The system has three main components in a clean separation of concerns:

### 1. Web UI (frontend/)
- Session management and listing input
- Displays ranked listings with deal-quality labels
- Chat interface for agent interaction
- Handles blocking clarifying questions from the agent
- Allows users to specify/edit session-level requirements and manually re-run a listing evaluation

### 2. Back-end API Service (backend/)
- **Canonical data owner**: All users, sessions, messages, and listings data
- Authentication (email/password with session cookies)
- Builds `session_context` and calls Agent Interface
- Applies structured actions returned by agent (evaluations, clarifications, preference updates)
- **Critical**: Backend is agnostic to LLM prompts and models

### 3. Agent Interface (backend/agent/)
- **Prompt engineering layer**: Constructs prompts, makes Gemini API calls
- **Agent memory management**: User preferences and session summaries (stored in `agent_memory` table)
- **Tool execution**: Returns structured actions:
  - `UPDATE_EVALUATIONS`: listing scores (0-100) + rationales
  - `ASK_CLARIFYING_QUESTION`: blocking questions to user
  - `UPDATE_PREFERENCES`: learned user preferences
- **Critical**: Agent Interface never writes to app tables (users/sessions/messages/listings), only to `agent_memory`

## Database Schema

Five core tables in SQLite (see `docs/lookout_design.md` Section 4 for full schema):

1. **users**: email, password_hash, display_name
2. **sessions**: user_id, title, category, requirements text, status (ACTIVE | WAITING_FOR_CLARIFICATION | CLOSED)
3. **messages**: session_id, sender (user|agent), type (normal|clarification_question), is_blocking
4. **listings**: session_id, title/url/price/metadata, status (active|removed), score (0-100), rationale
5. **agent_memory**: key (user:{id} or session:{id}), type (user_preferences|session_summary), data (JSONB)

**Key invariants:**
- Only `status='active'` listings are sent to Agent Interface and displayed in UI
- Listing scores are nullable until evaluated by agent
- `agent_memory` is logically owned by Agent Interface; backend calls it for cleanup only

## Clarifying Question Flow

Critical state machine (Section 5.2):

**ACTIVE → WAITING_FOR_CLARIFICATION:**
- Agent returns `ASK_CLARIFYING_QUESTION` with `blocking=true`
- Backend creates message with `type='clarification_question'`, `is_blocking=true`
- Session status → `WAITING_FOR_CLARIFICATION`, `pending_clarification_id` set

**WAITING_FOR_CLARIFICATION → ACTIVE:**
- User sends next message (treated as answer)
- Question message updated: `clarification_status='answered'`, links to answer via `answer_message_id`
- Session status → `ACTIVE`, `pending_clarification_id=NULL`
- Backend calls Agent Interface again with answer in context

## Deal Quality Scoring

- Agent returns continuous score: 0-100
- UI maps to discrete labels:
  - 0-20: Horrible deal
  - 21-40: Poor deal
  - 41-60: Fair deal
  - 61-80: Good deal
  - 81-100: Great deal

## Development Commands

### Initial Setup
```bash
./setup.sh          # One-time setup: creates venv, installs deps, initializes DB
```

### Running the Application
```bash
./start.sh                      # Launch full stack (backend + frontend)
cd backend && ./start_backend.sh  # Backend only (port 8000)
cd frontend && ./start_frontend.sh # Frontend only (port 5173 or 3000)
```

### Backend Development
```bash
cd backend
source venv/bin/activate        # Activate virtual environment
uvicorn main:app --reload       # Run with hot reload
pytest                          # Run tests
pytest tests/test_agent.py      # Run single test file
```

### Frontend Development
```bash
cd frontend
npm run dev                     # Start dev server
npm run build                   # Production build
npm test                        # Run tests
```

## Environment Variables

Required in `.env` (see `.env.example`):
- `GEMINI_API_KEY`: Google Gemini API key
- `DATABASE_URL`: SQLite path (default: `sqlite:///./data/lookout.db`)
- `SECRET_KEY`: Session signing secret
- `FRONTEND_URL`: Frontend origin (CORS)
- `BACKEND_URL`: Backend API URL

## API Endpoints

Key backend endpoints (FastAPI auto-docs at `/docs`):

**Auth:**
- POST `/api/auth/signup`, `/api/auth/login`, `/api/auth/logout`
- GET `/api/auth/me`

**Sessions:**
- POST/GET `/api/sessions`
- GET/DELETE `/api/sessions/{session_id}`
- GET `/api/sessions/{session_id}/state` (unified: session + messages + listings)

**Listings:**
- POST/GET `/api/sessions/{session_id}/listings`
- PATCH `/api/sessions/{session_id}/listings/{listing_id}` (mark removed)
- POST `/api/sessions/{session_id}/listings/{listing_id}/reevaluate` (manual re-run of a single listing)

**Messages:**
- POST `/api/sessions/{session_id}/messages` (triggers agent call)
- GET `/api/sessions/{session_id}/messages`

**Agent Interface (internal):**
- POST `/agent/sessions/{session_id}/respond` (called by backend, not UI)

## Key Design Principles

1. **Separation of concerns**: Backend owns data, Agent Interface owns prompts/LLM/memory
2. **Stateless agent calls**: Each agent request includes full `session_context` (user, session, messages, listings)
3. **Memory efficiency**: Agent memory (preferences, session summaries) reduces need to send full chat history
4. **Single blocking question**: Only one clarifying question at a time, simple state machine
5. **Delete cascades**: Session deletion must clean up messages, listings, AND agent_memory

## Implementation Reference

See `claude/tasks.md` for complete task breakdown with:
- 8 phases (32 tasks total, including post-MVP enhancements)
- Priorities (P0-P3)
- Dependencies and acceptance criteria
- Estimated timeline: 30-50 minutes for AI-assisted development

Full specification: `docs/lookout_design.md`
