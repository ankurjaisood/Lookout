# Marketplace Research Agent – MVP Design Document

## 1. Overview

This document describes the MVP architecture for a system that helps users research and compare online listings (e.g., cars, laptops) and decide which are good deals. The system combines a web UI, a back-end API service, and an AI-powered Agent Interface that uses an LLM and lightweight agent memory.

Goals:

- Help users evaluate and compare listings within a session.
- Provide simple, understandable deal scores and rationales.
- Ask clarifying questions only when necessary.
- Keep the back-end agnostic to specific LLM providers and prompts.
- Keep the data model and infrastructure as simple as possible for an MVP.

Non-goals (MVP):

- Marketplace normalization and staleness management.
- Cross-session comparative “deal history” (“this is better than last month’s Miata”).
- OAuth auth providers, complex logging/analytics, or multi-dimensional scoring.

---

## 2. High-Level Architecture

```text
+-----------+        +----------------+        +----------------------+
|           |  HTTPS |                |  HTTP  |                      |
|   Web UI  +------->+   Back-end     +------->+   Agent Interface    |
|           |        |   API Service  |        |   + Agent Memory     |
+-----------+        +----------------+        +----------------------+
                         |      ^
                         |      |
                         v      |
                     Relational DB         External LLM Provider(s)
                     (app tables)  <---->  (via Agent Interface only)
```

- **Web UI**: Session management, listing input, rankings display, chat interface.
- **Back-end API Service**: Owns all canonical user, session, message, and listing data; exposes endpoints to the UI; calls the Agent Interface.
- **Agent Interface**: Wraps LLM calls, tool usage, and agent memory. Back-end is unaware of prompts, models, or memory internals.
- **Relational DB**: Stores app tables (users, sessions, messages, listings). Agent memory uses a generic `agent_memory` table in the same DB for MVP but is owned logically by the Agent Interface.

---

## 3. Components & Requirements

### 3.1 Web UI

**Responsibilities**

- User login/logout.
- Display list of sessions; create/delete sessions.
- Collect listings for a session (URLs + basic fields).
- Display ranked listings with score-derived labels and rationales.
- Display chat messages and clarifying questions.
- Allow users to remove listings from consideration.

**Core Functional Requirements**

1. The UI shall allow users to sign up and log in with email + password.
2. The UI shall allow users to:
   - Create new sessions with a title and category (e.g., cars, laptops).
   - View a list of their existing sessions.
   - Delete a session.
3. Within a session, the UI shall allow users to:
   - Add listings by entering title, price, URL, and optional metadata.
   - Remove listings from consideration.
   - Send free-form chat messages to the agent.
4. The UI shall display:
   - The chat history for the session.
   - All **active** listings sorted by score (descending).
   - A deal-quality label for each listing derived from its 0–100 score using a fixed threshold mapping.
   - The agent’s rationale text for each evaluated listing.
5. When the session is waiting for a blocking clarifying question, the UI shall:
   - Prominently display the question message.
   - Treat the next user message as the answer.
6. The UI shall surface basic errors (e.g., agent unavailable) in a simple, human-readable way.

---

### 3.2 Back-end API Service

**Responsibilities**

- Authentication and session management.
- Canonical storage of users, sessions, messages, and listings.
- Enforcement of per-user access control.
- Construction of `session_context` and calls to the Agent Interface.
- Application of structured actions returned by the agent (evaluations, clarifications).

**Core Functional Requirements**

1. The back-end shall provide endpoints for:
   - User signup/login (email + password).
   - Session CRUD (create, list, delete).
   - Listing CRUD within a session (create, mark removed).
   - Posting user messages within a session.
   - Fetching session state for the UI (messages + active listings + scores).
2. The back-end shall be the canonical store for:
   - Users, sessions, messages, and listings.
   - Listings’ current 0–100 score and rationale (if evaluated).
3. The back-end shall enforce:
   - That users can only access their own sessions and data.
4. On relevant user actions (new message, new listings, etc.), the back-end shall:
   - Build a `session_context` from DB state.
   - Call `POST /agent/sessions/{session_id}/respond` on the Agent Interface.
   - Store the returned `agent_message` as a `messages` row.
   - Apply returned actions:
     - Update listing scores and rationales.
     - Record blocking clarifying questions and update session state accordingly.
5. When a session is deleted, the back-end shall:
   - Delete all associated messages and listings for that session.
   - Notify or call the Agent Interface to delete any associated session memory.
6. When a user account is deleted (future), the back-end shall:
   - Delete all sessions and related data for that user.
   - Notify or call the Agent Interface to delete any associated user preference memory.

---

### 3.3 Agent Interface & Agent Memory

**Responsibilities**

- Accept structured requests from the back-end and orchestrate LLM calls.
- Encapsulate all prompting, model/provider selection, and tool usage.
- Maintain agent memory (user preferences and session summaries) in `agent_memory`.
- Return a user-facing message and structured actions for the back-end.

**Core Functional Requirements**

1. The Agent Interface shall expose an HTTP endpoint:

   ```http
   POST /agent/sessions/{session_id}/respond
   ```

   taking a request containing:
   - `user_message` (id + text + optional attachment references).
   - `session_context`:
     - `user` (id, locale, timezone).
     - `session` (id, title, category, status).
     - `recent_messages` (truncated chat history).
     - `listings` (all **active** listings for the session, including any existing scores).
2. For each request, the Agent Interface shall:
   - Load user preference and session summary memory for the given user/session (if present).
   - Construct an LLM prompt using the request and memory.
   - Call the configured LLM provider.
3. The Agent Interface shall return a response containing:
   - `agent_message` (text to show to the user).
   - An array of `actions`, where each action is one of:
     - `UPDATE_EVALUATIONS`:
       - List of `{ listing_id, score (0–100), rationale }` entries.
     - `ASK_CLARIFYING_QUESTION`:
       - `{ question, blocking: true }`.
     - `UPDATE_PREFERENCES`:
       - `{ preference_patch }` JSON to modify user preference memory.
4. The Agent Interface shall **not** write directly to the app tables (users/sessions/messages/listings); it shall only write to `agent_memory`. All canonical writes go through the back-end.
5. The Agent Interface shall maintain an `agent_memory` store with entries:
   - `key='user:{user_id}', type='user_preferences'`:
     - Structured JSON of category-wise preferences and an optional NL summary.
   - `key='session:{session_id}', type='session_summary'`:
     - Structured JSON of requirements, a short NL summary, top listing IDs, and open questions.
6. The Agent Interface shall update:
   - User preference memory when the agent infers new preferences or receives `UPDATE_PREFERENCES` internally.
   - Session summary memory when significant session changes occur (requirements, top listings, clarifications).
7. When requested by the back-end (e.g., on user or session deletion), the Agent Interface shall:
   - Delete corresponding `agent_memory` entries for that user/session.

---

### 3.4 Authentication & Logging

**Authentication Requirements**

1. The system shall support simple email + password login:
   - `users` table shall store a unique email and a password hash per user.
2. The back-end shall issue HTTP-only, secure session cookies after successful login and use them to identify the `user_id` on subsequent requests.
3. The Agent Interface shall not receive or process raw passwords; it only receives `user_id` and non-secret profile data.

**Logging Requirements (MVP)**

1. For each call to `POST /agent/sessions/{session_id}/respond`, the back-end shall log:
   - Timestamp.
   - `user_id` and `session_id`.
   - Outcome: `success` or `error`.
   - Duration in ms.
   - Error code/message (if any).
2. Full LLM prompts and responses shall not be logged by default; logging of content shall only be enabled temporarily for debugging and with appropriate caution.

---

## 4. Data Model (Back-end)

The MVP uses a simple relational schema. All tables in this section are owned by the back-end except `agent_memory`, which is logically owned by the Agent Interface.

### 4.1 `users`

```text
users
-----
id             UUID (PK)
email          TEXT UNIQUE NOT NULL
password_hash  TEXT NOT NULL
display_name   TEXT
created_at     TIMESTAMP NOT NULL
updated_at     TIMESTAMP NOT NULL
```

### 4.2 `sessions`

```text
sessions
--------
id                        UUID (PK)
user_id                   UUID (FK → users.id) NOT NULL
title                     TEXT NOT NULL
category                  TEXT NOT NULL        -- e.g. 'cars', 'laptops'
status                    TEXT NOT NULL        -- 'ACTIVE' | 'WAITING_FOR_CLARIFICATION' | 'CLOSED'
pending_clarification_id  UUID NULL            -- FK → messages.id (blocking question message)
created_at                TIMESTAMP NOT NULL
updated_at                TIMESTAMP NOT NULL
```

### 4.3 `messages`

```text
messages
--------
id                    UUID (PK)
session_id            UUID (FK → sessions.id) NOT NULL
sender                TEXT NOT NULL           -- 'user' | 'agent'
type                  TEXT NOT NULL           -- 'normal' | 'clarification_question'
text                  TEXT NOT NULL
is_blocking           BOOLEAN NOT NULL DEFAULT FALSE
clarification_status  TEXT NULL               -- 'pending' | 'answered' | 'skipped'
answer_message_id     UUID NULL               -- FK → messages.id (the user’s answer)
created_at            TIMESTAMP NOT NULL
```

- Blocking clarifying questions are represented as:
  - `sender='agent'`, `type='clarification_question'`, `is_blocking=true`, `clarification_status='pending'`.
- When the user answers:
  - A new user `messages` row is created.
  - The question message’s `clarification_status` is set to `'answered'`, and `answer_message_id` is set.
  - The corresponding `session` is updated to `status='ACTIVE'` and `pending_clarification_id=NULL`.

### 4.4 `listings`

```text
listings
--------
id           UUID (PK)
session_id   UUID (FK → sessions.id) NOT NULL
title        TEXT NOT NULL
url          TEXT
price        NUMERIC(12,2)
currency     TEXT
marketplace  TEXT
metadata     JSONB                    -- arbitrary per-category fields
status       TEXT NOT NULL DEFAULT 'active'   -- 'active' | 'removed'

score        INTEGER NULL             -- 0–100; null until evaluated
rationale    TEXT NULL                -- explanation from the agent

created_at   TIMESTAMP NOT NULL
updated_at   TIMESTAMP NOT NULL
```

- Only `status='active'` listings are:
  - Included in `session_context.listings` for the Agent Interface.
  - Displayed in the main ranking UI.
- The UI derives human-readable labels (`horrible deal`, `poor deal`, `fair deal`, `good deal`, `great deal`) from `score` using a fixed threshold mapping implemented in code.

### 4.5 `agent_memory` (Agent-owned)

```text
agent_memory
------------
key          TEXT PRIMARY KEY         -- e.g. 'user:{user_id}', 'session:{session_id}'
type         TEXT NOT NULL            -- 'user_preferences' | 'session_summary'
data         JSONB NOT NULL           -- structured JSON (preferences/summary)
last_updated TIMESTAMP NOT NULL
```

- `user_preferences` entries contain category-wise preference structures and an optional NL summary for the user.
- `session_summary` entries contain requirements, a short NL summary, and optional top listing IDs and open question strings.

---

## 5. Agent API & Clarifying Question Flow

### 5.1 Agent API: `POST /agent/sessions/{session_id}/respond`

**Request (conceptual shape)**

```json
{
  "api_version": "1.0",
  "user_message": {
    "id": "msg_123",
    "text": "Here are 3 cars I'm considering.",
    "attachments": [
      { "type": "listing_reference", "listing_id": "listing_1" }
    ]
  },
  "session_context": {
    "user": {
      "id": "user_123",
      "locale": "en-US",
      "timezone": "America/Los_Angeles"
    },
    "session": {
      "id": "session_456",
      "title": "Used Miata search",
      "category": "cars",
      "status": "ACTIVE"
    },
    "recent_messages": [
      {
        "id": "msg_120",
        "sender": "user",
        "text": "I care more about reliability than power.",
        "type": "normal",
        "created_at": "2025-11-13T19:50:00Z"
      }
    ],
    "listings": [
      {
        "id": "listing_1",
        "title": "2014 Mazda Miata Club, 78k miles",
        "url": "https://example.com/miata-1",
        "price": 13500,
        "currency": "USD",
        "marketplace": "example_cars",
        "metadata": {
          "year": 2014,
          "mileage": 78000,
          "transmission": "manual"
        },
        "score": 72,
        "rationale": "Previously rated..."
      }
    ]
  }
}
```

**Response (conceptual shape)**

```json
{
  "agent_message": {
    "text": "Thanks for sharing these. Based on your preferences, here's how I rate them..."
  },
  "actions": [
    {
      "type": "UPDATE_EVALUATIONS",
      "evaluations": [
        {
          "listing_id": "listing_1",
          "score": 78,
          "rationale": "Strong service history, clean title, slightly above ideal price."
        },
        {
          "listing_id": "listing_2",
          "score": 65,
          "rationale": "Cheaper but higher mileage and less desirable trim."
        }
      ]
    },
    {
      "type": "ASK_CLARIFYING_QUESTION",
      "question": "How important is having a hardtop versus a soft top?",
      "blocking": true
    },
    {
      "type": "UPDATE_PREFERENCES",
      "preference_patch": {
        "cars": {
          "budget_range": [8000, 15000],
          "important_factors": ["reliability", "manual_transmission"]
        }
      }
    }
  ]
}
```

**Error Response (conceptual)**

```json
{
  "error": {
    "code": "LLM_PROVIDER_UNAVAILABLE",
    "message": "The assistant is temporarily unavailable. Please try again."
  }
}
```

### 5.2 Clarifying Question State Machine

Session state values:

- `ACTIVE`: normal mode; agent can freely evaluate listings.
- `WAITING_FOR_CLARIFICATION`: agent has asked a blocking clarifying question and is waiting for an answer.
- `CLOSED`: session is finished (user archived/deleted, or future extension).

**Transitions**

1. `ACTIVE` → `WAITING_FOR_CLARIFICATION`  
   - Trigger: Agent returns an `ASK_CLARIFYING_QUESTION` action with `blocking=true`.
   - Back-end:
     - Inserts a `messages` row (agent, `type='clarification_question'`, `is_blocking=true`, `clarification_status='pending'`).
     - Updates `sessions.status='WAITING_FOR_CLARIFICATION'` and `pending_clarification_id` to that message ID.

2. `WAITING_FOR_CLARIFICATION` → `ACTIVE`  
   - Trigger: User sends the next message in that session.
   - Back-end:
     - Inserts a `messages` row for the user.
     - Updates the blocking question message:
       - `clarification_status='answered'`, `answer_message_id=<user message id>`.
     - Sets `sessions.status='ACTIVE'` and `pending_clarification_id=NULL`.
     - Calls the Agent API again with updated `session_context`.

3. `ACTIVE` → `CLOSED`  
   - Trigger: User deletes or closes the session.

This supports a single blocking clarifying question at a time while keeping the back-end and Agent Interface responsibilities cleanly separated.

---

## 6. Scoring & Ranking

- The Agent Interface returns a `score` in the range `[0, 100]` for each evaluated listing, along with a textual `rationale`.
- The back-end persists `score` and `rationale` directly in the `listings` table.
- The UI:
  - Sorts active listings primarily by `score` (descending).
  - Maps `score` into a discrete deal label in one of:

    - `horrible deal`
    - `poor deal`
    - `fair deal`
    - `good deal`
    - `great deal`

  using a fixed threshold mapping implemented in the UI/back-end code.

This design keeps the data model simple while allowing clear, user-friendly deal quality indicators derived from a continuous internal score.

