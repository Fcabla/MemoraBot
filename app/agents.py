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
        return """You are MemoraBot, an intelligent file and note management assistant with advanced editing capabilities.

Your primary responsibilities:
1. Help users organize their thoughts and information into well-structured files
2. Intelligently manage files in "buckets" (categories/folders)
3. Make precise, token-efficient edits using smart tools
4. Always search for existing relevant files before creating new ones
5. Use contextual editing instead of rewriting entire files

INTELLIGENT EDITING CAPABILITIES:
- Use edit_file_lines() to replace specific text sections
- Use insert_at_line() for precise line-based insertions
- Use replace_section() for block replacements between markers
- Use smart_append() to add content in the most logical location
- Use preview_file_section() to understand context before editing
- Always show diffs of what changed for transparency

EDITING DECISION PROCESS:
1. For small changes: Use edit_file_lines() or insert_at_line()
2. For section updates: Use replace_section() with clear markers
3. For new content: Use smart_append() with section hints
4. For uncertain changes: Preview first, then edit precisely
5. Avoid write_file() unless creating entirely new files

TOKEN EFFICIENCY RULES:
- Never send entire file contents unless absolutely necessary
- Use preview tools to understand context with minimal tokens
- Make targeted edits that affect only relevant lines
- Provide clear diffs showing exactly what changed
- Combine related edits in a single operation when possible

Key behaviors:
- Be precise and surgical in your edits
- Show transparency about what you're changing and why
- Suggest appropriate file organization strategies
- Remember context from the conversation
- Proactively organize information into logical structures

When you perform file operations, always:
1. Explain your editing strategy and why you chose specific tools
2. Show diffs or clear descriptions of what changed
3. Confirm successful operations with context
4. Suggest next steps or related actions
5. Handle errors gracefully with helpful messages

Remember: You are like a coding agent but for notes and documents - precise, intelligent, and token-efficient."""

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

        @self.agent.tool
        def edit_file_lines(
            ctx: RunContext[AgentDependencies],
            bucket: str,
            filename: str,
            search_text: str,
            replacement_text: str
        ) -> str:
            """Replace specific text in a file with intelligent matching.

            Args:
                bucket: The bucket (folder) name
                filename: The file name
                search_text: Text to find and replace
                replacement_text: New text to replace with

            Returns:
                Diff showing what was changed
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.edit_file_lines(bucket, filename, search_text, replacement_text)

            logger.info(f"Edited lines in: {bucket}/{filename}")
            return result

        @self.agent.tool
        def insert_at_line(
            ctx: RunContext[AgentDependencies],
            bucket: str,
            filename: str,
            line_number: int,
            text: str,
            position: str = "after"
        ) -> str:
            """Insert text at a specific line number.

            Args:
                bucket: The bucket (folder) name
                filename: The file name
                line_number: Line number (1-based) where to insert
                text: Text to insert
                position: 'before', 'after', or 'replace'

            Returns:
                Success message with context
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.insert_at_line(bucket, filename, line_number, text, position)

            logger.info(f"Inserted at line {line_number} in: {bucket}/{filename}")
            return result

        @self.agent.tool
        def replace_section(
            ctx: RunContext[AgentDependencies],
            bucket: str,
            filename: str,
            start_marker: str,
            end_marker: str,
            new_content: str
        ) -> str:
            """Replace content between two markers.

            Args:
                bucket: The bucket (folder) name
                filename: The file name
                start_marker: Text marking start of section
                end_marker: Text marking end of section
                new_content: New content for the section

            Returns:
                Diff showing section replacement
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.replace_section(bucket, filename, start_marker, end_marker, new_content)

            logger.info(f"Replaced section in: {bucket}/{filename}")
            return result

        @self.agent.tool
        def smart_append(
            ctx: RunContext[AgentDependencies],
            bucket: str,
            filename: str,
            content: str,
            section_hint: Optional[str] = None
        ) -> str:
            """Intelligently append content to the best location in the file.

            Args:
                bucket: The bucket (folder) name
                filename: The file name
                content: Content to append
                section_hint: Hint about where to append (e.g., 'shopping', 'tasks')

            Returns:
                Description of where content was added
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.smart_append(bucket, filename, content, section_hint)

            logger.info(f"Smart append to: {bucket}/{filename}")
            return result

        @self.agent.tool
        def preview_file_section(
            ctx: RunContext[AgentDependencies],
            bucket: str,
            filename: str,
            around_text: Optional[str] = None,
            around_line: Optional[int] = None
        ) -> str:
            """Preview a section of a file for context before editing.

            Args:
                bucket: The bucket (folder) name
                filename: The file name
                around_text: Show context around this text
                around_line: Show context around this line number

            Returns:
                File preview with line numbers
            """
            from app.tools import FileTools

            tools = FileTools(ctx.deps.data_dir)
            result = tools.get_file_preview(bucket, filename, around_line, around_text)

            logger.info(f"Previewed section in: {bucket}/{filename}")
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

            # Extract tool usage information - combine calls with returns
            tool_calls = []
            tool_calls_map = {}  # Map to match calls with returns

            for msg in result.new_messages():
                if hasattr(msg, 'parts'):
                    for part in msg.parts:
                        if hasattr(part, 'part_kind'):
                            if part.part_kind == 'tool-call':
                                # This is a tool call
                                tool_id = getattr(part, 'tool_call_id', len(tool_calls_map))
                                tool_calls_map[tool_id] = {
                                    'tool': part.tool_name,
                                    'arguments': getattr(part, 'args', {}),
                                    'result': None  # Will be filled by tool-return
                                }
                            elif part.part_kind == 'tool-return':
                                # This is a tool return, match it with the call
                                tool_id = getattr(part, 'tool_call_id', None)
                                if tool_id in tool_calls_map:
                                    content = getattr(part, 'content', None)
                                    tool_calls_map[tool_id]['result'] = content
                        elif hasattr(part, 'tool_name'):
                            # Fallback for older format
                            tool_calls.append({
                                'tool': part.tool_name,
                                'arguments': getattr(part, 'args', {}),
                                'result': None
                            })

            # Convert map to list, only include complete tool calls
            tool_calls = list(tool_calls_map.values())

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
