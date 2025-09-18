/**
 * MemoraBot Chat Interface JavaScript
 */

class ChatInterface {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.themeSwitcher = document.getElementById('themeSwitcher');
        this.themeIcon = document.getElementById('themeIcon');
        this.themeText = document.getElementById('themeText');
        this.conversationId = this.generateConversationId();
        this.isProcessing = false;

        this.initializeEventListeners();
        this.initializeTheme();
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

        // Theme switcher
        this.themeSwitcher.addEventListener('click', () => this.toggleTheme());
    }

    initializeTheme() {
        // Get saved theme or default to light
        const savedTheme = localStorage.getItem('memorabot-theme') || 'light';
        this.setTheme(savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('memorabot-theme', theme);

        if (theme === 'dark') {
            this.themeIcon.textContent = '☀️';
            this.themeText.textContent = 'Light';
        } else {
            this.themeIcon.textContent = '🌙';
            this.themeText.textContent = 'Dark';
        }
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
        // Filter out empty or invalid tool calls
        const validToolCalls = toolCalls.filter(call =>
            call && call.tool && typeof call.tool === 'string'
        );

        if (validToolCalls.length === 0) return;

        const container = document.createElement('div');
        container.className = 'message system';

        const header = document.createElement('div');
        header.className = 'message-header';
        header.innerHTML = '<span class="message-role">🔧 Tool Calls</span>';
        container.appendChild(header);

        const content = document.createElement('div');
        content.className = 'message-content';

        validToolCalls.forEach((call) => {
            const toolCall = this.createToolCallElement(call);
            content.appendChild(toolCall);
        });

        container.appendChild(content);
        this.chatMessages.appendChild(container);
        this.scrollToBottom();
    }

    createToolCallElement(call) {
        // Validate the call object
        if (!call || !call.tool) {
            console.error('Invalid tool call:', call);
            return document.createElement('div');
        }

        const element = document.createElement('div');
        element.className = 'tool-call';

        // Create header with icon and name
        const header = document.createElement('div');
        header.className = 'tool-call-header';

        const icon = document.createElement('span');
        icon.className = 'tool-call-icon';
        const iconMap = {
            'read_file': '📖',
            'write_file': '✏️',
            'append_file': '➕',
            'delete_file': '🗑️',
            'list_files': '📋',
            'search_files': '🔍'
        };
        icon.textContent = iconMap[call.tool] || '🔧';

        const name = document.createElement('span');
        name.className = 'tool-call-name';
        name.textContent = call.tool || 'unknown';

        header.appendChild(icon);
        header.appendChild(name);

        // Create summary of what was done
        const summary = document.createElement('span');
        summary.className = 'tool-call-summary';
        summary.textContent = this.getToolSummary(call);

        // Create result status
        const status = document.createElement('span');
        status.className = 'tool-call-result-status';
        const hasError = call.result && (call.result.error ||
            (typeof call.result === 'string' && call.result.includes('Error')));
        status.textContent = hasError ? 'Failed' : 'Success';
        if (hasError) status.classList.add('error');

        element.appendChild(header);
        element.appendChild(summary);
        element.appendChild(status);

        // Add click to expand
        element.addEventListener('click', () => {
            element.classList.toggle('expanded');
            this.showToolDetails(element, call);
        });

        return element;
    }

    getToolSummary(call) {
        const { tool, arguments: args = {} } = call;

        switch(tool) {
            case 'read_file':
                if (args.bucket && args.filename) {
                    return `Reading ${args.bucket}/${args.filename}`;
                }
                return `Reading file`;
            case 'write_file':
                if (args.bucket && args.filename) {
                    return `Writing to ${args.bucket}/${args.filename}`;
                }
                return `Writing file`;
            case 'append_file':
                if (args.bucket && args.filename) {
                    return `Appending to ${args.bucket}/${args.filename}`;
                }
                return `Appending to file`;
            case 'delete_file':
                if (args.bucket && args.filename) {
                    return `Deleting ${args.bucket}/${args.filename}`;
                }
                return `Deleting file`;
            case 'list_files':
                if (args.bucket) {
                    return `Listing files in ${args.bucket}`;
                }
                return 'Listing all files';
            case 'search_files':
                if (args.query) {
                    return `Searching for "${args.query}"${args.bucket ? ` in ${args.bucket}` : ''}`;
                }
                return 'Searching files';
            default:
                const argCount = Object.keys(args).length;
                return argCount > 0 ? `Called with ${argCount} arguments` : 'Called';
        }
    }

    showToolDetails(element, call) {
        if (!element.classList.contains('expanded')) return;

        // Only add details if not already present
        if (element.querySelector('.tool-call-args')) return;

        // Add arguments section
        if (call.arguments) {
            const argsEl = document.createElement('div');
            argsEl.className = 'tool-call-args';
            argsEl.textContent = JSON.stringify(call.arguments, null, 2);
            element.appendChild(argsEl);
        }

        // Add result section
        if (call.result) {
            const resultEl = document.createElement('div');
            resultEl.className = 'tool-call-result';
            resultEl.textContent = typeof call.result === 'string'
                ? call.result
                : JSON.stringify(call.result, null, 2);

            if (call.result.error || (typeof call.result === 'string' && call.result.includes('Error'))) {
                resultEl.classList.add('error');
            }

            element.appendChild(resultEl);
        }
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