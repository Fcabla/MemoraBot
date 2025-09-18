# TICKET-004: File Tools Enhancement

**Status:** COMPLETED
**Phase:** 1 - Foundation & Core Infrastructure
**Priority:** High
**Estimated Effort:** 0.5 day
**Dependencies:** TICKET-003 (COMPLETED)

## Detail Section

### Purpose
Enhance the existing file manipulation tools in MemoraBot with additional features for better file management, validation, and metadata handling. Build upon the basic implementation from TICKET-003.

### Current State
TICKET-003 has already implemented:
- Basic FileTools class with CRUD operations (read, write, append, delete)
- File listing and searching
- Tool registration in agents.py
- Basic path sanitization

### Business Value
- Enhanced data integrity with size and type validation
- Better file organization with detailed metadata
- Improved search capabilities
- Comprehensive bucket statistics

### Acceptance Criteria
- [x] Keep tools synchronous (as per PydanticAI best practices)
- [x] Add file size validation
- [x] Add file type validation
- [x] Enhance list_files to return detailed metadata
- [x] Add get_bucket_stats() method
- [x] Add list_directory() method for directory navigation
- [x] Add overwrite parameter to write_file
- [x] Add configurable separator to append_file
- [x] Implement empty bucket cleanup
- [x] Improve search results with better excerpts

## Implementation Section

### Files to Modify

#### 1. Enhance `/app/tools.py`

Key enhancements needed:

1. **Add file size validation**:
   - Check against `settings.max_file_size_bytes` in write/append operations
   - Raise ValueError if exceeded

2. **Add file type validation**:
   - Use `is_allowed_file_type()` from utils
   - Check against `settings.ALLOWED_FILE_TYPES`

3. **Enhance write_file()**:
   - Add `overwrite: bool = False` parameter
   - Check if file exists and handle accordingly

4. **Enhance append_file()**:
   - Add `separator: str = "\n\n"` parameter
   - Use separator when appending content

5. **Enhance list_files()**:
   - Return List[Dict[str, Any]] instead of List[str]
   - Include: bucket, filename, path, size, size_formatted, modified, created

6. **Add get_bucket_stats()**:
   ```python
   def get_bucket_stats(self) -> Dict[str, Any]:
       """Get statistics about buckets and files.
       Returns dict with total_buckets, total_files, total_size, buckets info"""
   ```

7. **Add list_directory()**:
   ```python
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
   ```

8. **Empty bucket cleanup**:
   - In delete_file(), remove empty bucket directory after deletion

#### 2. Update `/app/utils.py`

Add missing utility functions if not present:

```python
def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def is_allowed_file_type(filename: str) -> bool:
    """Check if file type is allowed based on extension."""
    from app.config import settings
    extension = Path(filename).suffix.lower()
    allowed = settings.ALLOWED_FILE_TYPES.split(',')
    return extension in allowed
```

#### 3. Update `/app/config.py`

Ensure these settings exist:

```python
# File settings
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
max_file_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", ".txt,.md,.json,.yaml,.yml")
```

### Testing Steps

1. **Verify existing functionality**:
   ```bash
   python -c "from app.tools import FileTools; print('Basic tools work')"
   ```

2. **Test enhanced features**:
   ```python
   from app.tools import FileTools
   tools = FileTools()

   # Test with overwrite parameter
   tools.write_file("test", "file.txt", "content", overwrite=True)

   # Test list_files returns detailed info
   files = tools.list_files()
   print(files[0])  # Should have size, modified, created fields

   # Test directory listing
   dir_contents = tools.list_directory()
   print(dir_contents)  # Should show buckets and files at root

   dir_contents = tools.list_directory("notes")
   print(dir_contents)  # Should show contents of notes bucket

   # Test bucket stats
   stats = tools.get_bucket_stats()
   print(stats)
   ```

3. **Run unit tests**:
   ```bash
   pytest tests/test_tools.py -v
   ```

### Verification Checklist
- [x] File size validation works (settings.max_file_size_bytes)
- [x] File type validation works (settings.ALLOWED_FILE_TYPES)
- [x] write_file() has overwrite parameter
- [x] append_file() has separator parameter
- [x] list_files() returns detailed metadata
- [x] list_directory() provides navigation structure
- [x] get_bucket_stats() returns statistics
- [x] Empty bucket cleanup works
- [x] All operations remain synchronous (not async)

### Important Notes

1. **Keep Tools Synchronous**: Per PydanticAI best practices, tools registered with `@agent.tool` should be synchronous functions, not async. The existing implementation correctly uses synchronous file operations.

2. **Agent Registration**: The tools are already properly registered in `agents.py` using the `@agent.tool` decorator with synchronous wrapper functions.

3. **Dependencies**: This ticket builds on TICKET-003's basic implementation and enhances it with additional features.

#### 4. Update `/app/agents.py` - Register new tool

Add the list_directory tool registration in the `_register_tools()` method:

```python
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
```

### Related Files
- `/app/tools.py` - File manipulation tools (enhance existing)
- `/app/utils.py` - Utility functions (add missing helpers)
- `/app/config.py` - Configuration (add file settings)
- `/app/agents.py` - Tool registration (add list_directory)

### Next Steps
After completion, proceed to Phase 2 tickets for chat interface implementation.