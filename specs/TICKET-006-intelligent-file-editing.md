# TICKET-006: Intelligent File Editing

**Status:** TODO
**Phase:** 3 - Enhanced File Management
**Priority:** High
**Estimated Effort:** 1 day
**Dependencies:** TICKET-004 (COMPLETED)

## Detail Section

### Purpose
Replace basic append/overwrite operations with intelligent file editing capabilities similar to coding agents. Enable precise line-level modifications, contextual replacements, and smart content insertion without consuming excessive tokens by sending entire file contents.

### Business Value
- **Massive Token Savings**: Avoid sending full file contents for small edits (90%+ token reduction)
- **Precise Modifications**: Edit specific sections without affecting other content
- **Better User Experience**: Natural editing commands like "update line 5", "replace the shopping section"
- **Coding Agent Similarity**: Behave like modern AI coding assistants with intelligent file operations

### Acceptance Criteria
- [ ] Smart text replacement finds and replaces specific content sections
- [ ] Line-based editing for precise modifications
- [ ] Section-based replacement using markers or content matching
- [ ] Diff-style output showing exactly what changed
- [ ] Token-efficient operations (send only relevant context)
- [ ] Fallback to current append/write for edge cases
- [ ] All operations remain synchronous for PydanticAI compatibility

## Implementation Section

### Core Philosophy
Mimic how coding agents work:
1. **Analyze request** → Understand what needs to be changed
2. **Find relevant content** → Locate the right section/lines to modify
3. **Make precise changes** → Edit only what's necessary
4. **Provide clear feedback** → Show exactly what was changed

### Files to Create/Modify

#### 1. Enhance `/app/tools.py` - Add Intelligent Editing Tools

Add these new methods to the `FileTools` class:

```python
def edit_file_lines(
    self,
    bucket: str,
    filename: str,
    search_text: str,
    replacement_text: str,
    max_context_lines: int = 5
) -> str:
    """Replace specific text content with intelligent context matching.

    Args:
        bucket: Bucket name
        filename: File name
        search_text: Text to find and replace
        replacement_text: New text to insert
        max_context_lines: Lines of context to show in diff

    Returns:
        Diff showing what was changed
    """

def insert_at_line(
    self,
    bucket: str,
    filename: str,
    line_number: int,
    text: str,
    position: str = "after"  # "before", "after", "replace"
) -> str:
    """Insert text at a specific line number.

    Args:
        bucket: Bucket name
        filename: File name
        line_number: Target line (1-based)
        text: Text to insert
        position: Where to insert relative to line

    Returns:
        Success message with line context
    """

def replace_section(
    self,
    bucket: str,
    filename: str,
    start_marker: str,
    end_marker: str,
    new_content: str
) -> str:
    """Replace content between markers.

    Args:
        bucket: Bucket name
        filename: File name
        start_marker: Text marking section start
        end_marker: Text marking section end
        new_content: Replacement content

    Returns:
        Diff showing section replacement
    """

def smart_append(
    self,
    bucket: str,
    filename: str,
    content: str,
    section_hint: Optional[str] = None,
    avoid_duplicates: bool = True
) -> str:
    """Intelligently append content, avoiding duplicates and finding best location.

    Args:
        bucket: Bucket name
        filename: File name
        content: Content to append
        section_hint: Hint about where to append (e.g., "shopping list", "tasks")
        avoid_duplicates: Check for similar content before appending

    Returns:
        Where content was added and why
    """

def find_and_modify(
    self,
    bucket: str,
    filename: str,
    search_pattern: str,
    modification_type: str,
    new_content: str
) -> str:
    """Find content by pattern and modify it.

    Args:
        bucket: Bucket name
        filename: File name
        search_pattern: Regex or text pattern to find
        modification_type: "replace", "insert_before", "insert_after", "delete"
        new_content: Content for replacement/insertion

    Returns:
        Diff showing changes made
    """

def get_file_preview(
    self,
    bucket: str,
    filename: str,
    around_line: Optional[int] = None,
    around_text: Optional[str] = None,
    context_lines: int = 10
) -> str:
    """Get a preview of file content around specific location.

    Args:
        bucket: Bucket name
        filename: File name
        around_line: Show context around this line number
        around_text: Show context around this text
        context_lines: Lines of context to show

    Returns:
        File preview with line numbers
    """
```

#### 2. Add Utility Functions to `/app/utils.py`

```python
import difflib
from typing import List, Tuple, Optional

def generate_diff(
    original_lines: List[str],
    modified_lines: List[str],
    filename: str = "file"
) -> str:
    """Generate a unified diff showing changes.

    Args:
        original_lines: Original file lines
        modified_lines: Modified file lines
        filename: File name for diff header

    Returns:
        Unified diff string
    """
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"{filename} (original)",
        tofile=f"{filename} (modified)",
        lineterm=""
    )
    return "\n".join(diff)

def find_similar_lines(
    content: str,
    target_text: str,
    similarity_threshold: float = 0.6
) -> List[Tuple[int, str, float]]:
    """Find lines similar to target text.

    Args:
        content: File content
        target_text: Text to find similar content for
        similarity_threshold: Minimum similarity score

    Returns:
        List of (line_number, line_text, similarity_score)
    """
    from difflib import SequenceMatcher

    lines = content.split('\n')
    similar_lines = []

    for i, line in enumerate(lines, 1):
        similarity = SequenceMatcher(None, target_text.lower(), line.lower()).ratio()
        if similarity >= similarity_threshold:
            similar_lines.append((i, line, similarity))

    return sorted(similar_lines, key=lambda x: x[2], reverse=True)

def extract_section_by_keywords(
    content: str,
    keywords: List[str],
    context_lines: int = 3
) -> Optional[Tuple[int, int, List[str]]]:
    """Extract a section from content based on keywords.

    Args:
        content: File content
        keywords: Keywords to identify the section
        context_lines: Lines of context around matches

    Returns:
        (start_line, end_line, section_lines) or None if not found
    """
    lines = content.split('\n')

    # Find lines containing keywords
    matching_lines = []
    for i, line in enumerate(lines):
        if any(keyword.lower() in line.lower() for keyword in keywords):
            matching_lines.append(i)

    if not matching_lines:
        return None

    # Determine section boundaries
    start_line = max(0, min(matching_lines) - context_lines)
    end_line = min(len(lines), max(matching_lines) + context_lines + 1)

    return start_line, end_line, lines[start_line:end_line]

def smart_content_placement(
    existing_content: str,
    new_content: str,
    content_type_hint: Optional[str] = None
) -> Tuple[int, str]:
    """Determine the best place to insert new content.

    Args:
        existing_content: Current file content
        new_content: Content to insert
        content_type_hint: Hint about content type ("list", "task", etc.)

    Returns:
        (line_number, reason) where to insert
    """
    lines = existing_content.split('\n')

    # Strategies for placement
    strategies = {
        "list": _find_list_insertion_point,
        "task": _find_task_insertion_point,
        "note": _find_note_insertion_point,
        "default": _find_default_insertion_point
    }

    strategy = strategies.get(content_type_hint, strategies["default"])
    return strategy(lines, new_content)

def _find_list_insertion_point(lines: List[str], new_content: str) -> Tuple[int, str]:
    """Find best place to insert list items."""
    # Look for existing list patterns
    list_patterns = [r'^\s*[-\*\+]\s', r'^\s*\d+\.\s', r'^\s*•\s']

    for i, line in enumerate(lines):
        for pattern in list_patterns:
            import re
            if re.match(pattern, line):
                # Find end of this list
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == "" or not re.match(pattern, lines[j]):
                        return j, f"Added to existing list after line {i + 1}"
                return len(lines), "Added to end of list"

    return len(lines), "Added as new list at end of file"

def _find_task_insertion_point(lines: List[str], new_content: str) -> Tuple[int, str]:
    """Find best place to insert task items."""
    # Look for task patterns like "TODO:", "- [ ]", etc.
    task_keywords = ["todo", "task", "- [ ]", "- [x]"]

    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in task_keywords):
            return i + 1, f"Added after task section at line {i + 1}"

    return len(lines), "Added as new task section"

def _find_note_insertion_point(lines: List[str], new_content: str) -> Tuple[int, str]:
    """Find best place to insert general notes."""
    # Look for empty lines or section breaks
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "":
            return i + 1, f"Added after empty line {i + 1}"

    return len(lines), "Added to end of file"

def _find_default_insertion_point(lines: List[str], new_content: str) -> Tuple[int, str]:
    """Default insertion strategy."""
    return len(lines), "Added to end of file"
```

#### 3. Update `/app/agents.py` - Register New Tools

Add the new tools to the `_register_tools()` method:

```python
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
```

#### 4. Update Agent System Prompt in `/app/agents.py`

Enhance the system prompt to emphasize intelligent editing:

```python
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
```

### Usage Examples

Once implemented, users can interact naturally:

```
User: "Add 'buy milk' to my shopping list"
Agent: Uses smart_append() with section_hint="shopping" to find the shopping section and add the item appropriately.

User: "Change the third item in my todo list to 'Call dentist'"
Agent: Uses preview_file_section() to see the todo list, then insert_at_line() with position="replace" to update line 3.

User: "Replace the 'Meeting Notes' section with the new notes I'm about to give you"
Agent: Uses replace_section() with start_marker="Meeting Notes" to replace just that section.

User: "Fix the typo 'teh' to 'the' in my notes"
Agent: Uses edit_file_lines() to find and replace the specific typo without affecting other content.
```

### Testing Steps

1. **Test intelligent replacement**:
   ```python
   # Create a test file with content
   tools.write_file("test", "notes.txt", "Shopping:\n- bread\n- milk\n\nTasks:\n- call mom")

   # Test smart editing
   result = tools.edit_file_lines("test", "notes.txt", "- milk", "- organic milk")
   # Should show diff of just that line change
   ```

2. **Test line insertion**:
   ```python
   result = tools.insert_at_line("test", "notes.txt", 3, "- eggs", "after")
   # Should insert eggs after the milk line
   ```

3. **Test section replacement**:
   ```python
   result = tools.replace_section("test", "notes.txt", "Tasks:", "EOF", "Tasks:\n- call mom\n- buy groceries")
   # Should replace just the tasks section
   ```

4. **Test smart append**:
   ```python
   result = tools.smart_append("test", "notes.txt", "- butter", section_hint="shopping")
   # Should add butter to the shopping list, not tasks
   ```

### Verification Checklist
- [ ] All editing tools work with existing files
- [ ] Diffs are generated and displayed clearly
- [ ] Token usage is minimized (no full file sends)
- [ ] Tools integrate seamlessly with PydanticAI agent
- [ ] Error handling provides helpful feedback
- [ ] Tools remain synchronous (not async)
- [ ] Preview functionality helps with context
- [ ] Smart append finds appropriate insertion points

### Related Files
- `/app/tools.py` - Core intelligent editing tools
- `/app/utils.py` - Diff generation and content analysis utilities
- `/app/agents.py` - Tool registration and enhanced system prompt

### Next Steps
After completion, proceed to TICKET-007 for markdown rendering in the chat interface.