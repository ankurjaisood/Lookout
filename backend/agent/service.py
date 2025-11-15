"""
Agent Service
Task 3.5: Action Processing
Main orchestrator for agent responses

This module is the core of the AI agent functionality. It:
1. Loads agent memory (user preferences, session summaries)
2. Builds comprehensive prompts with context
3. Calls the Gemini LLM API
4. Parses structured responses (evaluations, questions, preference updates)
5. Updates agent memory based on learned information

Flow:
    User Message → Build Context → Load Memory → Create Prompt →
    Call Gemini → Parse Response → Process Actions → Update Memory → Return

The agent can perform three types of actions:
- UPDATE_EVALUATIONS: Score listings 0-100 with rationales
- ASK_CLARIFYING_QUESTION: Request user clarification (can be blocking)
- UPDATE_PREFERENCES: Learn and store user preferences
"""
from sqlalchemy.orm import Session
from agent.schemas import AgentRequest, AgentResponse, AgentMessage, AgentErrorResponse, AgentError
from agent.gemini_client import GeminiClient
from agent.memory import AgentMemory
from agent.prompts import PromptBuilder
from typing import Dict, Any, Union
import json


class AgentService:
    """
    Main agent service - orchestrates LLM calls, memory, and action processing

    This is the primary interface between the backend API and the AI agent.
    It handles the complete lifecycle of an agent interaction:
    - Memory retrieval and storage
    - Prompt construction
    - LLM API calls
    - Response parsing
    - Action processing

    Attributes:
        db: SQLAlchemy database session
        gemini: Gemini API client for LLM calls
        memory: Agent memory manager (preferences & summaries)
        prompt_builder: Utility for constructing prompts
    """

    def __init__(self, db: Session):
        """
        Initialize agent service with database session

        Args:
            db: SQLAlchemy session for database operations
        """
        self.db = db
        self.gemini = GeminiClient()
        self.memory = AgentMemory(db)
        self.prompt_builder = PromptBuilder()

    def process_request(self, request: AgentRequest) -> Union[AgentResponse, AgentErrorResponse]:
        """
        Main entry point - process agent request and return response

        This method orchestrates the complete agent interaction:
        1. Load user preferences and session summary from memory
        2. Build a comprehensive prompt with all context
        3. Call Gemini API with the prompt
        4. Parse the JSON response
        5. Process any actions (evaluations, questions, preferences)
        6. Return structured response to backend

        Args:
            request: AgentRequest containing user message and session context

        Returns:
            AgentResponse with message and actions, or AgentErrorResponse on failure

        Example Response:
            {
                "agent_message": {"text": "Here's my analysis..."},
                "actions": [
                    {"type": "UPDATE_EVALUATIONS", "evaluations": [...]},
                    {"type": "ASK_CLARIFYING_QUESTION", "question": "...", "blocking": true}
                ]
            }
        """
        try:
            # 1. Load memory
            user_id = request.session_context.user.id
            session_id = request.session_context.session.id

            user_preferences = self.memory.load_user_preferences(user_id)
            session_summary = self.memory.load_session_summary(session_id)

            # 2. Build prompt
            prompt = self.prompt_builder.build_full_prompt(
                user_message=request.user_message.text,
                session_context=request.session_context,
                user_preferences=user_preferences,
                session_summary=session_summary
            )

            # 3. Call Gemini
            gemini_response = self.gemini.generate_response(prompt)

            # 4. Parse response
            parsed = self.gemini.parse_json_response(gemini_response["text"])

            if not parsed:
                # If JSON parsing fails, return text as message with no actions
                return AgentResponse(
                    agent_message=AgentMessage(text=gemini_response["text"]),
                    actions=[]
                )

            # 5. Extract message and actions
            agent_message_text = parsed.get("message", "")
            actions = parsed.get("actions", [])

            # 6. Process actions (update memory if needed)
            processed_actions = self._process_actions(actions, user_id, session_id)

            return AgentResponse(
                agent_message=AgentMessage(text=agent_message_text),
                actions=processed_actions
            )

        except Exception as e:
            return AgentErrorResponse(
                error=AgentError(
                    code="LLM_PROVIDER_ERROR",
                    message=f"The assistant encountered an error: {str(e)}"
                )
            )

    def _process_actions(
        self,
        actions: list,
        user_id: str,
        session_id: str
    ) -> list:
        """
        Process actions returned by the agent and update memory as needed

        This method handles the three action types:
        1. UPDATE_EVALUATIONS: Passed through to backend for listing updates
        2. ASK_CLARIFYING_QUESTION: Passed through for state machine handling
        3. UPDATE_PREFERENCES: Updates user preference memory immediately

        Args:
            actions: List of action dictionaries from agent response
            user_id: User ID for preference updates
            session_id: Session ID for context

        Returns:
            List of processed actions to be handled by backend

        Note:
            Preference updates are applied to memory here and not passed
            to backend, as they're internal to the agent system.
        """
        processed = []

        for action in actions:
            action_type = action.get("type")

            if action_type == "UPDATE_EVALUATIONS":
                # Just pass through - backend will update listing scores
                processed.append(action)

            elif action_type == "ASK_CLARIFYING_QUESTION":
                # Just pass through - backend will handle state transition
                processed.append(action)

            elif action_type == "UPDATE_PREFERENCES":
                # Update user preferences in memory
                preference_patch = action.get("preference_patch", {})
                self.memory.update_user_preferences(user_id, preference_patch)
                # Don't pass to backend - just update memory
                processed.append(action)

            else:
                # Unknown action type - pass through anyway
                processed.append(action)

        return processed
