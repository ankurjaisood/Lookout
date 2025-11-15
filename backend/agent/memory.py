"""
Agent Memory System
Task 3.3: Agent Memory System
Manages user preferences and session summaries
"""
from sqlalchemy.orm import Session
import crud
from typing import Optional, Dict, Any


class AgentMemory:
    """
    Manages agent memory (user preferences and session summaries)
    """

    def __init__(self, db: Session):
        self.db = db

    def load_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Load user preferences memory
        Returns structured JSON with category-wise preferences
        """
        key = f"user:{user_id}"
        memory = crud.get_agent_memory(self.db, key=key)

        if memory and memory.type == "user_preferences":
            return memory.data

        # Return default structure if no preferences yet
        return {
            "categories": {},  # e.g., {"cars": {"budget_range": [8000, 15000]}}
            "summary": None  # Natural language summary
        }

    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """
        Save or update user preferences
        """
        key = f"user:{user_id}"
        crud.upsert_agent_memory(
            self.db,
            key=key,
            type="user_preferences",
            data=preferences
        )

    def update_user_preferences(self, user_id: str, preference_patch: Dict[str, Any]):
        """
        Merge new preferences with existing ones (deep merge for nested categories)
        """
        current = self.load_user_preferences(user_id)

        # Deep merge categories (merge at category level, not just top level)
        if "categories" in preference_patch:
            for category, prefs in preference_patch["categories"].items():
                if category not in current["categories"]:
                    current["categories"][category] = {}
                # Merge the preferences for this category
                current["categories"][category].update(prefs)

        # Update summary if provided
        if "summary" in preference_patch:
            current["summary"] = preference_patch["summary"]

        self.save_user_preferences(user_id, current)

    def load_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session summary memory
        Returns structured JSON with requirements, summary, top listings, etc.
        """
        key = f"session:{session_id}"
        memory = crud.get_agent_memory(self.db, key=key)

        if memory and memory.type == "session_summary":
            return memory.data

        # Return default structure if no summary yet
        return {
            "requirements": [],  # List of identified requirements
            "summary": None,  # Natural language summary
            "top_listing_ids": [],  # IDs of current top listings
            "open_questions": []  # Open questions to clarify
        }

    def save_session_summary(self, session_id: str, summary: Dict[str, Any]):
        """
        Save or update session summary
        """
        key = f"session:{session_id}"
        crud.upsert_agent_memory(
            self.db,
            key=key,
            type="session_summary",
            data=summary
        )

    def update_session_summary(
        self,
        session_id: str,
        requirements: Optional[list] = None,
        summary: Optional[str] = None,
        top_listing_ids: Optional[list] = None,
        open_questions: Optional[list] = None
    ):
        """
        Update specific fields in session summary
        """
        current = self.load_session_summary(session_id)

        if requirements is not None:
            current["requirements"] = requirements

        if summary is not None:
            current["summary"] = summary

        if top_listing_ids is not None:
            current["top_listing_ids"] = top_listing_ids

        if open_questions is not None:
            current["open_questions"] = open_questions

        self.save_session_summary(session_id, current)

    def delete_session_memory(self, session_id: str):
        """
        Delete session memory (called when session is deleted)
        """
        key = f"session:{session_id}"
        crud.delete_agent_memory(self.db, key=key)

    def delete_user_memory(self, user_id: str):
        """
        Delete user memory (called when user is deleted)
        """
        key = f"user:{user_id}"
        crud.delete_agent_memory(self.db, key=key)
