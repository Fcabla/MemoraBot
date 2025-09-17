"""Data models and schemas for the application."""

from typing import Optional, Any, Dict, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(BaseModel):
    """Chat message model."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ConversationState(BaseModel):
    """Conversation state management."""
    id: str
    messages: List[Message] = Field(default_factory=list)
    pydantic_messages: Optional[str] = None  # JSON serialized PydanticAI messages
    started_at: datetime
    last_activity: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: str, content: str, tool_calls=None):
        """Add a message to the conversation."""
        self.messages.append(
            Message(
                role=MessageRole(role),
                content=content,
                tool_calls=tool_calls
            )
        )
        self.last_activity = datetime.now()


class FileOperation(BaseModel):
    """File operation result model."""
    operation: str
    bucket: str
    filename: str
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolCall(BaseModel):
    """Tool call information."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    duration_ms: Optional[float] = None


class ChatRequest(BaseModel):
    """Chat request from client."""
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response to client."""
    message: str
    conversation_id: str
    timestamp: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None