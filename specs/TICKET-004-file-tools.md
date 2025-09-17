# TICKET-004: File Manipulation Tools

**Status:** TODO
**Phase:** 1 - Foundation & Core Infrastructure
**Priority:** High
**Estimated Effort:** 1 day
**Dependencies:** TICKET-003

## Detail Section

### Purpose
Implement the core file manipulation tools that MemoraBot will use to manage user files and notes. These tools provide the actual CRUD operations on the file system, with proper error handling, validation, and safety measures.

### Business Value
- Enables the core functionality of file and note management
- Provides safe, reliable file operations
- Ensures data integrity and prevents data loss
- Creates organized bucket-based storage system

### Acceptance Criteria
- [ ] All CRUD operations work correctly
- [ ] File operations are safe (no path traversal)
- [ ] Proper error handling for all edge cases
- [ ] File search functionality works
- [ ] Bucket organization is maintained
- [ ] File size and type validation works

## Implementation Section

### Files to Create/Modify

#### 1. `/app/tools.py`
```python
"""File manipulation tools for MemoraBot."""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.config import settings
from app.utils import (
    sanitize_filename,
    sanitize_bucket_name,
    format_file_size,
    is_allowed_file_type
)

logger = logging.getLogger("memorabot.tools")


class FileTools:
    """File manipulation tools for bucket-based storage."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize file tools with base directory.

        Args:
            base_dir: Base directory for file storage
        """
        self.base_dir = base_dir or Path(settings.DATA_DIR)
        self.base_dir = self.base_dir.resolve()

        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, bucket: str, filename: str) -> Path:
        """Validate and construct safe file path.

        Args:
            bucket: Bucket name
            filename: File name

        Returns:
            Safe file path

        Raises:
            ValueError: If path is invalid or unsafe
        """
        # Sanitize inputs
        bucket = sanitize_bucket_name(bucket)
        filename = sanitize_filename(filename)

        # Construct path
        file_path = self.base_dir / bucket / filename
        resolved_path = file_path.resolve()

        # Ensure path is within base directory (prevent path traversal)
        if not str(resolved_path).startswith(str(self.base_dir)):
            raise ValueError(f"Invalid path: {file_path}")

        # Check file type
        if not is_allowed_file_type(filename):
            raise ValueError(
                f"File type not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}"
            )

        return resolved_path

    async def read_file(self, bucket: str, filename: str) -> str:
        """Read contents of a file.

        Args:
            bucket: Bucket name
            filename: File name

        Returns:
            File contents

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If path is invalid
        """
        try:
            file_path = self._validate_path(bucket, filename)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {bucket}/{filename}")

            # Read file asynchronously
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                file_path.read_text,
                'utf-8'
            )

            logger.info(f"Read file: {bucket}/{filename} ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"Error reading file {bucket}/{filename}: {e}")
            raise

    async def write_file(
        self,
        bucket: str,
        filename: str,
        content: str,
        overwrite: bool = False
    ) -> str:
        """Write content to a file.

        Args:
            bucket: Bucket name
            filename: File name
            content: Content to write
            overwrite: Whether to overwrite existing file

        Returns:
            Success message

        Raises:
            FileExistsError: If file exists and overwrite=False
            ValueError: If content exceeds size limit
        """
        try:
            # Check content size
            content_size = len(content.encode('utf-8'))
            if content_size > settings.max_file_size_bytes:
                raise ValueError(
                    f"Content size ({format_file_size(content_size)}) exceeds "
                    f"limit ({settings.MAX_FILE_SIZE_MB}MB)"
                )

            file_path = self._validate_path(bucket, filename)

            # Check if file exists
            if file_path.exists() and not overwrite:
                raise FileExistsError(
                    f"File already exists: {bucket}/{filename}. "
                    "Use append_file to add content or set overwrite=True"
                )

            # Create bucket directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                file_path.write_text,
                content,
                'utf-8'
            )

            # Log operation
            action = "Overwrote" if file_path.exists() else "Created"
            logger.info(
                f"{action} file: {bucket}/{filename} "
                f"({format_file_size(content_size)})"
            )

            return f"Successfully wrote {format_file_size(content_size)} to {bucket}/{filename}"

        except Exception as e:
            logger.error(f"Error writing file {bucket}/{filename}: {e}")
            raise

    async def append_file(
        self,
        bucket: str,
        filename: str,
        content: str,
        separator: str = "\n\n"
    ) -> str:
        """Append content to an existing file.

        Args:
            bucket: Bucket name
            filename: File name
            content: Content to append
            separator: Separator between existing and new content

        Returns:
            Success message

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            file_path = self._validate_path(bucket, filename)

            if not file_path.exists():
                raise FileNotFoundError(
                    f"File not found: {bucket}/{filename}. "
                    "Use write_file to create a new file"
                )

            # Read existing content
            existing_content = await self.read_file(bucket, filename)

            # Check combined size
            new_content = existing_content + separator + content
            new_size = len(new_content.encode('utf-8'))

            if new_size > settings.max_file_size_bytes:
                raise ValueError(
                    f"Combined content size ({format_file_size(new_size)}) "
                    f"exceeds limit ({settings.MAX_FILE_SIZE_MB}MB)"
                )

            # Write combined content
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                file_path.write_text,
                new_content,
                'utf-8'
            )

            appended_size = len(content.encode('utf-8'))
            logger.info(
                f"Appended to file: {bucket}/{filename} "
                f"({format_file_size(appended_size)} added)"
            )

            return f"Successfully appended {format_file_size(appended_size)} to {bucket}/{filename}"

        except Exception as e:
            logger.error(f"Error appending to file {bucket}/{filename}: {e}")
            raise

    async def delete_file(self, bucket: str, filename: str) -> str:
        """Delete a file.

        Args:
            bucket: Bucket name
            filename: File name

        Returns:
            Success message

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            file_path = self._validate_path(bucket, filename)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {bucket}/{filename}")

            # Delete file asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, file_path.unlink)

            # Remove empty bucket directory
            bucket_dir = file_path.parent
            if bucket_dir.exists() and not list(bucket_dir.iterdir()):
                bucket_dir.rmdir()
                logger.info(f"Removed empty bucket: {bucket}")

            logger.info(f"Deleted file: {bucket}/{filename}")
            return f"Successfully deleted {bucket}/{filename}"

        except Exception as e:
            logger.error(f"Error deleting file {bucket}/{filename}: {e}")
            raise

    async def list_files(
        self,
        bucket: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List files in bucket(s).

        Args:
            bucket: Optional bucket name. If None, lists all files.

        Returns:
            List of file information dictionaries
        """
        try:
            files = []

            if bucket:
                # List files in specific bucket
                bucket = sanitize_bucket_name(bucket)
                bucket_path = self.base_dir / bucket

                if bucket_path.exists() and bucket_path.is_dir():
                    for file_path in bucket_path.iterdir():
                        if file_path.is_file():
                            stat = file_path.stat()
                            files.append({
                                'bucket': bucket,
                                'filename': file_path.name,
                                'path': f"{bucket}/{file_path.name}",
                                'size': stat.st_size,
                                'size_formatted': format_file_size(stat.st_size),
                                'modified': datetime.fromtimestamp(
                                    stat.st_mtime
                                ).isoformat(),
                                'created': datetime.fromtimestamp(
                                    stat.st_ctime
                                ).isoformat()
                            })
            else:
                # List all files in all buckets
                for bucket_path in self.base_dir.iterdir():
                    if bucket_path.is_dir():
                        bucket_name = bucket_path.name
                        for file_path in bucket_path.iterdir():
                            if file_path.is_file():
                                stat = file_path.stat()
                                files.append({
                                    'bucket': bucket_name,
                                    'filename': file_path.name,
                                    'path': f"{bucket_name}/{file_path.name}",
                                    'size': stat.st_size,
                                    'size_formatted': format_file_size(stat.st_size),
                                    'modified': datetime.fromtimestamp(
                                        stat.st_mtime
                                    ).isoformat(),
                                    'created': datetime.fromtimestamp(
                                        stat.st_ctime
                                    ).isoformat()
                                })

            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)

            logger.info(
                f"Listed {len(files)} files in "
                f"{bucket or 'all buckets'}"
            )
            return files

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise

    async def search_files(
        self,
        query: str,
        bucket: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for files containing specific text.

        Args:
            query: Search query
            bucket: Optional bucket to search in
            max_results: Maximum number of results

        Returns:
            List of matching files with excerpts
        """
        try:
            results = []
            query_lower = query.lower()

            # Get list of files to search
            files = await self.list_files(bucket)

            for file_info in files:
                if len(results) >= max_results:
                    break

                try:
                    # Read file content
                    content = await self.read_file(
                        file_info['bucket'],
                        file_info['filename']
                    )

                    # Search in content and filename
                    content_lower = content.lower()
                    filename_lower = file_info['filename'].lower()

                    if query_lower in content_lower or query_lower in filename_lower:
                        # Find excerpt around match
                        excerpt = ""
                        if query_lower in content_lower:
                            index = content_lower.index(query_lower)
                            start = max(0, index - 50)
                            end = min(len(content), index + len(query) + 50)
                            excerpt = content[start:end]
                            if start > 0:
                                excerpt = "..." + excerpt
                            if end < len(content):
                                excerpt = excerpt + "..."

                        results.append({
                            **file_info,
                            'excerpt': excerpt,
                            'match_in_filename': query_lower in filename_lower,
                            'match_in_content': query_lower in content_lower
                        })

                except Exception as e:
                    logger.warning(
                        f"Error searching file {file_info['path']}: {e}"
                    )
                    continue

            logger.info(
                f"Found {len(results)} matches for '{query}' in "
                f"{bucket or 'all buckets'}"
            )
            return results

        except Exception as e:
            logger.error(f"Error searching files: {e}")
            raise

    async def get_bucket_stats(self) -> Dict[str, Any]:
        """Get statistics about buckets and files.

        Returns:
            Dictionary with storage statistics
        """
        try:
            stats = {
                'total_buckets': 0,
                'total_files': 0,
                'total_size': 0,
                'buckets': {}
            }

            for bucket_path in self.base_dir.iterdir():
                if bucket_path.is_dir():
                    bucket_name = bucket_path.name
                    bucket_files = 0
                    bucket_size = 0

                    for file_path in bucket_path.iterdir():
                        if file_path.is_file():
                            bucket_files += 1
                            bucket_size += file_path.stat().st_size

                    stats['buckets'][bucket_name] = {
                        'files': bucket_files,
                        'size': bucket_size,
                        'size_formatted': format_file_size(bucket_size)
                    }

                    stats['total_buckets'] += 1
                    stats['total_files'] += bucket_files
                    stats['total_size'] += bucket_size

            stats['total_size_formatted'] = format_file_size(stats['total_size'])

            logger.info(f"Retrieved bucket statistics: {stats['total_files']} files in {stats['total_buckets']} buckets")
            return stats

        except Exception as e:
            logger.error(f"Error getting bucket stats: {e}")
            raise


# Global instance for easy access
file_tools = FileTools()
```

#### 2. Create test file `/tests/test_tools.py`
```python
"""Tests for file manipulation tools."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from app.tools import FileTools


@pytest.fixture
async def file_tools():
    """Create FileTools instance with temporary directory."""
    temp_dir = tempfile.mkdtemp()
    tools = FileTools(Path(temp_dir))
    yield tools
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_write_and_read_file(file_tools):
    """Test writing and reading a file."""
    bucket = "test_bucket"
    filename = "test.txt"
    content = "This is test content"

    # Write file
    result = await file_tools.write_file(bucket, filename, content)
    assert "Successfully wrote" in result

    # Read file
    read_content = await file_tools.read_file(bucket, filename)
    assert read_content == content


@pytest.mark.asyncio
async def test_append_file(file_tools):
    """Test appending to a file."""
    bucket = "test_bucket"
    filename = "test.txt"
    initial_content = "Initial content"
    append_content = "Appended content"

    # Write initial file
    await file_tools.write_file(bucket, filename, initial_content)

    # Append content
    result = await file_tools.append_file(bucket, filename, append_content)
    assert "Successfully appended" in result

    # Verify combined content
    content = await file_tools.read_file(bucket, filename)
    assert initial_content in content
    assert append_content in content


@pytest.mark.asyncio
async def test_delete_file(file_tools):
    """Test deleting a file."""
    bucket = "test_bucket"
    filename = "test.txt"
    content = "Content to delete"

    # Write file
    await file_tools.write_file(bucket, filename, content)

    # Delete file
    result = await file_tools.delete_file(bucket, filename)
    assert "Successfully deleted" in result

    # Verify file is gone
    with pytest.raises(FileNotFoundError):
        await file_tools.read_file(bucket, filename)


@pytest.mark.asyncio
async def test_list_files(file_tools):
    """Test listing files."""
    # Create multiple files
    await file_tools.write_file("bucket1", "file1.txt", "Content 1")
    await file_tools.write_file("bucket1", "file2.txt", "Content 2")
    await file_tools.write_file("bucket2", "file3.txt", "Content 3")

    # List all files
    all_files = await file_tools.list_files()
    assert len(all_files) == 3

    # List files in specific bucket
    bucket1_files = await file_tools.list_files("bucket1")
    assert len(bucket1_files) == 2


@pytest.mark.asyncio
async def test_search_files(file_tools):
    """Test searching files."""
    # Create files with searchable content
    await file_tools.write_file("notes", "meeting.txt", "Discuss project timeline")
    await file_tools.write_file("notes", "todo.txt", "Complete project proposal")
    await file_tools.write_file("docs", "readme.txt", "Installation instructions")

    # Search for "project"
    results = await file_tools.search_files("project")
    assert len(results) == 2

    # Verify search results
    for result in results:
        assert "project" in result['excerpt'].lower() or "project" in result['filename'].lower()


@pytest.mark.asyncio
async def test_path_traversal_protection(file_tools):
    """Test that path traversal attacks are prevented."""
    with pytest.raises(ValueError):
        await file_tools.write_file("../", "hack.txt", "Bad content")

    with pytest.raises(ValueError):
        await file_tools.read_file("..", "../../etc/passwd")


@pytest.mark.asyncio
async def test_file_type_validation(file_tools):
    """Test that only allowed file types are accepted."""
    # Allowed type should work
    await file_tools.write_file("test", "file.txt", "Content")
    await file_tools.write_file("test", "file.md", "Content")

    # Disallowed type should fail
    with pytest.raises(ValueError, match="File type not allowed"):
        await file_tools.write_file("test", "file.exe", "Content")
```

### Testing Steps

1. **Run unit tests**
   ```bash
   pytest tests/test_tools.py -v
   ```

2. **Test via Python console**
   ```python
   import asyncio
   from app.tools import file_tools

   async def test():
       # Write a file
       await file_tools.write_file("notes", "test.txt", "Hello, MemoraBot!")

       # Read it back
       content = await file_tools.read_file("notes", "test.txt")
       print(content)

       # List files
       files = await file_tools.list_files()
       print(files)

   asyncio.run(test())
   ```

3. **Test through the agent**
   - Start the application
   - Send messages to create, read, and manage files
   - Verify operations work correctly

### Verification Checklist
- [ ] All CRUD operations work
- [ ] Path traversal attacks are blocked
- [ ] File type validation works
- [ ] File size limits are enforced
- [ ] Search functionality returns correct results
- [ ] Bucket organization is maintained
- [ ] Empty buckets are cleaned up
- [ ] Async operations work correctly

### Related Files
- `/app/tools.py` - File manipulation tools
- `/app/utils.py` - Utility functions
- `/tests/test_tools.py` - Tool tests
- `/app/agents.py` - Uses these tools

### Next Steps
After completion, proceed to Phase 2 tickets for chat interface implementation.