#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JSON_FILE="${1:-$ROOT_DIR/demo.json}"

if [[ ! -f "$JSON_FILE" ]]; then
  echo "Demo data file not found: $JSON_FILE" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/backend:${PYTHONPATH:-}"
cd "$ROOT_DIR/backend"

DB_PATH="$ROOT_DIR/backend/data/lookout.db"
if [[ -f "$DB_PATH" ]]; then
  echo "Resetting database at $DB_PATH"
  rm -f "$DB_PATH"
fi

PYTHON_BIN="$ROOT_DIR/backend/venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3 || command -v python)"
fi

"$PYTHON_BIN" - "$JSON_FILE" <<'PY'
import json
import pathlib
import sys

import models
import crud
from database import init_db, SessionLocal
from agent.service import AgentService
from agent.schemas import AgentRequest, AgentErrorResponse, UserMessage as AgentUserMessage
from routes.agent_utils import build_session_context, process_agent_actions, _question_answered_by_context

from typing import Dict, Any


def load_demo(json_path: pathlib.Path):
    init_db()
    db = SessionLocal()
    agent_service = AgentService(db)

    with json_path.open() as f:
        payload = json.load(f)

    for user_data in payload.get("users", []):
        email = user_data["email"]
        user = crud.get_user_by_email(db, email)
        if not user:
            user = crud.create_user(
                db=db,
                email=email,
                password=user_data.get("password", "password123"),
                display_name=user_data.get("display_name")
            )
            print(f"Created user: {email}")
        else:
            print(f"Using existing user: {email}")

        for session_data in user_data.get("sessions", []):
            existing_session = (
                db.query(models.Session)
                .filter(
                    models.Session.user_id == user.id,
                    models.Session.title == session_data["title"]
                )
                .first()
            )
            if existing_session:
                session = existing_session
                print(f"  Using existing session: {session.title}")
            else:
                session = crud.create_session(
                    db=db,
                    user_id=user.id,
                    title=session_data["title"],
                    category=session_data.get("category", "other"),
                    requirements=session_data.get("requirements")
                )
                print(f"  Created session: {session.title}")

            for listing_data in session_data.get("listings", []):
                listing = crud.create_listing(
                    db=db,
                    session_id=session.id,
                    title=listing_data["title"],
                    url=listing_data.get("url"),
                    price=listing_data.get("price"),
                    currency=listing_data.get("currency"),
                    marketplace=listing_data.get("marketplace"),
                    listing_metadata=listing_data.get("metadata"),
                    description=listing_data.get("description")
                )
                print(f"    Added listing: {listing.title}")
                _evaluate_listing(db, agent_service, session, user, listing, f'Demo evaluation for "{listing.title}"')

    db.close()


def _evaluate_listing(db, agent_service, session, user, listing, reason_text):
    user_message = crud.create_message(
        db=db,
        session_id=session.id,
        sender="user",
        text=reason_text,
        type="normal"
    )

    agent_context = build_session_context(db, session, user)
    agent_request = AgentRequest(
        user_message=AgentUserMessage(id=user_message.id, text=user_message.text),
        session_context=agent_context
    )

    response = agent_service.process_request(agent_request)
    if isinstance(response, AgentErrorResponse):
        print(f"      ⚠️ Agent error: {response.error.message}")
        return

    agent_message = crud.create_message(
        db=db,
        session_id=session.id,
        sender="agent",
        text=response.agent_message.text,
        type="normal"
    )

    listing_contexts = {
        lst.id: {
            "listing_metadata": lst.listing_metadata,
            "description": lst.description
        }
        for lst in agent_context.listings
    }

    process_agent_actions(
        db=db,
        session_id=session.id,
        actions=response.actions,
        agent_message_id=agent_message.id,
        default_listing_id=listing.id,
        available_listing_ids=[lst.id for lst in agent_context.listings],
        listing_contexts=listing_contexts
    )

    updated_listing = crud.get_listing_by_id(db=db, listing_id=listing.id)
    _auto_resolve_clarifications(db, session.id, updated_listing, listing_contexts.get(listing.id))
    print(f"      Evaluation complete: score={updated_listing.score}, rationale={updated_listing.rationale}")


def _auto_resolve_clarifications(db, session_id, listing, listing_context):
    if not listing or not listing_context:
        return

    pending = crud.list_pending_clarifications_for_listing(
        db=db,
        session_id=session_id,
        listing_id=listing.id
    )

    resolved = False
    for clarification in pending:
        if _question_answered_by_context(clarification.text, listing_context):
            auto_msg = crud.create_message(
                db=db,
                session_id=session_id,
                sender="agent",
                text="Automatically resolved after demo update.",
                type="normal"
            )
            crud.update_message_clarification(
                db=db,
                message_id=clarification.id,
                clarification_status="answered",
                answer_message_id=auto_msg.id
            )
            resolved = True

    if resolved:
        crud.sync_session_clarification_state(db, session_id)


if __name__ == "__main__":
    json_path = pathlib.Path(sys.argv[1])
    load_demo(json_path)
PY
