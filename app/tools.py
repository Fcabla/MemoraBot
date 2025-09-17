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

    def write_file(self, bucket: str, filename: str, content: str) -> str:
        """Write content to a new file in a bucket.

        Args:
            bucket: The bucket (folder) name
            filename: The file name to create
            content: Content to write to the file

        Returns:
            Confirmation message

        Raises:
            ValueError: If file already exists
        """
        file_path = self._get_file_path(bucket, filename)

        if file_path.exists():
            raise ValueError(f"File {bucket}/{filename} already exists. Use append_file or delete first.")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Created file: {bucket}/{filename} ({len(content)} chars)")
            return f"Successfully created {bucket}/{filename} with {len(content)} characters"

        except Exception as e:
            logger.error(f"Error writing file {bucket}/{filename}: {e}")
            raise

    def append_file(self, bucket: str, filename: str, content: str) -> str:
        """Append content to an existing file.

        Args:
            bucket: The bucket (folder) name
            filename: The file name to append to
            content: Content to append

        Returns:
            Confirmation message
        """
        file_path = self._get_file_path(bucket, filename)

        try:
            # Create file if it doesn't exist
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Created new file: {bucket}/{filename}")
                return f"Created new file {bucket}/{filename} with {len(content)} characters"
            else:
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write('\n' + content)
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
            return f"Successfully deleted {bucket}/{filename}"

        except Exception as e:
            logger.error(f"Error deleting file {bucket}/{filename}: {e}")
            raise

    def list_files(self, bucket: Optional[str] = None) -> List[str]:
        """List files in a bucket or all buckets.

        Args:
            bucket: Optional bucket name. If None, lists all buckets.

        Returns:
            List of file paths
        """
        try:
            if bucket:
                # List files in specific bucket
                bucket_path = self._get_bucket_path(bucket)
                if not bucket_path.exists():
                    return []

                files = []
                for file_path in bucket_path.iterdir():
                    if file_path.is_file():
                        files.append(f"{bucket}/{file_path.name}")

                logger.info(f"Listed {len(files)} files in bucket: {bucket}")
                return sorted(files)
            else:
                # List all files in all buckets
                files = []
                for bucket_path in self.data_dir.iterdir():
                    if bucket_path.is_dir():
                        bucket_name = bucket_path.name
                        for file_path in bucket_path.iterdir():
                            if file_path.is_file():
                                files.append(f"{bucket_name}/{file_path.name}")

                logger.info(f"Listed {len(files)} files across all buckets")
                return sorted(files)

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

            for file_path in files_to_search:
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