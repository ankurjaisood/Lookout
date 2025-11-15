"""
Prompt Engineering & Tool Definitions
Task 3.4: Prompt Engineering & Tool Definition
"""
from agent.schemas import SessionContext
from typing import Dict, Any, Optional
import json


class PromptBuilder:
    """
    Constructs prompts for the agent
    """

    @staticmethod
    def build_system_prompt() -> str:
        """System prompt explaining agent's role and capabilities"""
        return """You are a marketplace research assistant helping users evaluate and compare online listings (cars, laptops, electronics, etc.) to identify good deals.

Your responsibilities:
1. Analyze listings within a session and provide 0-100 deal quality scores with clear rationales
2. Ask clarifying questions ONLY when necessary to better evaluate listings
3. Learn and remember user preferences across the session
4. Be concise and helpful

Scoring guidelines:
- 0-20: Horrible deal (significantly overpriced, major red flags)
- 21-40: Poor deal (overpriced or concerning issues)
- 41-60: Fair deal (market rate, nothing special)
- 61-80: Good deal (below market rate, solid value)
- 81-100: Great deal (excellent value, highly recommended)

Consider:
- Price relative to market value
- Condition and quality indicators
- Mileage, age, or usage (for applicable categories)
- Seller reputation and listing quality
- Category-specific factors (e.g., for cars: service history, accident history)

When you evaluate listings, respond with a JSON structure containing:
{
  "message": "Your message to the user",
  "actions": [
    {
      "type": "UPDATE_EVALUATIONS",
      "evaluations": [
        {"listing_id": "id", "score": 75, "rationale": "explanation"}
      ]
    }
  ]
}

If you need to ask a clarifying question:
{
  "message": "Your question to the user",
  "actions": [
    {
      "type": "ASK_CLARIFYING_QUESTION",
      "question": "What's more important: low mileage or lower price?",
      "blocking": true
    }
  ]
}

If you learn new preferences:
{
  "message": "Got it, I'll remember that",
  "actions": [
    {
      "type": "UPDATE_PREFERENCES",
      "preference_patch": {
        "categories": {
          "cars": {"important_factors": ["reliability", "fuel_economy"]}
        }
      }
    }
  ]
}

Always respond with valid JSON wrapped in ```json ... ```
"""

    @staticmethod
    def build_user_context(
        user_preferences: Optional[Dict] = None,
        session_summary: Optional[Dict] = None
    ) -> str:
        """Build context from user preferences and session summary"""
        parts = []

        if user_preferences and user_preferences.get("categories"):
            parts.append("## User Preferences")
            parts.append(json.dumps(user_preferences, indent=2))

        if session_summary and (session_summary.get("requirements") or session_summary.get("summary")):
            parts.append("## Session Summary")
            parts.append(json.dumps(session_summary, indent=2))

        return "\n\n".join(parts) if parts else ""

    @staticmethod
    def build_session_context_text(context: SessionContext) -> str:
        """Convert session context to readable text"""
        parts = []

        # Session info
        parts.append(f"## Current Session")
        parts.append(f"Category: {context.session.category}")
        parts.append(f"Title: {context.session.title}")
        parts.append(f"Status: {context.session.status}")
        if context.session.requirements:
            parts.append("\n## Requirements")
            parts.append(context.session.requirements.strip())

        # Recent messages (conversation history)
        if context.recent_messages:
            parts.append("\n## Recent Conversation")
            for msg in context.recent_messages[-10:]:  # Last 10 messages
                sender = msg.sender.upper()
                parts.append(f"{sender}: {msg.text}")

        # Listings
        parts.append(f"\n## Listings ({len(context.listings)} total)")
        for listing in context.listings:
            parts.append(f"\n### Listing: {listing.title}")
            parts.append(f"ID: {listing.id}")
            if listing.price:
                parts.append(f"Price: {listing.currency or '$'}{listing.price}")
            if listing.url:
                parts.append(f"URL: {listing.url}")
            if listing.marketplace:
                parts.append(f"Marketplace: {listing.marketplace}")
            if listing.listing_metadata:
                parts.append(f"Details: {json.dumps(listing.listing_metadata)}")
            if listing.score is not None:
                parts.append(f"Current Score: {listing.score}/100")
                parts.append(f"Previous Rationale: {listing.rationale}")

        return "\n".join(parts)

    @staticmethod
    def build_full_prompt(
        user_message: str,
        session_context: SessionContext,
        user_preferences: Optional[Dict] = None,
        session_summary: Optional[Dict] = None
    ) -> str:
        """Build the complete prompt for the agent"""
        prompt_parts = [
            PromptBuilder.build_system_prompt(),
            ""
        ]

        # Add user context if available
        user_context = PromptBuilder.build_user_context(user_preferences, session_summary)
        if user_context:
            prompt_parts.append(user_context)
            prompt_parts.append("")

        # Add session context
        prompt_parts.append(PromptBuilder.build_session_context_text(session_context))
        prompt_parts.append("")

        # Add current user message
        prompt_parts.append(f"## User's Current Message")
        prompt_parts.append(user_message)
        prompt_parts.append("")
        prompt_parts.append("Respond with JSON as specified above:")

        return "\n".join(prompt_parts)
