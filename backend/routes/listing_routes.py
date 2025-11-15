"""
Listing management routes
POST /api/sessions/{session_id}/listings - add listing
GET /api/sessions/{session_id}/listings - get all active listings
PATCH /api/sessions/{session_id}/listings/{listing_id} - mark as removed
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

router = APIRouter()


# Request/Response models
class CreateListingRequest(BaseModel):
    title: str
    url: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    marketplace: Optional[str] = None
    listing_metadata: Optional[dict] = None


class ListingResponse(BaseModel):
    id: str
    session_id: str
    title: str
    url: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    marketplace: Optional[str]
    listing_metadata: Optional[dict]
    status: str
    score: Optional[int]
    rationale: Optional[str]
    created_at: datetime
    updated_at: datetime

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


@router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    session_id: str,
    request: CreateListingRequest,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Add a new listing to a session
    """
    # Verify session ownership
    verify_session_ownership(session_id, current_user, db)

    # Create listing
    listing = crud.create_listing(
        db=db,
        session_id=session_id,
        title=request.title,
        url=request.url,
        price=request.price,
        currency=request.currency,
        marketplace=request.marketplace,
        listing_metadata=request.listing_metadata
    )

    return listing


@router.get("", response_model=List[ListingResponse])
async def list_listings(
    session_id: str,
    active_only: bool = True,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all listings for a session
    """
    # Verify session ownership
    verify_session_ownership(session_id, current_user, db)

    # Get listings
    listings = crud.list_listings_by_session(
        db=db,
        session_id=session_id,
        active_only=active_only
    )

    return listings


@router.patch("/{listing_id}", response_model=ListingResponse)
async def mark_listing_removed(
    session_id: str,
    listing_id: str,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Mark a listing as removed from consideration
    """
    # Verify session ownership
    verify_session_ownership(session_id, current_user, db)

    # Get listing
    listing = crud.get_listing_by_id(db=db, listing_id=listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    # Verify listing belongs to session
    if listing.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing does not belong to this session"
        )

    # Mark as removed
    listing = crud.mark_listing_removed(db=db, listing_id=listing_id)

    return listing
