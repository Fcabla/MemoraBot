"""Utility functions for the application."""

import re
import hashlib
import difflib
from pathlib import Path
from typing import Optional, List, Tuple
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


def is_allowed_file_type(filename: str, settings=None) -> bool:
    """Check if file type is allowed based on extension.

    Args:
        filename: File name to check
        settings: Application settings (optional)

    Returns:
        True if file type is allowed
    """
    if settings is None:
        from app.config import settings

    extension = Path(filename).suffix.lower()
    allowed = settings.ALLOWED_FILE_TYPES.split(',')
    return extension in allowed or not extension  # Allow no extension files


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