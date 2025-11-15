"""
Session management routes
POST /api/sessions - create session
GET /api/sessions - list user's sessions
GET /api/sessions/{session_id} - get session details
DELETE /api/sessions/{session_id} - delete session
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import List, Optional, Dict
from collections import defaultdict
from datetime import datetime
from database import get_db
import crud
import models
from auth import get_current_user

router = APIRouter()


# Request/Response models
class CreateSessionRequest(BaseModel):
    title: str
    category: str
    requirements: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    requirements: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    user_id: str
    title: str
    category: str
    requirements: Optional[str]
    status: str
    pending_clarification_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Session state response models
class MessageInState(BaseModel):
    id: str
    sender: str
    type: str
    text: str
    is_blocking: bool
    clarification_status: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ClarificationInListing(BaseModel):
    id: str
    text: str
    is_blocking: bool
    clarification_status: Optional[str]
    answer_message_id: Optional[str]
    answer_text: Optional[str]
    created_at: datetime


class ListingInState(BaseModel):
    id: str
    title: str
    url: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    marketplace: Optional[str]
    listing_metadata: Optional[dict]
    description: Optional[str]
    score: Optional[int]
    rationale: Optional[str]
    created_at: datetime
    clarifications: List[ClarificationInListing]

    class Config:
        from_attributes = True


class SessionStateResponse(BaseModel):
    session: SessionResponse
    messages: List[MessageInState]
    listings: List[ListingInState]


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new session for the current user
    """
    session = crud.create_session(
        db=db,
        user_id=current_user.id,
        title=request.title,
        category=request.category,
        requirements=request.requirements
    )
    return session


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List all sessions for the current user
    """
    sessions = crud.list_sessions_by_user(db=db, user_id=current_user.id)
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get a specific session by ID
    """
    session = crud.get_session_by_id(db=db, session_id=session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )

    return session


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update session metadata (title, category, requirements)
    """
    session = crud.get_session_by_id(db=db, session_id=session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this session"
        )

    updated = crud.update_session(
        db=db,
        session_id=session_id,
        title=request.title,
        category=request.category,
        requirements=request.requirements
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return updated


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete a session (cascades to messages and listings)
    """
    session = crud.get_session_by_id(db=db, session_id=session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this session"
        )

    # Delete session (also deletes agent memory)
    crud.delete_session(db=db, session_id=session_id)

    return None


@router.get("/{session_id}/state", response_model=SessionStateResponse)
async def get_session_state(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get complete session state (session + messages + listings)
    Unified endpoint for UI to fetch everything in one call
    """
    session = crud.get_session_by_id(db=db, session_id=session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )

    # Get messages
    messages = crud.list_messages_by_session(db=db, session_id=session_id)

    # Get listings (active only)
    listings = crud.list_listings_by_session(db=db, session_id=session_id, active_only=True)

    # Map clarifying questions to their listings
    clarifications = crud.list_listing_clarifications_by_session(db=db, session_id=session_id)
    clarifications_map = defaultdict(list)
    for clarification in clarifications:
        if not clarification.target_listing_id:
            continue
        answer_text = clarification.answer_message.text if clarification.answer_message else None
        clarifications_map[clarification.target_listing_id].append(
            ClarificationInListing(
                id=clarification.id,
                text=clarification.text,
                is_blocking=clarification.is_blocking,
                clarification_status=clarification.clarification_status,
                answer_message_id=clarification.answer_message_id,
                answer_text=answer_text,
                created_at=clarification.created_at
            )
        )

    listing_states: List[ListingInState] = []
    for listing in listings:
        metadata_value = listing.__dict__.get('listing_metadata', {})
        if not isinstance(metadata_value, dict):
            metadata_value = {}

        listing_states.append(
            ListingInState(
                id=listing.id,
                title=listing.title,
                url=listing.url,
                price=float(listing.price) if listing.price is not None else None,
                currency=listing.currency,
                marketplace=listing.marketplace,
                listing_metadata=metadata_value,
                description=listing.description,
                score=listing.score,
                rationale=listing.rationale,
                created_at=listing.created_at,
                clarifications=clarifications_map.get(listing.id, [])
            )
        )

    return SessionStateResponse(
        session=session,
        messages=messages,
        listings=listing_states
    )
