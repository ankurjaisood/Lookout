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
    AgentErrorResponse
)
from agent.service import AgentService
from routes.agent_utils import build_session_context, process_agent_actions

router = APIRouter(prefix="/messages")
clarification_router = APIRouter(prefix="/clarifications")


# Request/Response models
class SendMessageRequest(BaseModel):
    text: str


class ClarificationAnswerRequest(BaseModel):
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

    clarification_message = None
    if session.status == "WAITING_FOR_CLARIFICATION" and session.pending_clarification_id:
        clarification_message = crud.get_message_by_id(db, session.pending_clarification_id)

    user_message, session = _create_user_message_with_optional_clarification(
        db=db,
        session=session,
        text=request.text,
        clarification_message=clarification_message
    )

    return _call_agent_and_record_response(db, session, current_user, user_message)


@clarification_router.post("/{clarification_id}/answer", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def answer_clarification(
    session_id: str,
    clarification_id: str,
    request: ClarificationAnswerRequest,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Answer a specific clarifying question (typically from a listing card)
    """
    session = verify_session_ownership(session_id, current_user, db)

    clarification_message = crud.get_message_by_id(db, clarification_id)
    if not clarification_message or clarification_message.session_id != session_id or clarification_message.type != "clarification_question":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clarifying question not found"
        )

    user_message, session = _create_user_message_with_optional_clarification(
        db=db,
        session=session,
        text=request.text,
        clarification_message=clarification_message
    )

    return _call_agent_and_record_response(db, session, current_user, user_message)




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


def _create_user_message_with_optional_clarification(
    db: DBSession,
    session: models.Session,
    text: str,
    clarification_message: Optional[models.Message] = None
):
    """
    Create a user message and optionally mark a clarification as answered.
    Returns tuple of (user_message, updated_session).
    """
    user_message = crud.create_message(
        db=db,
        session_id=session.id,
        sender="user",
        text=text,
        type="normal"
    )

    updated_session = session

    if clarification_message:
        crud.update_message_clarification(
            db=db,
            message_id=clarification_message.id,
            clarification_status="answered",
            answer_message_id=user_message.id
        )

        updated_session = crud.sync_session_clarification_state(db, session.id) or session

    return user_message, updated_session


def _call_agent_and_record_response(
    db: DBSession,
    session: models.Session,
    current_user: models.User,
    user_message: models.Message
):
    """
    Build agent context, call agent service, and persist resulting actions.
    """
    agent_context = build_session_context(db, session, current_user)
    agent_request = AgentRequest(
        user_message=AgentUserMessage(
            id=user_message.id,
            text=user_message.text
        ),
        session_context=agent_context
    )

    agent_service = AgentService(db)
    agent_response = agent_service.process_request(agent_request)

    if isinstance(agent_response, AgentErrorResponse):
        crud.create_message(
            db=db,
            session_id=session.id,
            sender="agent",
            text=agent_response.error.message,
            type="normal"
        )
        return user_message

    agent_message = crud.create_message(
        db=db,
        session_id=session.id,
        sender="agent",
        text=agent_response.agent_message.text,
        type="normal"
    )

    listing_context_map = {
        lst.id: {
            "listing_metadata": lst.listing_metadata,
            "description": lst.description
        }
        for lst in agent_context.listings
    }

    process_agent_actions(
        db=db,
        session_id=session.id,
        actions=agent_response.actions,
        agent_message_id=agent_message.id,
        default_listing_id=None,
        available_listing_ids=[listing.id for listing in agent_context.listings],
        listing_contexts=listing_context_map
    )

    return user_message
