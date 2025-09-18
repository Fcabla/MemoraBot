"""File manipulation tools for MemoraBot."""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from app.config import settings

logger = logging.getLogger("memorabot.tools")


class FileTools:
    """File manipulation tools for managing buckets and files."""

    def __init__(self, data_dir: str = None):
        """Initialize FileTools with data directory."""
        self.data_dir = Path(data_dir or settings.DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_bucket_path(self, bucket: str) -> Path:
        """Get the path for a bucket (directory)."""
        # Sanitize bucket name
        from app.utils import sanitize_bucket_name
        safe_bucket = sanitize_bucket_name(bucket)
        bucket_path = self.data_dir / safe_bucket
        bucket_path.mkdir(parents=True, exist_ok=True)
        return bucket_path

    def _get_file_path(self, bucket: str, filename: str) -> Path:
        """Get the full path for a file in a bucket."""
        from app.utils import sanitize_filename
        safe_filename = sanitize_filename(filename)
        bucket_path = self._get_bucket_path(bucket)
        return bucket_path / safe_filename

    def read_file(self, bucket: str, filename: str) -> str:
        """Read contents of a file from a bucket.

        Args:
            bucket: The bucket (folder) name
            filename: The file name to read

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = self._get_file_path(bucket, filename)

        if not file_path.exists():
            raise FileNotFoundError(f"File {bucket}/{filename} not found")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info(f"Read file: {bucket}/{filename} ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"Error reading file {bucket}/{filename}: {e}")
            raise

    def write_file(self, bucket: str, filename: str, content: str, overwrite: bool = False) -> str:
        """Write content to a new file in a bucket.

        Args:
            bucket: The bucket (folder) name
            filename: The file name to create
            content: Content to write to the file
            overwrite: If True, overwrite existing file

        Returns:
            Confirmation message

        Raises:
            ValueError: If file already exists and overwrite is False
            ValueError: If file size exceeds limit
            ValueError: If file type is not allowed
        """
        # Check file type
        from app.utils import is_allowed_file_type
        if not is_allowed_file_type(filename, settings):
            raise ValueError(f"File type not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}")

        # Check file size
        content_bytes = content.encode('utf-8')
        if len(content_bytes) > settings.max_file_size_bytes:
            from app.utils import format_file_size
            raise ValueError(
                f"File size ({format_file_size(len(content_bytes))}) exceeds limit "
                f"({format_file_size(settings.max_file_size_bytes)})"
            )

        file_path = self._get_file_path(bucket, filename)

        if file_path.exists() and not overwrite:
            raise ValueError(f"File {bucket}/{filename} already exists. Use overwrite=True or append_file.")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            action = "Overwrote" if file_path.exists() and overwrite else "Created"
            logger.info(f"{action} file: {bucket}/{filename} ({len(content)} chars)")
            return f"Successfully {action.lower()} {bucket}/{filename} with {len(content)} characters"

        except Exception as e:
            logger.error(f"Error writing file {bucket}/{filename}: {e}")
            raise

    def append_file(self, bucket: str, filename: str, content: str, separator: str = "\n\n") -> str:
        """Append content to an existing file.

        Args:
            bucket: The bucket (folder) name
            filename: The file name to append to
            content: Content to append
            separator: Separator to use when appending (default: "\n\n")

        Returns:
            Confirmation message

        Raises:
            ValueError: If resulting file size would exceed limit
            ValueError: If file type is not allowed
        """
        # Check file type
        from app.utils import is_allowed_file_type
        if not is_allowed_file_type(filename, settings):
            raise ValueError(f"File type not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}")

        file_path = self._get_file_path(bucket, filename)

        # Check size limit
        new_content_bytes = content.encode('utf-8')
        existing_size = file_path.stat().st_size if file_path.exists() else 0
        separator_bytes = separator.encode('utf-8') if file_path.exists() else b''
        total_size = existing_size + len(separator_bytes) + len(new_content_bytes)

        if total_size > settings.max_file_size_bytes:
            from app.utils import format_file_size
            raise ValueError(
                f"Resulting file size ({format_file_size(total_size)}) would exceed limit "
                f"({format_file_size(settings.max_file_size_bytes)})"
            )

        try:
            # Create file if it doesn't exist
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Created new file: {bucket}/{filename}")
                return f"Created new file {bucket}/{filename} with {len(content)} characters"
            else:
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(separator + content)
                logger.info(f"Appended to file: {bucket}/{filename}")
                return f"Appended {len(content)} characters to {bucket}/{filename}"

        except Exception as e:
            logger.error(f"Error appending to file {bucket}/{filename}: {e}")
            raise

    def delete_file(self, bucket: str, filename: str) -> str:
        """Delete a file from a bucket.

        Args:
            bucket: The bucket (folder) name
            filename: The file name to delete

        Returns:
            Confirmation message

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = self._get_file_path(bucket, filename)

        if not file_path.exists():
            raise FileNotFoundError(f"File {bucket}/{filename} not found")

        try:
            file_path.unlink()
            logger.info(f"Deleted file: {bucket}/{filename}")

            # Clean up empty bucket directory
            bucket_path = self._get_bucket_path(bucket)
            if bucket_path.exists() and not any(bucket_path.iterdir()):
                bucket_path.rmdir()
                logger.info(f"Removed empty bucket: {bucket}")
                return f"Successfully deleted {bucket}/{filename} and removed empty bucket"

            return f"Successfully deleted {bucket}/{filename}"

        except Exception as e:
            logger.error(f"Error deleting file {bucket}/{filename}: {e}")
            raise

    def list_files(self, bucket: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files in a bucket or all buckets with detailed metadata.

        Args:
            bucket: Optional bucket name. If None, lists all buckets.

        Returns:
            List of dictionaries with file metadata
        """
        from app.utils import format_file_size
        from datetime import datetime

        try:
            files_list = []

            if bucket:
                # List files in specific bucket
                bucket_path = self._get_bucket_path(bucket)
                if not bucket_path.exists():
                    return []

                for file_path in bucket_path.iterdir():
                    if file_path.is_file():
                        stat = file_path.stat()
                        files_list.append({
                            "bucket": bucket,
                            "filename": file_path.name,
                            "path": f"{bucket}/{file_path.name}",
                            "size": stat.st_size,
                            "size_formatted": format_file_size(stat.st_size),
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                        })

                logger.info(f"Listed {len(files_list)} files in bucket: {bucket}")
            else:
                # List all files in all buckets
                for bucket_path in self.data_dir.iterdir():
                    if bucket_path.is_dir():
                        bucket_name = bucket_path.name
                        for file_path in bucket_path.iterdir():
                            if file_path.is_file():
                                stat = file_path.stat()
                                files_list.append({
                                    "bucket": bucket_name,
                                    "filename": file_path.name,
                                    "path": f"{bucket_name}/{file_path.name}",
                                    "size": stat.st_size,
                                    "size_formatted": format_file_size(stat.st_size),
                                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                                })

                logger.info(f"Listed {len(files_list)} files across all buckets")

            # Sort by path for consistency
            return sorted(files_list, key=lambda x: x['path'])

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise

    def search_files(self, query: str, bucket: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for files containing specific content.

        Args:
            query: Search query string
            bucket: Optional bucket to search in

        Returns:
            List of matching files with excerpts
        """
        results = []

        try:
            # Get list of files to search
            files_to_search = self.list_files(bucket)

            for file_info in files_to_search:
                # Extract path from file metadata dict
                if isinstance(file_info, dict):
                    file_path = file_info.get('path', '')
                    bucket_name = file_info.get('bucket', '')
                    filename = file_info.get('filename', '')
                else:
                    # Fallback for string paths
                    file_path = str(file_info)
                    if '/' in file_path:
                        bucket_name, filename = file_path.split('/', 1)
                    else:
                        continue  # Skip malformed paths

                try:
                    content = self.read_file(bucket_name, filename)

                    # Simple text search (case-insensitive)
                    if query.lower() in content.lower():
                        # Find excerpt around match
                        content_lower = content.lower()
                        query_lower = query.lower()
                        match_index = content_lower.find(query_lower)

                        # Get context around match (50 chars before/after)
                        start = max(0, match_index - 50)
                        end = min(len(content), match_index + len(query) + 50)
                        excerpt = content[start:end].strip()

                        if start > 0:
                            excerpt = "..." + excerpt
                        if end < len(content):
                            excerpt = excerpt + "..."

                        results.append({
                            "file": file_path,
                            "bucket": bucket_name,
                            "filename": filename,
                            "excerpt": excerpt,
                            "size": len(content)
                        })

                except Exception as e:
                    # Skip files that can't be read
                    logger.warning(f"Couldn't search in {file_path}: {e}")
                    continue

            logger.info(f"Found {len(results)} files matching query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error searching files: {e}")
            raise

    def get_file_stats(self, bucket: str, filename: str) -> Dict[str, Any]:
        """Get statistics about a file.

        Args:
            bucket: The bucket name
            filename: The file name

        Returns:
            Dictionary with file statistics
        """
        file_path = self._get_file_path(bucket, filename)

        if not file_path.exists():
            raise FileNotFoundError(f"File {bucket}/{filename} not found")

        try:
            stat = file_path.stat()

            # Count lines and words
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = len(content.splitlines())
            words = len(content.split())
            chars = len(content)

            return {
                "file": f"{bucket}/{filename}",
                "size_bytes": stat.st_size,
                "lines": lines,
                "words": words,
                "characters": chars,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
            }

        except Exception as e:
            logger.error(f"Error getting stats for {bucket}/{filename}: {e}")
            raise

    def get_bucket_stats(self) -> Dict[str, Any]:
        """Get statistics about buckets and files.

        Returns:
            Dictionary with total_buckets, total_files, total_size, and buckets info
        """
        from app.utils import format_file_size
        from datetime import datetime

        try:
            total_buckets = 0
            total_files = 0
            total_size = 0
            buckets_info = []

            for bucket_path in self.data_dir.iterdir():
                if bucket_path.is_dir():
                    total_buckets += 1
                    bucket_files = 0
                    bucket_size = 0

                    for file_path in bucket_path.iterdir():
                        if file_path.is_file():
                            total_files += 1
                            bucket_files += 1
                            file_size = file_path.stat().st_size
                            total_size += file_size
                            bucket_size += file_size

                    buckets_info.append({
                        "name": bucket_path.name,
                        "files_count": bucket_files,
                        "total_size": bucket_size,
                        "size_formatted": format_file_size(bucket_size)
                    })

            # Sort buckets by file count
            buckets_info.sort(key=lambda x: x['files_count'], reverse=True)

            return {
                "total_buckets": total_buckets,
                "total_files": total_files,
                "total_size": total_size,
                "total_size_formatted": format_file_size(total_size),
                "buckets": buckets_info
            }

        except Exception as e:
            logger.error(f"Error getting bucket stats: {e}")
            raise

    def list_directory(self, path: str = "") -> Dict[str, Any]:
        """List directory contents with buckets and files for navigation.

        Args:
            path: Optional path within data directory (e.g., "bucket_name")

        Returns:
            Dict with:
            - current_path: Current directory path
            - buckets: List of subdirectories/buckets
            - files: List of files with metadata
            - parent_path: Parent directory (if applicable)
        """
        from app.utils import format_file_size, sanitize_bucket_name
        from datetime import datetime

        try:
            # Parse and sanitize the path
            if path:
                safe_path = sanitize_bucket_name(path)
                current_dir = self.data_dir / safe_path
            else:
                current_dir = self.data_dir

            # Ensure the directory exists
            if not current_dir.exists():
                # Return empty structure for non-existent path
                return {
                    "current_path": path,
                    "buckets": [],
                    "files": [],
                    "parent_path": "" if path else None
                }

            result = {
                "current_path": path,
                "buckets": [],
                "files": [],
                "parent_path": None
            }

            # Set parent path if not at root
            if path:
                result["parent_path"] = ""

            # List buckets (subdirectories) and files
            for item in current_dir.iterdir():
                if item.is_dir():
                    # Count files in bucket
                    file_count = sum(1 for f in item.iterdir() if f.is_file())
                    result["buckets"].append({
                        "name": item.name,
                        "path": item.name if not path else f"{path}/{item.name}",
                        "files_count": file_count
                    })
                elif item.is_file():
                    stat = item.stat()
                    result["files"].append({
                        "filename": item.name,
                        "path": item.name if not path else f"{path}/{item.name}",
                        "size": stat.st_size,
                        "size_formatted": format_file_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })

            # Sort for consistency
            result["buckets"].sort(key=lambda x: x["name"])
            result["files"].sort(key=lambda x: x["filename"])

            logger.info(f"Listed directory: {path or 'root'} - {len(result['buckets'])} buckets, {len(result['files'])} files")
            return result

        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            raise

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
        file_path = self._get_file_path(bucket, filename)

        if not file_path.exists():
            raise FileNotFoundError(f"File {bucket}/{filename} not found")

        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_lines = content.split('\n')

            # Find and replace the text
            modified_content = content.replace(search_text, replacement_text)

            if modified_content == content:
                return f"No matches found for '{search_text}' in {bucket}/{filename}"

            modified_lines = modified_content.split('\n')

            # Check file size
            content_bytes = modified_content.encode('utf-8')
            if len(content_bytes) > settings.max_file_size_bytes:
                from app.utils import format_file_size
                raise ValueError(
                    f"Modified file size ({format_file_size(len(content_bytes))}) would exceed limit "
                    f"({format_file_size(settings.max_file_size_bytes)})"
                )

            # Write the modified content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            # Generate diff
            from app.utils import generate_diff
            diff_output = generate_diff(original_lines, modified_lines, f"{bucket}/{filename}")

            logger.info(f"Edited lines in: {bucket}/{filename}")
            return f"Successfully replaced text in {bucket}/{filename}:\n\n{diff_output}"

        except Exception as e:
            logger.error(f"Error editing lines in {bucket}/{filename}: {e}")
            raise

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
        file_path = self._get_file_path(bucket, filename)

        if not file_path.exists():
            raise FileNotFoundError(f"File {bucket}/{filename} not found")

        if position not in ["before", "after", "replace"]:
            raise ValueError("Position must be 'before', 'after', or 'replace'")

        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Convert to 0-based index
            target_index = line_number - 1

            if target_index < 0 or target_index >= len(lines):
                raise ValueError(f"Line number {line_number} is out of range (file has {len(lines)} lines)")

            original_lines = [line.rstrip('\n') for line in lines]

            # Modify the lines
            if position == "before":
                lines.insert(target_index, text + '\n')
            elif position == "after":
                lines.insert(target_index + 1, text + '\n')
            elif position == "replace":
                lines[target_index] = text + '\n'

            modified_content = ''.join(lines)

            # Check file size
            content_bytes = modified_content.encode('utf-8')
            if len(content_bytes) > settings.max_file_size_bytes:
                from app.utils import format_file_size
                raise ValueError(
                    f"Modified file size ({format_file_size(len(content_bytes))}) would exceed limit "
                    f"({format_file_size(settings.max_file_size_bytes)})"
                )

            # Write the modified content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            modified_lines = [line.rstrip('\n') for line in lines]

            # Generate diff
            from app.utils import generate_diff
            diff_output = generate_diff(original_lines, modified_lines, f"{bucket}/{filename}")

            logger.info(f"Inserted at line {line_number} in: {bucket}/{filename}")
            return f"Successfully {position}d text at line {line_number} in {bucket}/{filename}:\n\n{diff_output}"

        except Exception as e:
            logger.error(f"Error inserting at line {line_number} in {bucket}/{filename}: {e}")
            raise

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
        file_path = self._get_file_path(bucket, filename)

        if not file_path.exists():
            raise FileNotFoundError(f"File {bucket}/{filename} not found")

        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_lines = content.split('\n')

            # Find start and end markers
            lines = content.split('\n')
            start_idx = None
            end_idx = None

            for i, line in enumerate(lines):
                if start_marker in line and start_idx is None:
                    start_idx = i
                elif end_marker in line and start_idx is not None:
                    end_idx = i
                    break

            if start_idx is None:
                return f"Start marker '{start_marker}' not found in {bucket}/{filename}"

            if end_idx is None:
                return f"End marker '{end_marker}' not found after start marker in {bucket}/{filename}"

            # Replace the section
            new_lines = lines[:start_idx + 1] + [new_content] + lines[end_idx:]
            modified_content = '\n'.join(new_lines)

            # Check file size
            content_bytes = modified_content.encode('utf-8')
            if len(content_bytes) > settings.max_file_size_bytes:
                from app.utils import format_file_size
                raise ValueError(
                    f"Modified file size ({format_file_size(len(content_bytes))}) would exceed limit "
                    f"({format_file_size(settings.max_file_size_bytes)})"
                )

            # Write the modified content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            # Generate diff
            from app.utils import generate_diff
            diff_output = generate_diff(original_lines, new_lines, f"{bucket}/{filename}")

            logger.info(f"Replaced section in: {bucket}/{filename}")
            return f"Successfully replaced section between '{start_marker}' and '{end_marker}' in {bucket}/{filename}:\n\n{diff_output}"

        except Exception as e:
            logger.error(f"Error replacing section in {bucket}/{filename}: {e}")
            raise

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
        file_path = self._get_file_path(bucket, filename)

        try:
            # Read existing content or create empty if file doesn't exist
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            else:
                existing_content = ""

            # Check for duplicates if requested
            if avoid_duplicates and existing_content:
                from app.utils import find_similar_lines
                similar_lines = find_similar_lines(existing_content, content, 0.8)
                if similar_lines:
                    line_num, line_text, similarity = similar_lines[0]
                    return f"Similar content already exists at line {line_num}: '{line_text}' (similarity: {similarity:.2f})"

            # Determine best insertion point
            from app.utils import smart_content_placement
            if existing_content:
                insertion_line, reason = smart_content_placement(
                    existing_content, content, section_hint
                )

                lines = existing_content.split('\n')
                original_lines = lines.copy()

                # Insert at the determined position
                if insertion_line >= len(lines):
                    # Append to end
                    if existing_content and not existing_content.endswith('\n'):
                        modified_content = existing_content + '\n' + content
                    else:
                        modified_content = existing_content + content
                else:
                    # Insert at specific line
                    lines.insert(insertion_line, content)
                    modified_content = '\n'.join(lines)
            else:
                # New file
                modified_content = content
                original_lines = []
                reason = "Created new file"

            # Check file size
            content_bytes = modified_content.encode('utf-8')
            if len(content_bytes) > settings.max_file_size_bytes:
                from app.utils import format_file_size
                raise ValueError(
                    f"Modified file size ({format_file_size(len(content_bytes))}) would exceed limit "
                    f"({format_file_size(settings.max_file_size_bytes)})"
                )

            # Write the content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            # Generate diff if there was existing content
            if existing_content:
                from app.utils import generate_diff
                modified_lines = modified_content.split('\n')
                diff_output = generate_diff(original_lines, modified_lines, f"{bucket}/{filename}")
                result = f"Smart append to {bucket}/{filename}: {reason}\n\n{diff_output}"
            else:
                result = f"Created new file {bucket}/{filename} with {len(content)} characters"

            logger.info(f"Smart append to: {bucket}/{filename}")
            return result

        except Exception as e:
            logger.error(f"Error with smart append to {bucket}/{filename}: {e}")
            raise

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
        file_path = self._get_file_path(bucket, filename)

        if not file_path.exists():
            raise FileNotFoundError(f"File {bucket}/{filename} not found")

        if modification_type not in ["replace", "insert_before", "insert_after", "delete"]:
            raise ValueError("modification_type must be 'replace', 'insert_before', 'insert_after', or 'delete'")

        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_lines = content.split('\n')
            lines = content.split('\n')
            modified = False

            # Find pattern in lines
            import re
            for i, line in enumerate(lines):
                if re.search(search_pattern, line):
                    if modification_type == "replace":
                        lines[i] = re.sub(search_pattern, new_content, line)
                    elif modification_type == "insert_before":
                        lines.insert(i, new_content)
                    elif modification_type == "insert_after":
                        lines.insert(i + 1, new_content)
                    elif modification_type == "delete":
                        lines.pop(i)
                    modified = True
                    break  # Only modify first match

            if not modified:
                return f"Pattern '{search_pattern}' not found in {bucket}/{filename}"

            modified_content = '\n'.join(lines)

            # Check file size
            content_bytes = modified_content.encode('utf-8')
            if len(content_bytes) > settings.max_file_size_bytes:
                from app.utils import format_file_size
                raise ValueError(
                    f"Modified file size ({format_file_size(len(content_bytes))}) would exceed limit "
                    f"({format_file_size(settings.max_file_size_bytes)})"
                )

            # Write the modified content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            # Generate diff
            from app.utils import generate_diff
            diff_output = generate_diff(original_lines, lines, f"{bucket}/{filename}")

            logger.info(f"Find and modify in: {bucket}/{filename}")
            return f"Successfully {modification_type}d content matching '{search_pattern}' in {bucket}/{filename}:\n\n{diff_output}"

        except Exception as e:
            logger.error(f"Error finding and modifying in {bucket}/{filename}: {e}")
            raise

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
        file_path = self._get_file_path(bucket, filename)

        if not file_path.exists():
            raise FileNotFoundError(f"File {bucket}/{filename} not found")

        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')

            if around_line:
                # Preview around specific line number
                center_line = around_line - 1  # Convert to 0-based
                start = max(0, center_line - context_lines)
                end = min(len(lines), center_line + context_lines + 1)
                preview_lines = lines[start:end]
                start_line_num = start + 1
            elif around_text:
                # Find text and preview around it
                for i, line in enumerate(lines):
                    if around_text.lower() in line.lower():
                        center_line = i
                        start = max(0, center_line - context_lines)
                        end = min(len(lines), center_line + context_lines + 1)
                        preview_lines = lines[start:end]
                        start_line_num = start + 1
                        break
                else:
                    return f"Text '{around_text}' not found in {bucket}/{filename}"
            else:
                # Preview from the beginning
                preview_lines = lines[:context_lines * 2]
                start_line_num = 1

            # Format with line numbers
            formatted_lines = []
            for i, line in enumerate(preview_lines):
                line_num = start_line_num + i
                formatted_lines.append(f"{line_num:4d}: {line}")

            preview = '\n'.join(formatted_lines)

            logger.info(f"Previewed section in: {bucket}/{filename}")
            return f"Preview of {bucket}/{filename}:\n\n{preview}"

        except Exception as e:
            logger.error(f"Error previewing {bucket}/{filename}: {e}")
            raise