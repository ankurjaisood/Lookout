"""
Agent Interface request/response schemas
Based on docs/lookout_design.md Section 5.1
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# Request schemas
class UserInfo(BaseModel):
    id: str
    locale: str = "en-US"
    timezone: str = "America/Los_Angeles"


class SessionInfo(BaseModel):
    id: str
    title: str
    category: str
    status: str
    requirements: Optional[str] = None


class MessageInfo(BaseModel):
    id: str
    sender: str
    text: str
    type: str
    created_at: str


class ListingInfo(BaseModel):
    id: str
    title: str
    url: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    marketplace: Optional[str]
    listing_metadata: Optional[Dict]
    score: Optional[int]
    rationale: Optional[str]


class SessionContext(BaseModel):
    user: UserInfo
    session: SessionInfo
    recent_messages: List[MessageInfo]
    listings: List[ListingInfo]


class UserMessage(BaseModel):
    id: str
    text: str


class AgentRequest(BaseModel):
    api_version: str = "1.0"
    user_message: UserMessage
    session_context: SessionContext


# Response schemas
class EvaluationAction(BaseModel):
    listing_id: str
    score: int  # 0-100
    rationale: str


class UpdateEvaluationsAction(BaseModel):
    type: str = "UPDATE_EVALUATIONS"
    evaluations: List[EvaluationAction]


class AskClarifyingQuestionAction(BaseModel):
    type: str = "ASK_CLARIFYING_QUESTION"
    question: str
    blocking: bool = True


class UpdatePreferencesAction(BaseModel):
    type: str = "UPDATE_PREFERENCES"
    preference_patch: Dict[str, Any]


class AgentMessage(BaseModel):
    text: str


class AgentResponse(BaseModel):
    agent_message: AgentMessage
    actions: List[Dict[str, Any]]  # Can be any of the action types


class AgentError(BaseModel):
    code: str
    message: str


class AgentErrorResponse(BaseModel):
    error: AgentError
