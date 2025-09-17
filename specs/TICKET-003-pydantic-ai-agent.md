# TICKET-003: PydanticAI Agent Configuration

**Status:** COMPLETED
**Phase:** 1 - Foundation & Core Infrastructure
**Priority:** High
**Estimated Effort:** 1 day
**Dependencies:** TICKET-002

## Detail Section

### Purpose
Configure the PydanticAI agent that will serve as the brain of MemoraBot. This agent will process user messages, make decisions about file operations, and coordinate tool usage for intelligent file management.

### Business Value
- Provides natural language understanding capabilities
- Enables intelligent decision-making for file operations
- Creates a conversational interface for knowledge management
- Establishes the AI foundation for all smart features

### Acceptance Criteria
- [x] Agent initializes with appropriate LLM provider
- [x] Agent can process text messages and generate responses
- [x] Tool registration system works
- [x] Agent maintains conversation context
- [x] System prompt guides behavior correctly
- [x] Error handling for LLM failures

## Implementation Section

### Files to Create/Modify

#### 1. `/app/agents.py`
```python
"""PydanticAI agent configuration and setup."""

import os
import logging
import json
from typing import Optional, Any, Dict, List
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessagesTypeAdapter

from app.config import settings
from app.schemas import ConversationState, FileOperation

logger = logging.getLogger("memorabot.agent")


class AgentDependencies(BaseModel):
    """Dependencies passed to the agent."""
    conversation_id: str
    user_id: Optional[str] = None
    data_dir: str = Field(default_factory=lambda: settings.DATA_DIR)


class MemoraBot:
    """Main MemoraBot agent manager."""

    def __init__(self):
        """Initialize MemoraBot with configured LLM."""
        self.agent = self._create_agent()
        self._register_tools()
        self.conversations: Dict[str, ConversationState] = {}
        self.message_adapter = ModelMessagesTypeAdapter()

    def _create_agent(self) -> Agent:
        """Create the PydanticAI agent with appropriate model."""

        # Set API keys via environment variables
        if settings.LLM_PROVIDER == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
            model_name = 'openai:gpt-4-turbo-preview'
        elif settings.LLM_PROVIDER == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
            os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
            model_name = 'anthropic:claude-3-opus-20240229'
        else:
            raise ValueError(
                f"Invalid LLM configuration: {settings.LLM_PROVIDER}. "
                "Supported providers: openai, anthropic"
            )

        # Create agent with system prompt
        agent = Agent(
            model_name,
            system_prompt=self._get_system_prompt(),
            deps_type=AgentDependencies,
            retries=2,
        )

        logger.info(f"Agent initialized with {model_name}")
        return agent

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are MemoraBot, an intelligent file and note management assistant.

Your primary responsibilities:
1. Help users organize their thoughts and information into well-structured files
2. Intelligently manage files in "buckets" (categories/folders)
3. Always search for existing relevant files before creating new ones
4. Append to existing files when appropriate rather than creating duplicates
5. Maintain clear file organization and naming conventions

Key behaviors:
- Be concise and helpful in responses
- Show transparency about file operations you perform
- Suggest appropriate file organization strategies
- Remember context from the conversation
- Proactively organize information into logical structures

File operation guidelines:
- Check if a relevant file exists before creating a new one
- Use descriptive, searchable file names
- Organize files into logical buckets (folders)
- Prefer appending to existing files over creating many small files
- Clean up and merge related content when appropriate

When you perform file operations, always:
1. Explain what you're doing and why
2. Confirm successful operations
3. Suggest next steps or related actions
4. Handle errors gracefully with helpful messages

Remember: You are a helpful assistant focused on keeping the user's information
organized and easily accessible."""

    def _register_tools(self) -> None:
        """Register all available tools with the agent."""

        @self.agent.tool
        def read_file(
            ctx: RunContext[AgentDependencies],
            bucket: str,
            filename: str
        ) -> str:
            """Read contents of a file from a bucket.

            Args:
                bucket: The bucket (folder) name
                filename: The file name to read

            Returns:
                File contents as string
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.read_file(bucket, filename)

            logger.info(f"Read file: {bucket}/{filename}")
            return result

        @self.agent.tool
        def write_file(
            ctx: RunContext[AgentDependencies],
            bucket: str,
            filename: str,
            content: str
        ) -> str:
            """Write content to a new file in a bucket.

            Args:
                bucket: The bucket (folder) name
                filename: The file name to create
                content: Content to write to the file

            Returns:
                Confirmation message
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.write_file(bucket, filename, content)

            logger.info(f"Created file: {bucket}/{filename}")
            return result

        @self.agent.tool
        def append_file(
            ctx: RunContext[AgentDependencies],
            bucket: str,
            filename: str,
            content: str
        ) -> str:
            """Append content to an existing file.

            Args:
                bucket: The bucket (folder) name
                filename: The file name to append to
                content: Content to append

            Returns:
                Confirmation message
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.append_file(bucket, filename, content)

            logger.info(f"Appended to file: {bucket}/{filename}")
            return result

        @self.agent.tool
        def list_files(
            ctx: RunContext[AgentDependencies],
            bucket: Optional[str] = None
        ) -> List[str]:
            """List files in a bucket or all buckets.

            Args:
                bucket: Optional bucket name. If None, lists all buckets.

            Returns:
                List of file paths
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.list_files(bucket)

            logger.info(f"Listed files in: {bucket or 'all buckets'}")
            return result

        @self.agent.tool
        def search_files(
            ctx: RunContext[AgentDependencies],
            query: str,
            bucket: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """Search for files containing specific content.

            Args:
                query: Search query string
                bucket: Optional bucket to search in

            Returns:
                List of matching files with excerpts
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.search_files(query, bucket)

            logger.info(f"Searched for: '{query}' in {bucket or 'all buckets'}")
            return result

        @self.agent.tool
        def delete_file(
            ctx: RunContext[AgentDependencies],
            bucket: str,
            filename: str
        ) -> str:
            """Delete a file from a bucket.

            Args:
                bucket: The bucket (folder) name
                filename: The file name to delete

            Returns:
                Confirmation message
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.delete_file(bucket, filename)

            logger.info(f"Deleted file: {bucket}/{filename}")
            return result

    async def process_message(
        self,
        message: str,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a user message and return response with tool calls."""

        # Get or create conversation state
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationState(
                id=conversation_id,
                started_at=datetime.now()
            )

        conversation = self.conversations[conversation_id]

        # Create dependencies
        deps = AgentDependencies(
            conversation_id=conversation_id,
            user_id=user_id
        )

        try:
            # Prepare message history if exists
            message_history = None
            if conversation.pydantic_messages:
                # Deserialize stored messages back to PydanticAI format
                message_history = self.message_adapter.validate_json(
                    conversation.pydantic_messages
                )

            # Run the agent
            result = await self.agent.run(
                message,
                deps=deps,
                message_history=message_history
            )

            # Store the new messages for future conversations
            conversation.pydantic_messages = result.new_messages_json()

            # Add to our conversation tracking
            conversation.add_message("user", message)
            conversation.add_message("assistant", result.data)

            # Extract tool usage information
            tool_calls = []
            for msg in result.new_messages():
                if hasattr(msg, 'parts'):
                    for part in msg.parts:
                        if hasattr(part, 'tool_name'):
                            tool_calls.append({
                                'tool': part.tool_name,
                                'arguments': getattr(part, 'args', {}),
                            })

            response = {
                'message': result.data,
                'tool_calls': tool_calls,
                'conversation_id': conversation_id,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Processed message for conversation {conversation_id}")
            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            raise

    def get_conversation_history(
        self,
        conversation_id: str
    ) -> Optional[ConversationState]:
        """Get conversation history."""
        return self.conversations.get(conversation_id)

    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation history."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Cleared conversation {conversation_id}")
            return True
        return False


# Global agent instance
memorabot = MemoraBot()
```

#### 2. `/app/schemas.py`
```python
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
```

#### 3. `/app/utils.py`
```python
"""Utility functions for the application."""

import re
import hashlib
from pathlib import Path
from typing import Optional, List
from datetime import datetime


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe file system usage.

    Args:
        filename: Raw filename string

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Limit length
    max_length = 255
    if len(filename) > max_length:
        # Preserve extension if present
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            name, ext = parts
            filename = name[:max_length - len(ext) - 1] + '.' + ext
        else:
            filename = filename[:max_length]

    # Default name if empty
    if not filename:
        filename = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return filename


def sanitize_bucket_name(bucket: str) -> str:
    """Sanitize a bucket name for safe directory usage.

    Args:
        bucket: Raw bucket name

    Returns:
        Sanitized bucket name
    """
    # Convert to lowercase and replace spaces
    bucket = bucket.lower().replace(' ', '_')

    # Remove invalid characters
    bucket = re.sub(r'[^a-z0-9_-]', '', bucket)

    # Remove leading/trailing dashes and underscores
    bucket = bucket.strip('-_')

    # Default name if empty
    if not bucket:
        bucket = "default"

    return bucket


def generate_conversation_id() -> str:
    """Generate a unique conversation ID.

    Returns:
        Unique conversation identifier
    """
    timestamp = datetime.now().isoformat()
    hash_input = f"{timestamp}".encode()
    return hashlib.sha256(hash_input).hexdigest()[:16]


def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text for categorization.

    Args:
        text: Input text

    Returns:
        List of keywords
    """
    # Simple keyword extraction (can be enhanced with NLP)
    # Remove common words and punctuation
    stop_words = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an',
        'and', 'or', 'but', 'in', 'with', 'to', 'for',
        'of', 'as', 'by', 'that', 'this', 'it', 'from',
        'be', 'are', 'was', 'were', 'been'
    }

    # Clean and split text
    words = re.findall(r'\b[a-z]+\b', text.lower())

    # Filter out stop words and short words
    keywords = [
        word for word in words
        if word not in stop_words and len(word) > 3
    ]

    # Return unique keywords
    return list(dict.fromkeys(keywords))[:10]


def suggest_bucket_name(text: str, existing_buckets: List[str]) -> str:
    """Suggest an appropriate bucket name based on content.

    Args:
        text: Content to categorize
        existing_buckets: List of existing bucket names

    Returns:
        Suggested bucket name
    """
    keywords = extract_keywords(text)

    # Check if any keyword matches existing buckets
    for keyword in keywords:
        for bucket in existing_buckets:
            if keyword in bucket or bucket in keyword:
                return bucket

    # Generate new bucket name from keywords
    if keywords:
        # Use the most prominent keyword
        suggested = sanitize_bucket_name(keywords[0])
        if suggested not in existing_buckets:
            return suggested

    # Default to general bucket
    return "notes"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def is_allowed_file_type(filename: str, settings) -> bool:
    """Check if file type is allowed.

    Args:
        filename: File name to check
        settings: Application settings

    Returns:
        True if file type is allowed
    """
    from pathlib import Path
    extension = Path(filename).suffix
    allowed_extensions = getattr(settings, 'ALLOWED_FILE_TYPES', '.txt,.md,.json,.yaml').split(',')
    return extension in allowed_extensions
```

#### 4. Update `/app/routers/chat.py`
```python
"""Chat interface API endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.schemas import ChatRequest, ChatResponse
from app.agents import memorabot
from app.utils import generate_conversation_id

logger = logging.getLogger("memorabot.chat")
router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest) -> ChatResponse:
    """Process a chat message through the agent."""

    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or generate_conversation_id()

    try:
        # Process message through agent
        result = await memorabot.process_message(
            message=request.message,
            conversation_id=conversation_id,
            user_id=request.user_id
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/history/{conversation_id}")
async def get_chat_history(conversation_id: str) -> dict:
    """Get chat history for a conversation."""
    conversation = memorabot.get_conversation_history(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found"
        )

    return {
        "conversation_id": conversation_id,
        "messages": [msg.model_dump() for msg in conversation.messages],
        "started_at": conversation.started_at.isoformat(),
        "last_activity": conversation.last_activity.isoformat()
    }


@router.delete("/clear/{conversation_id}")
async def clear_chat(conversation_id: str) -> dict:
    """Clear a specific chat session."""
    success = memorabot.clear_conversation(conversation_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found"
        )

    return {
        "status": "cleared",
        "conversation_id": conversation_id
    }
```

### Testing Steps

1. **Test agent initialization**
   ```python
   import os
   os.environ["OPENAI_API_KEY"] = "test-key-123"  # Set test key

   from app.agents import MemoraBot
   from app.config import settings

   settings.LLM_PROVIDER = "openai"
   settings.OPENAI_API_KEY = "test-key-123"
   settings.DATA_DIR = "./test_data"

   bot = MemoraBot()
   assert bot.agent is not None
   ```

2. **Test message processing**
   ```python
   import asyncio
   import os
   from app.agents import memorabot

   # Ensure API key is set
   os.environ["OPENAI_API_KEY"] = "your-actual-key"

   async def test():
       response = await memorabot.process_message(
           "Hello, can you help me organize my notes?",
           "test-conversation-123"
       )
       print(response)
       assert 'message' in response
       assert 'conversation_id' in response

   asyncio.run(test())
   ```

3. **Test via API**
   ```bash
   # First ensure your .env file has proper API keys set
   export OPENAI_API_KEY="your-api-key"

   # Start the server
   uvicorn app.main:app --reload

   # Test the chat endpoint
   curl -X POST http://localhost:8000/chat/message \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Create a file called todo.txt in the tasks bucket with my shopping list: milk, eggs, bread"
     }'
   ```

4. **Test tool registration**
   ```python
   from app.agents import MemoraBot

   bot = MemoraBot()

   # Check that tools are registered
   tool_names = [tool.name for tool in bot.agent._tools]
   assert 'read_file' in tool_names
   assert 'write_file' in tool_names
   assert 'list_files' in tool_names
   ```

### Verification Checklist
- [x] Agent initializes with configured LLM (OpenAI, Anthropic, or Gemini)
- [x] API keys are properly set via environment variables
- [x] Tools are registered using @agent.tool decorator
- [x] Tools are synchronous (not async) functions
- [x] Message processing returns proper response format
- [x] Conversation history uses PydanticAI message format
- [x] Error handling works for missing API keys
- [x] Tool calls are extracted from result messages

### Related Files
- `/app/agents.py` - Main agent configuration
- `/app/schemas.py` - Data models
- `/app/utils.py` - Utility functions
- `/app/routers/chat.py` - Chat API endpoints

### Important Notes

1. **API Key Setup**: Ensure you have either `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` set in your environment or `.env` file

2. **Model Names**: Use the correct format:
   - OpenAI: `'openai:gpt-4-turbo-preview'`, `'openai:gpt-3.5-turbo'`
   - Anthropic: `'anthropic:claude-3-opus-20240229'`, `'anthropic:claude-3-sonnet-20240229'`

3. **Tools Must Be Synchronous**: The file tools should be synchronous functions, not async

4. **Message History**: Store using `result.new_messages_json()` and restore using `ModelMessagesTypeAdapter`

### Next Steps
After completion, proceed to TICKET-004 for file manipulation tools implementation.