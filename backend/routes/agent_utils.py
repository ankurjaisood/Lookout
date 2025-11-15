"""
Shared helper functions for building agent context and processing actions.
"""
from sqlalchemy.orm import Session as DBSession
from typing import List, Optional
import crud
import models
from agent.schemas import (
    SessionContext, UserInfo, SessionInfo, MessageInfo, ListingInfo
)


def build_session_context(
    db: DBSession,
    session: models.Session,
    user: models.User
) -> SessionContext:
    """
    Build a complete SessionContext payload for the agent.
    """
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

    listings = crud.list_listings_by_session(db, session.id, active_only=True)
    listing_infos = []
    for listing in listings:
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
            description=listing.description,
            score=listing.score,
            rationale=listing.rationale
        ))

    return SessionContext(
        user=UserInfo(id=user.id, locale="en-US", timezone="America/Los_Angeles"),
        session=SessionInfo(
            id=session.id,
            title=session.title,
            category=session.category,
            status=session.status,
            requirements=session.requirements
        ),
        recent_messages=message_infos,
        listings=listing_infos
    )


def process_agent_actions(
    db: DBSession,
    session_id: str,
    actions: List[dict],
    agent_message_id: str,
    default_listing_id: Optional[str] = None,
    available_listing_ids: Optional[List[str]] = None
):
    """
    Apply structured agent actions to the database.
    """
    available_listing_ids = available_listing_ids or []
    last_evaluated_listing_id = None
    clarification_state_dirty = False

    for action in actions:
        action_type = action.get("type")

        if action_type == "UPDATE_EVALUATIONS":
            for evaluation in action.get("evaluations", []):
                listing_id = evaluation.get("listing_id")
                score = evaluation.get("score")
                rationale = evaluation.get("rationale")
                if listing_id:
                    crud.update_listing_score(
                        db=db,
                        listing_id=listing_id,
                        score=score,
                        rationale=rationale
                    )
                    last_evaluated_listing_id = listing_id

        elif action_type == "ASK_CLARIFYING_QUESTION":
            question_text = action.get("question")
            is_blocking = action.get("blocking", True)
            listing_id = (
                action.get("listing_id")
                or default_listing_id
                or last_evaluated_listing_id
            )
            if not listing_id and len(available_listing_ids) == 1:
                listing_id = available_listing_ids[0]

            clarification_message = crud.create_message(
                db=db,
                session_id=session_id,
                sender="agent",
                text=question_text,
                type="clarification_question",
                is_blocking=is_blocking,
                clarification_status="pending",
                target_listing_id=listing_id
            )

            clarification_state_dirty = clarification_state_dirty or is_blocking

        elif action_type == "UPDATE_PREFERENCES":
            continue

    if clarification_state_dirty:
        crud.sync_session_clarification_state(db, session_id)
