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
                    bucket_name, filename = file_path.split('/', 1)

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