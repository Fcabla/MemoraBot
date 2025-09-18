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