# Lookout - Marketplace Research Agent MVP - Implementation Tasks

This document contains the prioritized task breakdown for implementing the Marketplace Research Agent MVP as defined in `docs/lookout_design.md`.

## Technology Stack

- **Backend**: Python + FastAPI
- **Frontend**: React
- **Database**: SQLite
- **LLM Provider**: Google Gemini API
- **Repository Structure**: Monorepo

## Implementation Progress

**Last Updated**: 2025-11-16

- ✅ **Phase 0**: Project Setup & Infrastructure (4/4 tasks complete)
- ✅ **Phase 1**: Database Layer (2/2 tasks complete)
- ✅ **Phase 2**: Back-end API Core (4/4 tasks complete)
- ✅ **Phase 3**: Agent Interface (5/5 tasks complete)
- ✅ **Phase 4**: Back-end Integration (3/3 tasks complete)
- ✅ **Phase 5**: Frontend Implementation (7/7 tasks complete)
- ✅ **Phase 6**: Testing & Quality (4/4 tasks complete)
- ✅ **Phase 7**: Documentation & Polish (1/2 tasks complete - seed data optional)
- ✅ **Phase 8**: Post-MVP Enhancements (1/1 tasks complete)

**Overall Progress**: 32/32 tasks completed (100%) - MVP COMPLETE + Enhancements!

---

## Phase 0: Project Setup & Infrastructure

### Task 0.1: Initialize Monorepo Structure
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 2 (High-Level Architecture)
**Dependencies**: None

Create the base monorepo directory structure:
```
/
├── backend/           # FastAPI backend + Agent Interface
├── frontend/          # React frontend
├── docs/              # Existing documentation
├── claude/            # Claude Code configuration
└── README.md          # Project overview
```

**Acceptance Criteria**:
- [x] Directory structure created
- [x] Root-level README.md with project overview
- [x] .gitignore configured for Python and Node.js

**Status**: ✅ COMPLETED

### Task 0.2: Backend Python Environment Setup
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 3.2 (Back-end API Service)
**Dependencies**: Task 0.1

**Acceptance Criteria**:
- [ ] Python virtual environment setup (venv or poetry)
- [ ] requirements.txt or pyproject.toml created
- [ ] Core dependencies installed:
  - FastAPI
  - Uvicorn (ASGI server)
  - SQLAlchemy
  - Pydantic
  - python-jose (JWT)
  - passlib (password hashing)
  - google-generativeai (Gemini SDK)
  - pytest (testing)
- [ ] Backend can run with `uvicorn main:app --reload`

### Task 0.3: Frontend React Setup
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 3.1 (Web UI)
**Dependencies**: Task 0.1

**Acceptance Criteria**:
- [ ] React app initialized (using Vite or Create React App)
- [ ] Core dependencies installed:
  - React Router
  - Axios or Fetch for API calls
  - Basic UI library (optional: MUI, Tailwind, etc.)
- [ ] Development server runs successfully
- [ ] Basic folder structure (components, pages, services, utils)

### Task 0.4: Setup & Launch Scripts
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 2 (High-Level Architecture)
**Dependencies**: Task 0.2, Task 0.3

Create automation scripts for easy installation and launch on macOS.

**Scripts to create**:
- `setup.sh` - One-time setup (install dependencies, create venv, init database)
- `start.sh` - Launch entire stack (backend + frontend in parallel)
- `backend/start_backend.sh` - Launch backend only
- `frontend/start_frontend.sh` - Launch frontend only
- `.env.example` - Template for environment variables

**Acceptance Criteria**:
- [ ] `setup.sh` in root:
  - Creates Python virtual environment
  - Installs Python dependencies
  - Initializes SQLite database
  - Installs Node.js dependencies
  - Copies .env.example to .env with placeholder values
  - Executable with `chmod +x`
- [ ] `start.sh` in root:
  - Activates Python venv
  - Starts backend on port 8000 (background process)
  - Starts frontend on port 5173 or 3000
  - Displays URLs when ready
  - Handles Ctrl+C to stop both processes
  - Executable with `chmod +x`
- [ ] `.env.example` includes:
  - GEMINI_API_KEY=your_api_key_here
  - DATABASE_URL=sqlite:///./data/lookout.db
  - SECRET_KEY=your_secret_key_here
  - FRONTEND_URL=http://localhost:5173
  - BACKEND_URL=http://localhost:8000
- [ ] All scripts work on macOS (tested with bash/zsh)
- [ ] Scripts include helpful echo messages for progress

---

## Phase 1: Database Layer

### Task 1.1: Database Schema Design & Setup
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 4 (Data Model)
**Dependencies**: Task 0.2

Create SQLite database with all required tables.

**Tables to implement**:
1. `users` (Section 4.1)
2. `sessions` (Section 4.2)
3. `messages` (Section 4.3)
4. `listings` (Section 4.4)
5. `agent_memory` (Section 4.5)

**Acceptance Criteria**:
- [ ] SQLAlchemy models created for all 5 tables
- [ ] Database initialization script
- [ ] Foreign key relationships properly defined
- [ ] Indexes on commonly queried fields (user_id, session_id)
- [ ] Database file created at backend/data/lookout.db

### Task 1.2: Database Access Layer (DAL)
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 3.2 (Back-end API Service)
**Dependencies**: Task 1.1

Create database access functions for CRUD operations.

**Acceptance Criteria**:
- [ ] CRUD functions for users (create, get_by_email, get_by_id)
- [ ] CRUD functions for sessions (create, list_by_user, get_by_id, delete)
- [ ] CRUD functions for messages (create, list_by_session)
- [ ] CRUD functions for listings (create, list_by_session, update_score, mark_removed)
- [ ] CRUD functions for agent_memory (get, upsert, delete)
- [ ] Proper session/transaction management
- [ ] Basic error handling

---

## Phase 2: Back-end API Core

### Task 2.1: Authentication System
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 3.4 (Authentication & Logging)
**Dependencies**: Task 1.2

Implement email/password authentication with session cookies.

**Acceptance Criteria**:
- [ ] POST /api/auth/signup endpoint (email validation, password hashing)
- [ ] POST /api/auth/login endpoint (credential verification, session cookie)
- [ ] POST /api/auth/logout endpoint (cookie invalidation)
- [ ] GET /api/auth/me endpoint (current user info)
- [ ] Password hashing using bcrypt/passlib
- [ ] HTTP-only, secure session cookies
- [ ] Authentication dependency for protected routes
- [ ] Proper error responses (401, 409 for duplicate email)

### Task 2.2: Session Management Endpoints
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 3.2, Requirement 1
**Dependencies**: Task 2.1

**Endpoints**:
- POST /api/sessions (create new session)
- GET /api/sessions (list user's sessions)
- GET /api/sessions/{session_id} (get session details)
- DELETE /api/sessions/{session_id} (delete session)

**Acceptance Criteria**:
- [ ] All endpoints implemented with proper auth
- [ ] User can only access their own sessions
- [ ] Session creation validates title and category
- [ ] Session deletion cascades to messages and listings
- [ ] Session deletion notifies Agent Interface to clean up memory
- [ ] Proper HTTP status codes (200, 201, 404, 403)

### Task 2.3: Listing Management Endpoints
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 3.2, Requirement 1
**Dependencies**: Task 2.2

**Endpoints**:
- POST /api/sessions/{session_id}/listings (add listing)
- GET /api/sessions/{session_id}/listings (get all active listings)
- PATCH /api/sessions/{session_id}/listings/{listing_id} (mark as removed)

**Acceptance Criteria**:
- [ ] All endpoints implemented with proper auth
- [ ] Listings tied to sessions owned by authenticated user
- [ ] Listing creation validates required fields (title, price, url)
- [ ] Metadata field accepts arbitrary JSON
- [ ] Mark removed sets status='removed', doesn't delete
- [ ] GET endpoint only returns status='active' listings by default
- [ ] Listings returned sorted by score (descending), nulls last

### Task 2.4: Message & Chat Endpoints
**Priority**: P1
**Design Doc Reference**: Section 3.2, Requirement 1
**Dependencies**: Task 2.2

**Endpoints**:
- POST /api/sessions/{session_id}/messages (send user message)
- GET /api/sessions/{session_id}/messages (get chat history)

**Acceptance Criteria**:
- [ ] POST creates user message and calls Agent Interface
- [ ] GET returns messages ordered by created_at
- [ ] Messages include sender, type, text, blocking status
- [ ] Proper handling of blocking clarification questions
- [ ] Agent response stored as agent message after Agent Interface call

---

## Phase 3: Agent Interface

### Task 3.1: Agent Interface Core Structure
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 3.3 (Agent Interface & Agent Memory)
**Dependencies**: Task 1.2

Set up the Agent Interface as a FastAPI module within the backend.

**Acceptance Criteria**:
- [ ] Agent Interface module structure (`backend/agent/`)
- [ ] POST /agent/sessions/{session_id}/respond endpoint skeleton
- [ ] Request/response Pydantic models matching design doc Section 5.1
- [ ] Error handling and error response format
- [ ] Logging for agent calls (timestamp, user_id, session_id, outcome, duration)

### Task 3.2: Gemini API Integration
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 3.3, Requirement 2
**Dependencies**: Task 3.1

Integrate Google Gemini API for LLM calls.

**Acceptance Criteria**:
- [ ] Gemini SDK initialized with API key from environment
- [ ] Function to build prompt from session_context and memory
- [ ] Function to call Gemini API with constructed prompt
- [ ] Error handling for API failures (rate limits, timeouts, etc.)
- [ ] Model configuration (temperature, max_tokens, etc.)
- [ ] Response parsing

### Task 3.3: Agent Memory System
**Priority**: P0 (Blocking)
**Design Doc Reference**: Section 3.3, Requirements 5-7
**Dependencies**: Task 3.1

Implement agent memory for user preferences and session summaries.

**Acceptance Criteria**:
- [ ] Load user preferences from agent_memory (key='user:{user_id}')
- [ ] Load session summary from agent_memory (key='session:{session_id}')
- [ ] Update user preferences when agent infers new preferences
- [ ] Update session summary when requirements or clarifications change
- [ ] Delete memory entries on session/user deletion
- [ ] Memory structures match design doc Section 4.5

### Task 3.4: Prompt Engineering & Tool Definition
**Priority**: P1
**Design Doc Reference**: Section 3.3, Requirements 2-3
**Dependencies**: Task 3.2, Task 3.3

Create system prompts and tool definitions for the agent.

**Acceptance Criteria**:
- [ ] System prompt that explains agent's role and capabilities
- [ ] Prompt includes session_context (user, session, messages, listings)
- [ ] Prompt includes loaded memory (preferences, session summary)
- [ ] Tool definitions for:
  - UPDATE_EVALUATIONS (listing_id, score, rationale)
  - ASK_CLARIFYING_QUESTION (question, blocking)
  - UPDATE_PREFERENCES (preference_patch)
- [ ] Gemini function calling configured for these tools
- [ ] Prompt instructs agent to ask minimal clarifying questions
- [ ] Prompt instructs agent to provide clear rationales

### Task 3.5: Action Processing
**Priority**: P1
**Design Doc Reference**: Section 3.3, Requirement 3 & Section 5
**Dependencies**: Task 3.4

Parse and structure agent actions from LLM response.

**Acceptance Criteria**:
- [ ] Parse tool calls from Gemini response
- [ ] Convert to standardized action format:
  - UPDATE_EVALUATIONS with evaluations array
  - ASK_CLARIFYING_QUESTION with question and blocking flag
  - UPDATE_PREFERENCES with preference_patch
- [ ] Extract agent_message text from response
- [ ] Handle cases where agent provides message without actions
- [ ] Validate action structures before returning

---

## Phase 4: Back-end Integration

### Task 4.1: Agent Interface Call Integration
**Priority**: P1
**Design Doc Reference**: Section 3.2, Requirement 4
**Dependencies**: Task 2.4, Task 3.5

Integrate Agent Interface calls into message endpoint.

**Acceptance Criteria**:
- [ ] POST /api/sessions/{session_id}/messages builds session_context
- [ ] session_context includes user, session, recent_messages, listings
- [ ] Call POST /agent/sessions/{session_id}/respond
- [ ] Store agent_message as new message row
- [ ] Process UPDATE_EVALUATIONS action (update listing scores/rationales)
- [ ] Process ASK_CLARIFYING_QUESTION action (create message, update session status)
- [ ] Process UPDATE_PREFERENCES action (trigger memory update)
- [ ] Handle agent errors gracefully

### Task 4.2: Clarifying Question State Machine
**Priority**: P1
**Design Doc Reference**: Section 5.2 (Clarifying Question State Machine)
**Dependencies**: Task 4.1

Implement session state transitions for clarifying questions.

**Acceptance Criteria**:
- [ ] ACTIVE → WAITING_FOR_CLARIFICATION transition:
  - Create clarification message with is_blocking=true
  - Update session status and pending_clarification_id
- [ ] WAITING_FOR_CLARIFICATION → ACTIVE transition:
  - User message links to clarification via answer_message_id
  - Clarification message marked as answered
  - Session status back to ACTIVE
  - Agent called again with answer in context
- [ ] UI-facing endpoint returns session status
- [ ] Block new listing additions when WAITING_FOR_CLARIFICATION

### Task 4.3: Session State Endpoint
**Priority**: P1
**Design Doc Reference**: Section 3.1, Requirement 4
**Dependencies**: Task 2.3, Task 4.1

Unified endpoint for UI to fetch complete session state.

**Endpoint**:
- GET /api/sessions/{session_id}/state

**Acceptance Criteria**:
- [ ] Returns session info (title, category, status)
- [ ] Returns all messages (chat history)
- [ ] Returns all active listings with scores/rationales
- [ ] Listings sorted by score (descending)
- [ ] Includes pending clarification question if WAITING_FOR_CLARIFICATION
- [ ] Single efficient query (minimize DB round-trips)

---

## Phase 5: Frontend Implementation

### Task 5.1: Frontend Routing & Layout
**Priority**: P1
**Design Doc Reference**: Section 3.1
**Dependencies**: Task 0.3

**Acceptance Criteria**:
- [ ] React Router setup with routes:
  - /login
  - /signup
  - /sessions (session list)
  - /sessions/:sessionId (session detail)
- [ ] Basic layout component (header, main content)
- [ ] Navigation between routes

### Task 5.2: Authentication UI
**Priority**: P1
**Design Doc Reference**: Section 3.1, Requirement 1
**Dependencies**: Task 5.1, Task 2.1

**Acceptance Criteria**:
- [ ] Login page (email, password, submit)
- [ ] Signup page (email, password, confirm password, submit)
- [ ] Auth state management (Context API or state library)
- [ ] Session cookie handling
- [ ] Redirect to /sessions after login
- [ ] Protected routes (redirect to /login if not authenticated)
- [ ] Logout functionality
- [ ] Display current user email in header

### Task 5.3: Session List UI
**Priority**: P1
**Design Doc Reference**: Section 3.1, Requirements 2-3
**Dependencies**: Task 5.2, Task 2.2

**Acceptance Criteria**:
- [ ] Display list of user's sessions
- [ ] Create new session form (title, category dropdown)
- [ ] Click session to navigate to /sessions/:sessionId
- [ ] Delete session button with confirmation
- [ ] Empty state when no sessions exist
- [ ] Session list updates after create/delete

### Task 5.4: Session Detail - Listings Display
**Priority**: P1
**Design Doc Reference**: Section 3.1, Requirements 3-4
**Dependencies**: Task 5.3, Task 2.3, Task 4.3

**Acceptance Criteria**:
- [ ] Fetch session state on mount
- [ ] Display listings as cards (title, price, url, marketplace)
- [ ] Show deal quality label derived from score:
  - Horrible deal (0-20)
  - Poor deal (21-40)
  - Fair deal (41-60)
  - Good deal (61-80)
  - Great deal (81-100)
- [ ] Display rationale for each listing
- [ ] Listings sorted by score (highest first)
- [ ] "Remove from consideration" button per listing
- [ ] Visual distinction for unevaluated listings (score=null)

### Task 5.5: Session Detail - Add Listing Form
**Priority**: P1
**Design Doc Reference**: Section 3.1, Requirement 3
**Dependencies**: Task 5.4

**Acceptance Criteria**:
- [ ] Form to add new listing (title, price, url, optional metadata)
- [ ] Metadata fields specific to category (e.g., year/mileage for cars)
- [ ] Form validation (required fields)
- [ ] Submit creates listing via API
- [ ] Listing appears in list immediately after creation
- [ ] Form resets after successful submission

### Task 5.6: Session Detail - Chat Interface
**Priority**: P1
**Design Doc Reference**: Section 3.1, Requirements 3-5
**Dependencies**: Task 5.4, Task 2.4, Task 4.1

**Acceptance Criteria**:
- [ ] Display chat messages (user and agent)
- [ ] Visual distinction between user/agent messages
- [ ] Text input field at bottom
- [ ] Send message button
- [ ] Message sends to POST /api/sessions/{session_id}/messages
- [ ] Chat auto-scrolls to latest message
- [ ] Blocking clarification questions prominently displayed
- [ ] When session is WAITING_FOR_CLARIFICATION:
  - Show highlighted question
  - Next user message treated as answer
- [ ] Loading indicator while agent responds

### Task 5.7: Error Handling & Loading States
**Priority**: P2
**Design Doc Reference**: Section 3.1, Requirement 6
**Dependencies**: Task 5.6

**Acceptance Criteria**:
- [ ] Loading spinners for async operations
- [ ] Error messages for failed API calls
- [ ] Network error handling (agent unavailable, timeout)
- [ ] Form validation errors displayed inline
- [ ] Toast/notification system for success messages
- [ ] Graceful degradation when agent is slow/unavailable

---

## Phase 6: Testing & Quality

### Task 6.1: Backend Unit Tests
**Priority**: P2
**Design Doc Reference**: Implicit requirement for quality
**Dependencies**: Task 4.3

**Acceptance Criteria**:
- [ ] Tests for database CRUD functions
- [ ] Tests for authentication (signup, login, password hashing)
- [ ] Tests for session CRUD with access control
- [ ] Tests for listing CRUD and scoring updates
- [ ] Tests for message creation and agent integration
- [ ] Mock Gemini API calls in tests
- [ ] Test coverage for error cases

### Task 6.2: Agent Interface Tests
**Priority**: P2
**Design Doc Reference**: Section 3.3
**Dependencies**: Task 3.5

**Acceptance Criteria**:
- [ ] Tests for memory load/save
- [ ] Tests for action parsing from LLM responses
- [ ] Tests for prompt construction
- [ ] Mock Gemini API responses
- [ ] Test clarifying question flow
- [ ] Test preference update flow

### Task 6.3: Add Inline Documentation
**Priority**: P2
**Design Doc Reference**: Code quality requirement
**Dependencies**: All implementation tasks

**Acceptance Criteria**:
- [x] Module-level docstrings
- [x] Function docstrings with Args/Returns
- [x] Inline comments for complex logic
- [x] API endpoint documentation

**Status**: ✅ COMPLETED

### Task 6.4: Frontend Unit Tests
**Priority**: P2
**Design Doc Reference**: Quality and testing requirement
**Dependencies**: Task 5.7

**Acceptance Criteria**:
- [x] Tests for API service functions (14 tests)
- [x] Tests for AuthContext provider and hooks (7 tests)
- [x] Tests for LoginPage component (7 tests)
- [x] Tests for SignupPage component (8 tests)
- [x] Tests for SessionsPage component (13 tests)
- [x] Mock API calls in all tests
- [x] Test user interactions with @testing-library/user-event
- [x] Vitest configuration and setup

**Status**: ✅ COMPLETED
**Test Results**: All 49 frontend tests passing

---

## Phase 7: Documentation & Polish

### Task 7.1: Setup Documentation
**Priority**: P1
**Dependencies**: Task 0.4, All implementation tasks

**Acceptance Criteria**:
- [ ] Comprehensive README.md with:
  - **Project Overview**: Brief description of the marketplace research agent
  - **Prerequisites**: Python 3.10+, Node.js 18+, macOS compatibility note
  - **Quick Start**: Three simple steps:
    1. Clone repo
    2. Run `./setup.sh`
    3. Run `./start.sh`
  - **Environment Variables**: Reference to .env.example, how to get Gemini API key
  - **Manual Setup**: Step-by-step if scripts fail
  - **Running the Application**:
    - Full stack: `./start.sh`
    - Backend only: `cd backend && ./start_backend.sh`
    - Frontend only: `cd frontend && ./start_frontend.sh`
  - **Accessing the Application**:
    - Frontend: http://localhost:5173 (or 3000)
    - Backend API: http://localhost:8000
    - API Docs: http://localhost:8000/docs
  - **Project Structure**: Directory tree with explanations
  - **Troubleshooting**: Common issues (port conflicts, missing API key, etc.)
- [ ] Backend API documentation (FastAPI auto-docs at /docs)
- [ ] SETUP.md (detailed installation guide for different scenarios)
- [ ] Architecture diagram or reference to design doc

### Task 7.2: Seed Data & Demo
**Priority**: P3
**Dependencies**: Task 7.1

**Acceptance Criteria**:
- [ ] Seed script to create demo user
- [ ] Seed script to create sample session with listings
- [ ] Sample car listings with realistic data
- [ ] Sample preferences in agent memory
- [ ] Instructions to run demo

---

## Phase 8: Post-MVP Enhancements

### Task 8.1: Session Requirements & Manual Listing Re-evaluation
**Priority**: P1  
**Dependencies**: Phases 2-6

**Acceptance Criteria**:
- [x] Add session-level `requirements` field end-to-end (DB, CRUD, API, agent context)
- [x] UI for creating and editing requirements (session creation + detail view)
- [x] Manual listing re-evaluation endpoint (`POST /api/sessions/{session_id}/listings/{listing_id}/reevaluate`)
- [x] Frontend control (reload icon with progress state) to trigger reevaluation
- [x] New backend + frontend tests covering the endpoint and API client helpers
- [x] Documentation updates (README, CLAUDE.md, design doc, changelog) explaining the workflow

**Status**: ✅ COMPLETED

---

## Priority Legend

- **P0**: Blocking - must be completed before dependent tasks
- **P1**: Core MVP functionality
- **P2**: Important for quality and usability
- **P3**: Nice to have, polish

## Estimated Phase Durations (AI-Assisted Development)

- Phase 0: 3-5 minutes (project setup, scripts)
- Phase 1: 3-5 minutes (database models and CRUD)
- Phase 2: 5-7 minutes (API endpoints)
- Phase 3: 5-8 minutes (Agent Interface with Gemini)
- Phase 4: 3-5 minutes (integration logic)
- Phase 5: 10-15 minutes (React UI components)
- Phase 6: 3-5 minutes (basic tests)
- Phase 7: 2-3 minutes (documentation)
- Phase 8: 2-4 minutes (session requirements & manual reevaluation)

**Total Estimated Time**: 30-50 minutes for working MVP

*Note: Times assume rapid iteration with Claude Code. Manual human development would take significantly longer (25-35 hours).*

---

## Notes

1. All tasks reference the design document (`docs/lookout_design.md`) for detailed specifications
2. Tasks are ordered by dependency - earlier phases must be completed before later ones
3. Within each phase, tasks can be parallelized where dependencies allow
4. Testing is integrated throughout but formalized in Phase 6
5. Each task includes clear acceptance criteria to define "done"
