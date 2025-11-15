"""
Agent Interface routes
POST /agent/sessions/{session_id}/respond
Internal API called by backend, not directly by UI
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from typing import Union
from database import get_db
from agent.schemas import AgentRequest, AgentResponse, AgentErrorResponse
from agent.service import AgentService

router = APIRouter()


@router.post("/sessions/{session_id}/respond")
async def agent_respond(
    session_id: str,
    request: AgentRequest,
    db: DBSession = Depends(get_db)
) -> Union[AgentResponse, AgentErrorResponse]:
    """
    Agent Interface endpoint
    Called by backend when user sends a message

    This is the main entry point for the Agent Interface
    """
    # Create agent service
    agent_service = AgentService(db)

    # Process request
    response = agent_service.process_request(request)

    return response
