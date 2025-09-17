# TICKET-005: Chat UI Templates & Styling

**Status:** TODO
**Phase:** 2 - Chat Interface & User Interaction
**Priority:** High
**Estimated Effort:** 1.5 days
**Dependencies:** TICKET-002, TICKET-004

## Detail Section

### Purpose
Create the complete chat user interface using Jinja2 templates with clean, modern styling. The UI should display all conversation elements transparently, including tool calls and responses, making the agent's decision-making process visible to users.

### Business Value
- Provides intuitive user interface for interacting with MemoraBot
- Builds trust through transparency of operations
- Creates professional, responsive design
- Enhances user experience with clear visual hierarchy

### Acceptance Criteria
- [ ] Chat interface renders correctly in all modern browsers
- [ ] Messages display with proper formatting and timestamps
- [ ] Tool calls are visually distinct from regular messages
- [ ] Input area supports multiline text
- [ ] Auto-scrolling works for new messages
- [ ] Mobile-responsive design
- [ ] Loading states display during processing

## Implementation Section

### Files to Create/Modify

#### 1. `/static/css/main.css`
```css
/* Main application styles */

:root {
    --primary-color: #2563eb;
    --primary-hover: #1d4ed8;
    --bg-color: #f9fafb;
    --card-bg: #ffffff;
    --text-primary: #111827;
    --text-secondary: #6b7280;
    --border-color: #e5e7eb;
    --success-color: #10b981;
    --error-color: #ef4444;
    --warning-color: #f59e0b;
    --tool-bg: #f3f4f6;
    --tool-border: #d1d5db;
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-primary);
    line-height: 1.6;
    height: 100vh;
    overflow: hidden;
}

.app-container {
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 1rem;
}

/* Chat Container */
.chat-container {
    background: var(--card-bg);
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
    width: 100%;
    max-width: 900px;
    height: 90vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* Chat Header */
.chat-header {
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color);
    background: linear-gradient(135deg, var(--primary-color), #3b82f6);
    color: white;
}

.chat-header h1 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
}

.chat-header p {
    font-size: 0.875rem;
    opacity: 0.9;
}

/* Chat Messages Area */
.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
    scroll-behavior: smooth;
}

.chat-messages::-webkit-scrollbar {
    width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
    background: var(--bg-color);
    border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
    background: var(--text-secondary);
}

/* Message Styles */
.message {
    margin-bottom: 1.5rem;
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.message-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

.message-role {
    font-weight: 600;
    font-size: 0.875rem;
    text-transform: capitalize;
}

.message-timestamp {
    font-size: 0.75rem;
    color: var(--text-secondary);
}

.message-content {
    padding: 0.75rem 1rem;
    border-radius: 8px;
    background: var(--bg-color);
    position: relative;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* Role-specific styles */
.message.user .message-content {
    background: var(--primary-color);
    color: white;
    margin-left: 20%;
}

.message.assistant .message-content {
    background: var(--bg-color);
    border: 1px solid var(--border-color);
    margin-right: 20%;
}

.message.system .message-content {
    background: var(--warning-color);
    color: white;
    text-align: center;
    margin: 0 auto;
    max-width: 70%;
}

.message.error .message-content {
    background: var(--error-color);
    color: white;
}

/* Tool Call Styles */
.tool-call {
    background: var(--tool-bg);
    border: 1px solid var(--tool-border);
    border-radius: 6px;
    padding: 0.75rem;
    margin: 0.5rem 0;
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
}

.tool-call-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: var(--primary-color);
}

.tool-call-icon {
    width: 16px;
    height: 16px;
    display: inline-block;
}

.tool-call-name {
    font-family: 'Courier New', monospace;
}

.tool-call-args {
    background: white;
    padding: 0.5rem;
    border-radius: 4px;
    margin-top: 0.5rem;
    border: 1px solid var(--border-color);
}

.tool-call-result {
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 4px;
    color: #166534;
}

.tool-call-result.error {
    background: #fef2f2;
    border-color: #fca5a5;
    color: #991b1b;
}

/* Input Area */
.chat-input-container {
    padding: 1.5rem;
    border-top: 1px solid var(--border-color);
    background: var(--card-bg);
    display: flex;
    gap: 1rem;
}

.message-input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    font-size: 0.875rem;
    resize: vertical;
    min-height: 60px;
    max-height: 150px;
    font-family: inherit;
    line-height: 1.5;
}

.message-input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.send-button {
    padding: 0.75rem 1.5rem;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
    align-self: flex-end;
}

.send-button:hover:not(:disabled) {
    background: var(--primary-hover);
}

.send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Loading States */
.loading-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--bg-color);
    border-radius: 8px;
    margin-bottom: 1rem;
}

.loading-dots {
    display: flex;
    gap: 0.25rem;
}

.loading-dot {
    width: 8px;
    height: 8px;
    background: var(--primary-color);
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) { animation-delay: -0.32s; }
.loading-dot:nth-child(2) { animation-delay: -0.16s; }
.loading-dot:nth-child(3) { animation-delay: 0; }

@keyframes bounce {
    0%, 80%, 100% {
        transform: scale(0);
    }
    40% {
        transform: scale(1);
    }
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .chat-container {
        height: 100vh;
        max-width: 100%;
        border-radius: 0;
    }

    .message.user .message-content {
        margin-left: 10%;
    }

    .message.assistant .message-content {
        margin-right: 10%;
    }

    .chat-input-container {
        padding: 1rem;
    }
}

/* Utility Classes */
.text-muted {
    color: var(--text-secondary);
}

.text-small {
    font-size: 0.875rem;
}

.text-error {
    color: var(--error-color);
}

.text-success {
    color: var(--success-color);
}

.mt-1 { margin-top: 0.5rem; }
.mt-2 { margin-top: 1rem; }
.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
```

#### 2. Update `/templates/chat.html`
```html
{% extends "base.html" %}

{% block title %}MemoraBot - Chat{% endblock %}

{% block extra_head %}
<style>
    /* Additional inline styles for icons */
    .icon-user::before { content: "👤"; }
    .icon-bot::before { content: "🤖"; }
    .icon-tool::before { content: "🔧"; }
    .icon-file::before { content: "📄"; }
    .icon-folder::before { content: "📁"; }
    .icon-search::before { content: "🔍"; }
    .icon-write::before { content: "✏️"; }
    .icon-delete::before { content: "🗑️"; }
</style>
{% endblock %}

{% block content %}
<div class="chat-container">
    <header class="chat-header">
        <h1>🗂️ MemoraBot</h1>
        <p>Your AI File & Note Assistant</p>
    </header>

    <div class="chat-messages" id="chatMessages">
        <!-- Welcome message -->
        <div class="message assistant">
            <div class="message-header">
                <span class="message-role icon-bot">Assistant</span>
                <span class="message-timestamp" data-timestamp="{{ current_time }}"></span>
            </div>
            <div class="message-content">
Hello! I'm MemoraBot, your intelligent file and note assistant. I can help you:

• Create and organize notes in categorized buckets
• Search through your existing files
• Append information to existing notes
• Manage your knowledge base efficiently

What would you like to work on today?
            </div>
        </div>
    </div>

    <div class="chat-input-container">
        <textarea
            id="messageInput"
            class="message-input"
            placeholder="Type your message here... (Shift+Enter for new line, Enter to send)"
            rows="3"
            autofocus
        ></textarea>
        <button id="sendButton" class="send-button" type="button">
            Send
        </button>
    </div>
</div>

<!-- Message Templates (hidden) -->
<div id="templates" style="display: none;">
    <!-- User Message Template -->
    <div class="message user" id="userMessageTemplate">
        <div class="message-header">
            <span class="message-role icon-user">You</span>
            <span class="message-timestamp" data-timestamp=""></span>
        </div>
        <div class="message-content"></div>
    </div>

    <!-- Assistant Message Template -->
    <div class="message assistant" id="assistantMessageTemplate">
        <div class="message-header">
            <span class="message-role icon-bot">Assistant</span>
            <span class="message-timestamp" data-timestamp=""></span>
        </div>
        <div class="message-content"></div>
    </div>

    <!-- Tool Call Template -->
    <div class="tool-call" id="toolCallTemplate">
        <div class="tool-call-header">
            <span class="tool-call-icon"></span>
            <span class="tool-call-name"></span>
        </div>
        <div class="tool-call-args"></div>
        <div class="tool-call-result"></div>
    </div>

    <!-- Loading Template -->
    <div class="loading-indicator" id="loadingTemplate">
        <span>MemoraBot is thinking</span>
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    </div>

    <!-- Error Message Template -->
    <div class="message error" id="errorMessageTemplate">
        <div class="message-header">
            <span class="message-role">⚠️ Error</span>
            <span class="message-timestamp" data-timestamp=""></span>
        </div>
        <div class="message-content"></div>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script src="{{ url_for('static', path='/js/chat.js') }}"></script>
{% endblock %}
```

#### 3. `/static/js/chat.js`
```javascript
/**
 * MemoraBot Chat Interface JavaScript
 */

class ChatInterface {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.conversationId = this.generateConversationId();
        this.isProcessing = false;

        this.initializeEventListeners();
        this.updateTimestamps();
        setInterval(() => this.updateTimestamps(), 60000); // Update every minute
    }

    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // Enter key to send (Shift+Enter for new line)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isProcessing) return;

        // Disable input while processing
        this.setProcessing(true);

        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';

        // Add user message to chat
        this.addMessage('user', message);

        // Show loading indicator
        const loadingId = this.showLoading();

        try {
            // Send to server
            const response = await fetch('/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId
                })
            });

            // Remove loading indicator
            this.removeLoading(loadingId);

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();

            // Display tool calls if any
            if (data.tool_calls && data.tool_calls.length > 0) {
                this.displayToolCalls(data.tool_calls);
            }

            // Add assistant response
            this.addMessage('assistant', data.message);

            // Update conversation ID if provided
            if (data.conversation_id) {
                this.conversationId = data.conversation_id;
            }

        } catch (error) {
            // Remove loading indicator
            this.removeLoading(loadingId);

            // Show error message
            this.addMessage('error', `Failed to send message: ${error.message}`);
            console.error('Chat error:', error);
        } finally {
            this.setProcessing(false);
        }
    }

    addMessage(role, content, toolCalls = null) {
        const template = document.getElementById(`${role}MessageTemplate`);
        if (!template) {
            console.error(`Template not found for role: ${role}`);
            return;
        }

        const message = template.cloneNode(true);
        message.id = ''; // Remove template ID
        message.style.display = ''; // Make visible

        // Set content
        const contentEl = message.querySelector('.message-content');
        if (contentEl) {
            contentEl.textContent = content;
        }

        // Set timestamp
        const timestampEl = message.querySelector('.message-timestamp');
        if (timestampEl) {
            timestampEl.setAttribute('data-timestamp', new Date().toISOString());
            timestampEl.textContent = 'just now';
        }

        // Add to chat
        this.chatMessages.appendChild(message);
        this.scrollToBottom();
    }

    displayToolCalls(toolCalls) {
        const container = document.createElement('div');
        container.className = 'message system';

        const header = document.createElement('div');
        header.className = 'message-header';
        header.innerHTML = '<span class="message-role">🔧 Tool Calls</span>';
        container.appendChild(header);

        const content = document.createElement('div');
        content.className = 'message-content';

        toolCalls.forEach(call => {
            const toolCall = this.createToolCallElement(call);
            content.appendChild(toolCall);
        });

        container.appendChild(content);
        this.chatMessages.appendChild(container);
        this.scrollToBottom();
    }

    createToolCallElement(call) {
        const template = document.getElementById('toolCallTemplate');
        const element = template.cloneNode(true);
        element.id = '';
        element.style.display = '';

        // Set tool name and icon
        const nameEl = element.querySelector('.tool-call-name');
        const iconEl = element.querySelector('.tool-call-icon');

        if (nameEl) nameEl.textContent = call.tool;

        // Set icon based on tool type
        if (iconEl) {
            const iconMap = {
                'read_file': '📖',
                'write_file': '✏️',
                'append_file': '➕',
                'delete_file': '🗑️',
                'list_files': '📋',
                'search_files': '🔍'
            };
            iconEl.textContent = iconMap[call.tool] || '🔧';
        }

        // Set arguments
        const argsEl = element.querySelector('.tool-call-args');
        if (argsEl && call.arguments) {
            argsEl.textContent = JSON.stringify(call.arguments, null, 2);
        }

        // Set result
        const resultEl = element.querySelector('.tool-call-result');
        if (resultEl && call.result) {
            resultEl.textContent = typeof call.result === 'string'
                ? call.result
                : JSON.stringify(call.result, null, 2);

            // Add error class if result indicates error
            if (call.result.error || (typeof call.result === 'string' && call.result.includes('Error'))) {
                resultEl.classList.add('error');
            }
        }

        return element;
    }

    showLoading() {
        const template = document.getElementById('loadingTemplate');
        const loading = template.cloneNode(true);
        const loadingId = `loading-${Date.now()}`;
        loading.id = loadingId;
        loading.style.display = '';

        this.chatMessages.appendChild(loading);
        this.scrollToBottom();

        return loadingId;
    }

    removeLoading(loadingId) {
        const loading = document.getElementById(loadingId);
        if (loading) {
            loading.remove();
        }
    }

    setProcessing(isProcessing) {
        this.isProcessing = isProcessing;
        this.sendButton.disabled = isProcessing;
        this.messageInput.disabled = isProcessing;

        if (isProcessing) {
            this.sendButton.textContent = 'Sending...';
        } else {
            this.sendButton.textContent = 'Send';
            this.messageInput.focus();
        }
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    updateTimestamps() {
        const timestamps = document.querySelectorAll('.message-timestamp[data-timestamp]');
        timestamps.forEach(el => {
            const timestamp = el.getAttribute('data-timestamp');
            if (timestamp) {
                el.textContent = this.formatRelativeTime(new Date(timestamp));
            }
        });
    }

    formatRelativeTime(date) {
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // Difference in seconds

        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} hour${Math.floor(diff / 3600) > 1 ? 's' : ''} ago`;
        return date.toLocaleDateString();
    }

    generateConversationId() {
        return 'conv-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }
}

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});
```

#### 4. `/static/js/main.js` (general utilities)
```javascript
/**
 * General utility functions
 */

// Format dates consistently
function formatDate(date) {
    return new Date(date).toLocaleString();
}

// Copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        return false;
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    // Implementation for toast notifications if needed
    console.log(`[${type.toUpperCase()}] ${message}`);
}
```

### Testing Steps

1. **Visual testing**
   - Open http://localhost:8000 in different browsers
   - Test on different screen sizes
   - Verify responsive design

2. **Interaction testing**
   - Send messages and verify display
   - Test Shift+Enter for multiline
   - Test Enter to send
   - Verify auto-scroll works

3. **Tool call display**
   - Send messages that trigger file operations
   - Verify tool calls display correctly
   - Check that results are formatted properly

### Verification Checklist
- [ ] Chat interface renders correctly
- [ ] Messages display with proper styling
- [ ] Tool calls are visually distinct
- [ ] Timestamps update correctly
- [ ] Auto-scrolling works
- [ ] Input area resizes properly
- [ ] Loading states display
- [ ] Error messages show correctly
- [ ] Mobile responsive design works

### Related Files
- `/templates/chat.html` - Main chat template
- `/static/css/main.css` - Styling
- `/static/js/chat.js` - Chat functionality
- `/app/routers/chat.py` - Backend API

### Next Steps
After completion, proceed to TICKET-006 for WebSocket/SSE implementation.