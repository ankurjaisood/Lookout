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
    agent_context = build_session_context(db, session, current_user)

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
    process_agent_actions(db, session_id, agent_response.actions, agent_message.id)

    return user_message




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
