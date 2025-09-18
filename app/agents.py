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
        self.message_adapter = ModelMessagesTypeAdapter

    def _create_agent(self) -> Agent:
        """Create the PydanticAI agent with appropriate model."""

        # Set API keys via environment variables and determine model
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
        elif settings.LLM_PROVIDER == "gemini":
            # Support both GEMINI_API_KEY and GOOGLE_API_KEY
            api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
            if not api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is required for Gemini provider")
            os.environ["GOOGLE_API_KEY"] = api_key
            model_name = 'gemini-2.0-flash'
        else:
            raise ValueError(
                f"Invalid LLM configuration: {settings.LLM_PROVIDER}. "
                "Supported providers: openai, anthropic, gemini"
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
            content: str,
            overwrite: bool = False
        ) -> str:
            """Write content to a new file in a bucket.

            Args:
                bucket: The bucket (folder) name
                filename: The file name to create
                content: Content to write to the file
                overwrite: If True, overwrite existing file

            Returns:
                Confirmation message
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.write_file(bucket, filename, content, overwrite=overwrite)

            logger.info(f"Created/overwrote file: {bucket}/{filename}")
            return result

        @self.agent.tool
        def append_file(
            ctx: RunContext[AgentDependencies],
            bucket: str,
            filename: str,
            content: str,
            separator: str = "\n\n"
        ) -> str:
            """Append content to an existing file.

            Args:
                bucket: The bucket (folder) name
                filename: The file name to append to
                content: Content to append
                separator: Separator to use when appending (default: "\\n\\n")

            Returns:
                Confirmation message
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.append_file(bucket, filename, content, separator=separator)

            logger.info(f"Appended to file: {bucket}/{filename}")
            return result

        @self.agent.tool
        def list_files(
            ctx: RunContext[AgentDependencies],
            bucket: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """List files in a bucket or all buckets with detailed metadata.

            Args:
                bucket: Optional bucket name. If None, lists all buckets.

            Returns:
                List of dictionaries with file metadata
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

        @self.agent.tool
        def get_bucket_stats(
            ctx: RunContext[AgentDependencies]
        ) -> Dict[str, Any]:
            """Get statistics about buckets and files.

            Returns:
                Dictionary with total_buckets, total_files, total_size, and buckets info
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.get_bucket_stats()

            logger.info("Retrieved bucket statistics")
            return result

        @self.agent.tool
        def list_directory(
            ctx: RunContext[AgentDependencies],
            path: str = ""
        ) -> Dict[str, Any]:
            """List directory contents for navigation.

            Args:
                path: Optional path within data directory

            Returns:
                Directory structure with buckets and files
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.list_directory(path)

            logger.info(f"Listed directory: {path or 'root'}")
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
            conversation.add_message("assistant", result.output)

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
                'message': result.output,
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