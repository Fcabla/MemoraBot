# TICKET-008: File System Monitoring API

**Status:** TODO
**Phase:** 3 - Enhanced File Management
**Priority:** High
**Estimated Effort:** 1 day
**Dependencies:** TICKET-002, TICKET-004 (COMPLETED)

## Detail Section

### Purpose
Implement real-time file system monitoring and browsing capabilities so users can watch what the agent is doing with their files, browse the data folder structure through the API, and potentially edit files directly through the UI in future versions.

### Business Value
- **Transparency**: Users can see file changes in real-time as the agent works
- **File Browsing**: Navigate the data folder structure through the web interface
- **Trust Building**: Clear visibility into all file operations
- **Foundation for Advanced Features**: Enables future file editing UI and collaborative features
- **Debugging**: Easier troubleshooting of file operations

### Acceptance Criteria
- [ ] Real-time file change notifications via Server-Sent Events (SSE)
- [ ] API endpoints for browsing directory structure
- [ ] File content preview and retrieval endpoints
- [ ] File metadata (size, modified date, type) in responses
- [ ] Optional: Direct file editing through API (PUT endpoints)
- [ ] File change events include operation type (created, modified, deleted)
- [ ] Graceful handling of file system permissions and errors

## Implementation Section

### Technical Approach
- Use Python's **watchdog** library for file system monitoring
- Implement **Server-Sent Events (SSE)** for real-time updates (simpler than WebSocket for this use case)
- Add new API endpoints under `/files/` namespace
- Maintain compatibility with existing file tools

### Files to Create/Modify

#### 1. Add Dependencies to `pyproject.toml`

```toml
dependencies = [
    # ... existing dependencies ...
    "watchdog>=3.0.0",
    "aiofiles>=23.0.0",  # For async file operations
]
```

#### 2. Create `/app/file_monitor.py` - File System Monitoring

```python
"""File system monitoring and change detection."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from app.config import settings

logger = logging.getLogger("memorabot.file_monitor")


@dataclass
class FileChangeEvent:
    """Represents a file system change event."""
    event_type: str  # created, modified, deleted, moved
    file_path: str
    bucket: str
    filename: str
    timestamp: str
    file_size: Optional[int] = None
    is_directory: bool = False
    old_path: Optional[str] = None  # for moved events


class MemorabotFileHandler(FileSystemEventHandler):
    """Custom file system event handler for MemoraBot."""

    def __init__(self, data_dir: str, event_callback=None):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.event_callback = event_callback
        self.logger = logging.getLogger("memorabot.file_handler")

    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event."""
        try:
            # Skip temporary files and hidden files
            if self._should_ignore_path(event.src_path):
                return

            change_event = self._create_change_event(event)
            if change_event and self.event_callback:
                self.event_callback(change_event)

        except Exception as e:
            self.logger.error(f"Error handling file event: {e}", exc_info=True)

    def _should_ignore_path(self, path: str) -> bool:
        """Check if path should be ignored."""
        path_obj = Path(path)

        # Ignore hidden files and temporary files
        if any(part.startswith('.') for part in path_obj.parts):
            return True

        # Ignore common temporary file patterns
        ignored_patterns = ['.tmp', '.temp', '.swp', '.swo', '~']
        if any(path.endswith(pattern) for pattern in ignored_patterns):
            return True

        return False

    def _create_change_event(self, event: FileSystemEvent) -> Optional[FileChangeEvent]:
        """Convert watchdog event to our change event."""
        try:
            file_path = Path(event.src_path)

            # Extract bucket and filename from path
            relative_path = file_path.relative_to(self.data_dir)
            parts = relative_path.parts

            if len(parts) < 2:
                return None  # Skip root-level events

            bucket = parts[0]
            filename = "/".join(parts[1:])

            # Get file info
            file_size = None
            if not event.is_directory and file_path.exists():
                try:
                    file_size = file_path.stat().st_size
                except OSError:
                    pass

            # Map event types
            event_type_map = {
                'created': 'created',
                'modified': 'modified',
                'deleted': 'deleted',
                'moved': 'moved'
            }

            event_type = event_type_map.get(event.event_type, event.event_type)

            change_event = FileChangeEvent(
                event_type=event_type,
                file_path=str(relative_path),
                bucket=bucket,
                filename=filename,
                timestamp=datetime.now().isoformat(),
                file_size=file_size,
                is_directory=event.is_directory,
                old_path=str(Path(event.dest_path).relative_to(self.data_dir)) if hasattr(event, 'dest_path') else None
            )

            return change_event

        except Exception as e:
            self.logger.error(f"Error creating change event: {e}")
            return None


class FileSystemMonitor:
    """Main file system monitoring service."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.observer = None
        self.handler = None
        self.clients: Set[asyncio.Queue] = set()
        self.is_running = False

    def start(self):
        """Start monitoring the file system."""
        if self.is_running:
            return

        try:
            # Ensure data directory exists
            self.data_dir.mkdir(exist_ok=True)

            # Create handler and observer
            self.handler = MemorabotFileHandler(
                str(self.data_dir),
                event_callback=self._on_file_change
            )

            self.observer = Observer()
            self.observer.schedule(
                self.handler,
                str(self.data_dir),
                recursive=True
            )

            self.observer.start()
            self.is_running = True

            logger.info(f"File system monitoring started for: {self.data_dir}")

        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")

    def stop(self):
        """Stop monitoring the file system."""
        if not self.is_running:
            return

        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()

            self.is_running = False
            logger.info("File system monitoring stopped")

        except Exception as e:
            logger.error(f"Error stopping file monitoring: {e}")

    def add_client(self, client_queue: asyncio.Queue):
        """Add a client queue for event notifications."""
        self.clients.add(client_queue)

    def remove_client(self, client_queue: asyncio.Queue):
        """Remove a client queue."""
        self.clients.discard(client_queue)

    def _on_file_change(self, event: FileChangeEvent):
        """Handle file change events by notifying all clients."""
        event_data = asdict(event)

        # Log the event
        logger.info(f"File event: {event.event_type} - {event.file_path}")

        # Notify all connected clients
        for client_queue in self.clients.copy():
            try:
                client_queue.put_nowait(event_data)
            except asyncio.QueueFull:
                # Remove client if queue is full (client not consuming)
                self.clients.discard(client_queue)
                logger.warning("Removed slow client from file monitoring")


# Global monitor instance
file_monitor = FileSystemMonitor(settings.DATA_DIR)
```

#### 3. Create `/app/routers/files.py` - File Browsing API

```python
"""File browsing and monitoring API endpoints."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import aiofiles

from app.config import settings
from app.file_monitor import file_monitor
from app.utils import format_file_size, sanitize_filename, sanitize_bucket_name

logger = logging.getLogger("memorabot.files")
router = APIRouter()


class FileInfo(BaseModel):
    """File information model."""
    name: str
    path: str
    is_directory: bool
    size: Optional[int] = None
    size_formatted: Optional[str] = None
    modified: Optional[str] = None
    created: Optional[str] = None
    extension: Optional[str] = None


class DirectoryListing(BaseModel):
    """Directory listing response."""
    current_path: str
    parent_path: Optional[str]
    directories: List[FileInfo]
    files: List[FileInfo]
    total_items: int


class FileContent(BaseModel):
    """File content response."""
    content: str
    encoding: str
    size: int
    modified: str


@router.get("/browse", response_model=DirectoryListing)
@router.get("/browse/{path:path}", response_model=DirectoryListing)
async def browse_directory(path: str = ""):
    """Browse directory structure in the data folder.

    Args:
        path: Relative path within data directory (e.g., "notes" or "notes/2024")

    Returns:
        Directory listing with files and subdirectories
    """
    try:
        # Sanitize and resolve path
        data_dir = Path(settings.DATA_DIR)
        if path:
            current_path = data_dir / path
        else:
            current_path = data_dir

        # Security check - ensure path is within data directory
        try:
            current_path.resolve().relative_to(data_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid path")

        if not current_path.exists():
            raise HTTPException(status_code=404, detail="Directory not found")

        if not current_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")

        # Get parent path
        parent_path = None
        if current_path != data_dir:
            parent_rel = current_path.parent.relative_to(data_dir)
            parent_path = str(parent_rel) if str(parent_rel) != "." else ""

        # List directory contents
        directories = []
        files = []

        for item in current_path.iterdir():
            try:
                # Skip hidden files
                if item.name.startswith('.'):
                    continue

                stat = item.stat()
                item_path = item.relative_to(data_dir)

                file_info = FileInfo(
                    name=item.name,
                    path=str(item_path),
                    is_directory=item.is_dir(),
                    size=stat.st_size if not item.is_dir() else None,
                    size_formatted=format_file_size(stat.st_size) if not item.is_dir() else None,
                    modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    extension=item.suffix if not item.is_dir() else None
                )

                if item.is_dir():
                    directories.append(file_info)
                else:
                    files.append(file_info)

            except (OSError, ValueError) as e:
                logger.warning(f"Error reading item {item}: {e}")
                continue

        # Sort results
        directories.sort(key=lambda x: x.name.lower())
        files.sort(key=lambda x: x.name.lower())

        return DirectoryListing(
            current_path=path,
            parent_path=parent_path,
            directories=directories,
            files=files,
            total_items=len(directories) + len(files)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error browsing directory {path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/content/{bucket}/{filename:path}", response_model=FileContent)
async def get_file_content(bucket: str, filename: str):
    """Get the content of a specific file.

    Args:
        bucket: Bucket (directory) name
        filename: File name (can include subdirectories)

    Returns:
        File content and metadata
    """
    try:
        # Sanitize inputs
        bucket = sanitize_bucket_name(bucket)
        filename = sanitize_filename(filename)

        # Build file path
        data_dir = Path(settings.DATA_DIR)
        file_path = data_dir / bucket / filename

        # Security check
        try:
            file_path.resolve().relative_to(data_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid file path")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if file_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is a directory, not a file")

        # Check file size (optional limit)
        stat = file_path.stat()
        max_size = 10 * 1024 * 1024  # 10MB limit for web display
        if stat.st_size > max_size:
            raise HTTPException(status_code=413, detail="File too large for display")

        # Read file content
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            encoding = 'utf-8'
        except UnicodeDecodeError:
            # Try binary mode for non-text files
            async with aiofiles.open(file_path, 'rb') as f:
                content_bytes = await f.read()
            content = content_bytes.decode('utf-8', errors='replace')
            encoding = 'binary'

        return FileContent(
            content=content,
            encoding=encoding,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading file {bucket}/{filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/content/{bucket}/{filename:path}")
async def update_file_content(
    bucket: str,
    filename: str,
    request: Request
):
    """Update file content directly (optional feature).

    Args:
        bucket: Bucket (directory) name
        filename: File name
        request: Request body containing new file content as text

    Returns:
        Success confirmation
    """
    try:
        # Get content from request body
        content = await request.body()
        content_str = content.decode('utf-8')

        # Use existing file tools for consistency
        from app.tools import FileTools
        tools = FileTools(settings.DATA_DIR)

        # Check if file exists to determine operation
        data_dir = Path(settings.DATA_DIR)
        file_path = data_dir / sanitize_bucket_name(bucket) / sanitize_filename(filename)

        if file_path.exists():
            # Update existing file
            result = tools.write_file(bucket, filename, content_str, overwrite=True)
        else:
            # Create new file
            result = tools.write_file(bucket, filename, content_str)

        return {"status": "success", "message": result}

    except Exception as e:
        logger.error(f"Error updating file {bucket}/{filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watch")
async def watch_file_changes():
    """Server-Sent Events endpoint for real-time file change notifications.

    Returns:
        SSE stream of file change events
    """

    async def event_stream():
        # Create client queue
        client_queue = asyncio.Queue(maxsize=100)

        try:
            # Add client to monitor
            file_monitor.add_client(client_queue)

            # Send initial connection confirmation
            yield f"data: {json.dumps({'type': 'connected', 'message': 'File monitoring started'})}\n\n"

            # Stream events
            while True:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                    yield f"data: {json.dumps({'type': 'file_change', 'event': event})}\n\n"

                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield f"data: {json.dumps({'type': 'ping', 'timestamp': datetime.now().isoformat()})}\n\n"

        except asyncio.CancelledError:
            logger.info("File monitoring client disconnected")
        except Exception as e:
            logger.error(f"Error in file monitoring stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # Clean up
            file_monitor.remove_client(client_queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/stats")
async def get_file_stats():
    """Get overall statistics about the file system.

    Returns:
        File system statistics
    """
    try:
        from app.tools import FileTools
        tools = FileTools(settings.DATA_DIR)

        stats = tools.get_bucket_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting file stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### 4. Update `/app/main.py` - Add File Monitoring Startup

```python
# Add to imports
from app.file_monitor import file_monitor
from app.routers import chat, health, files  # Add files router

# Update lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting MemoraBot application")

    # Ensure data directory exists
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    # Start file monitoring
    file_monitor.start()

    yield

    # Shutdown
    logger.info("Shutting down MemoraBot application")
    file_monitor.stop()

# Add files router
app.include_router(files.router, prefix="/files", tags=["files"])
```

#### 5. Optional: Add Frontend File Browser Component

Create `/static/js/file-browser.js`:

```javascript
/**
 * File browser component for real-time file monitoring
 */

class FileBrowser {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentPath = '';
        this.eventSource = null;

        this.initializeFileMonitoring();
    }

    async initializeFileMonitoring() {
        // Connect to file change events
        this.eventSource = new EventSource('/files/watch');

        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleFileEvent(data);
        };

        this.eventSource.onerror = (error) => {
            console.error('File monitoring error:', error);
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.reconnect(), 5000);
        };
    }

    handleFileEvent(data) {
        if (data.type === 'file_change') {
            const event = data.event;
            this.displayFileChangeNotification(event);

            // Refresh current view if needed
            if (this.shouldRefreshView(event)) {
                this.refreshCurrentView();
            }
        }
    }

    displayFileChangeNotification(event) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'file-change-notification';

        const icon = this.getEventIcon(event.event_type);
        const message = `${icon} ${event.event_type}: ${event.file_path}`;

        notification.textContent = message;

        // Add to notifications area (create if doesn't exist)
        let notificationsArea = document.getElementById('file-notifications');
        if (!notificationsArea) {
            notificationsArea = document.createElement('div');
            notificationsArea.id = 'file-notifications';
            notificationsArea.className = 'file-notifications-area';
            document.body.appendChild(notificationsArea);
        }

        notificationsArea.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => notification.remove(), 5000);
    }

    getEventIcon(eventType) {
        const icons = {
            'created': '➕',
            'modified': '✏️',
            'deleted': '🗑️',
            'moved': '📦'
        };
        return icons[eventType] || '📄';
    }

    shouldRefreshView(event) {
        // Refresh if event is in current directory
        return event.file_path.startsWith(this.currentPath);
    }

    async refreshCurrentView() {
        // Implement view refresh logic based on your UI
        console.log('Refreshing file view for path:', this.currentPath);
    }

    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    reconnect() {
        this.disconnect();
        this.initializeFileMonitoring();
    }
}

// CSS for notifications
const fileMonitoringStyles = `
.file-notifications-area {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    max-width: 300px;
}

.file-change-notification {
    background: var(--primary-color);
    color: white;
    padding: 0.75rem;
    border-radius: 6px;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    box-shadow: var(--shadow);
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
`;

// Add styles to document
const styleSheet = document.createElement('style');
styleSheet.textContent = fileMonitoringStyles;
document.head.appendChild(styleSheet);
```

### Usage Examples

Once implemented:

1. **Real-time monitoring**:
   ```javascript
   // Files changed by agent appear as notifications
   const browser = new FileBrowser('file-browser-container');
   ```

2. **Browse files via API**:
   ```bash
   curl http://localhost:8000/files/browse/notes
   # Returns directory listing of notes bucket
   ```

3. **Get file content**:
   ```bash
   curl http://localhost:8000/files/content/notes/shopping.txt
   # Returns file content and metadata
   ```

4. **Watch changes**:
   ```bash
   curl http://localhost:8000/files/watch
   # Streams file change events in real-time
   ```

### Testing Steps

1. **Test file monitoring**:
   - Start the application
   - Create/modify files through the agent
   - Verify events appear in `/files/watch` stream

2. **Test directory browsing**:
   - Browse `/files/browse` API
   - Navigate to different bucket directories
   - Verify file metadata is correct

3. **Test file content retrieval**:
   - Get content of existing files via API
   - Verify encoding and metadata

### Verification Checklist
- [ ] File system monitoring starts/stops with application
- [ ] SSE stream provides real-time file change events
- [ ] Directory browsing API returns correct file listings
- [ ] File content API handles text files correctly
- [ ] Security: Path traversal protection works
- [ ] Error handling for missing files/directories
- [ ] Performance: No significant impact on file operations

### Related Files
- `/app/file_monitor.py` - Core monitoring service
- `/app/routers/files.py` - API endpoints
- `/app/main.py` - Application startup integration
- `/static/js/file-browser.js` - Frontend component (optional)

### Future Enhancements
After this ticket, you could add:
- File upload capabilities
- In-browser file editor
- File operation history
- Collaborative editing features

### Next Steps
This completes the core intelligent file management enhancement phase. The system will now have coding-agent-like capabilities with intelligent editing, markdown rendering, and real-time file monitoring.