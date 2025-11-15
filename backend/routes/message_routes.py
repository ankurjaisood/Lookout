"""
Message and chat routes
POST /api/sessions/{session_id}/messages - send user message (triggers agent)
GET /api/sessions/{session_id}/messages - get chat history
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database import get_db
import crud
import models
from auth import get_current_user
from agent.schemas import (
    AgentRequest, UserMessage as AgentUserMessage,
    SessionContext, UserInfo, SessionInfo, MessageInfo, ListingInfo,
    AgentErrorResponse
)
from agent.service import AgentService

router = APIRouter()


# Request/Response models
class SendMessageRequest(BaseModel):
    text: str


class MessageResponse(BaseModel):
    id: str
    session_id: str
    sender: str
    type: str
    text: str
    is_blocking: bool
    clarification_status: Optional[str]
    answer_message_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


def verify_session_ownership(session_id: str, current_user: models.User, db: DBSession):
    """Helper to verify user owns the session"""
    session = crud.get_session_by_id(db=db, session_id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    return session


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Send a user message (triggers agent response)
    """
    # Verify session ownership
    session = verify_session_ownership(session_id, current_user, db)

    # Handle clarifying question answer flow
    if session.status == "WAITING_FOR_CLARIFICATION" and session.pending_clarification_id:
        # This message is an answer to a clarifying question
        user_message = crud.create_message(
            db=db,
            session_id=session_id,
            sender="user",
            text=request.text,
            type="normal"
        )

        # Update clarification question status
        crud.update_message_clarification(
            db=db,
            message_id=session.pending_clarification_id,
            clarification_status="answered",
            answer_message_id=user_message.id
        )

        # Update session status back to ACTIVE
        crud.update_session_status(
            db=db,
            session_id=session_id,
            status="ACTIVE",
            pending_clarification_id=None
        )

        # Refresh session
        session = crud.get_session_by_id(db, session_id)

    else:
        # Normal message flow
        user_message = crud.create_message(
            db=db,
            session_id=session_id,
            sender="user",
            text=request.text,
            type="normal"
        )

    # Build session context for agent
    agent_context = _build_session_context(db, session, current_user)

    # Create agent request
    agent_request = AgentRequest(
        user_message=AgentUserMessage(
            id=user_message.id,
            text=user_message.text
        ),
        session_context=agent_context
    )

    # Call agent service
    agent_service = AgentService(db)
    agent_response = agent_service.process_request(agent_request)

    # Handle agent error
    if isinstance(agent_response, AgentErrorResponse):
        # Create error message
        error_message = crud.create_message(
            db=db,
            session_id=session_id,
            sender="agent",
            text=agent_response.error.message,
            type="normal"
        )
        return user_message

    # Create agent message
    agent_message = crud.create_message(
        db=db,
        session_id=session_id,
        sender="agent",
        text=agent_response.agent_message.text,
        type="normal"
    )

    # Process actions
    _process_agent_actions(db, session_id, agent_response.actions, agent_message.id)

    return user_message


def _build_session_context(
    db: DBSession,
    session: models.Session,
    user: models.User
) -> SessionContext:
    """
    Build comprehensive session context for agent request

    This function gathers all necessary context for the agent to evaluate listings:
    - User information (ID, locale, timezone)
    - Session metadata (ID, title, category, status)
    - Recent message history (last 20 messages)
    - All active listings with current scores and rationales

    The context is structured according to the agent API specification
    (see docs/lookout_design.md Section 5.1)

    Args:
        db: Database session
        session: Current session object
        user: Current user object

    Returns:
        SessionContext object ready for agent API call
    """
    # Get recent messages
    messages = crud.list_messages_by_session(db, session.id, limit=20)
    message_infos = [
        MessageInfo(
            id=msg.id,
            sender=msg.sender,
            text=msg.text,
            type=msg.type,
            created_at=str(msg.created_at)
        )
        for msg in messages
    ]

    # Get active listings
    listings = crud.list_listings_by_session(db, session.id, active_only=True)
    listing_infos = []
    for listing in listings:
        # Access listing_metadata via __dict__ to avoid SQLAlchemy MetaData collision
        metadata_value = listing.__dict__.get('listing_metadata', {})
        if not isinstance(metadata_value, dict):
            metadata_value = {}

        listing_infos.append(ListingInfo(
            id=listing.id,
            title=listing.title,
            url=listing.url,
            price=float(listing.price) if listing.price else None,
            currency=listing.currency,
            marketplace=listing.marketplace,
            listing_metadata=metadata_value,
            score=listing.score,
            rationale=listing.rationale
        ))

    return SessionContext(
        user=UserInfo(id=user.id, locale="en-US", timezone="America/Los_Angeles"),
        session=SessionInfo(
            id=session.id,
            title=session.title,
            category=session.category,
            status=session.status
        ),
        recent_messages=message_infos,
        listings=listing_infos
    )


def _process_agent_actions(
    db: DBSession,
    session_id: str,
    actions: list,
    agent_message_id: str
):
    """
    Process actions returned by agent and apply to database

    This function implements the action processing logic described in the design doc.
    It handles three types of actions:

    1. UPDATE_EVALUATIONS:
       - Updates listing scores (0-100) and rationales in database
       - Multiple listings can be evaluated in one action

    2. ASK_CLARIFYING_QUESTION:
       - Creates a clarification question message
       - If blocking=true, implements state machine transition:
         Session status: ACTIVE → WAITING_FOR_CLARIFICATION
         Sets pending_clarification_id

    3. UPDATE_PREFERENCES:
       - No backend action needed (handled by agent memory)

    Args:
        db: Database session
        session_id: Current session ID
        actions: List of action dictionaries from agent
        agent_message_id: ID of the agent's message (for linking)

    State Machine (for clarifying questions):
        ACTIVE → WAITING_FOR_CLARIFICATION (when agent asks blocking question)
        WAITING_FOR_CLARIFICATION → ACTIVE (when user answers, handled in send_message)

    See docs/lookout_design.md Section 5.2 for full state machine specification
    """
    for action in actions:
        action_type = action.get("type")

        if action_type == "UPDATE_EVALUATIONS":
            # Update listing scores and rationales
            evaluations = action.get("evaluations", [])
            for eval_data in evaluations:
                crud.update_listing_score(
                    db=db,
                    listing_id=eval_data.get("listing_id"),
                    score=eval_data.get("score"),
                    rationale=eval_data.get("rationale")
                )

        elif action_type == "ASK_CLARIFYING_QUESTION":
            # Create clarifying question message
            question_text = action.get("question")
            is_blocking = action.get("blocking", True)

            question_message = crud.create_message(
                db=db,
                session_id=session_id,
                sender="agent",
                type="clarification_question",
                text=question_text,
                is_blocking=is_blocking,
                clarification_status="pending"
            )

            if is_blocking:
                # Update session status
                crud.update_session_status(
                    db=db,
                    session_id=session_id,
                    status="WAITING_FOR_CLARIFICATION",
                    pending_clarification_id=question_message.id
                )

        elif action_type == "UPDATE_PREFERENCES":
            # Preferences are handled by agent service in memory
            # Nothing to do in backend
            pass


@router.get("", response_model=List[MessageResponse])
async def list_messages(
    session_id: str,
    limit: Optional[int] = None,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get chat history for a session
    """
    # Verify session ownership
    verify_session_ownership(session_id, current_user, db)

    # Get messages
    messages = crud.list_messages_by_session(
        db=db,
        session_id=session_id,
        limit=limit
    )

    return messages
