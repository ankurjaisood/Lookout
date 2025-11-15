"""
Shared helper functions for building agent context and processing actions.
"""
from sqlalchemy.orm import Session as DBSession
from typing import List
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
    agent_message_id: str
):
    """
    Apply structured agent actions to the database.
    """
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

        elif action_type == "ASK_CLARIFYING_QUESTION":
            question_text = action.get("question")
            is_blocking = action.get("blocking", True)

            clarification_message = crud.create_message(
                db=db,
                session_id=session_id,
                sender="agent",
                text=question_text,
                type="clarification_question",
                is_blocking=is_blocking,
                clarification_status="pending"
            )

            if is_blocking:
                crud.update_session_status(
                    db=db,
                    session_id=session_id,
                    status="WAITING_FOR_CLARIFICATION",
                    pending_clarification_id=clarification_message.id
                )

        elif action_type == "UPDATE_PREFERENCES":
            continue
