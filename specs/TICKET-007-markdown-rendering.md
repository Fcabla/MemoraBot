# TICKET-007: Markdown Rendering in Chat

**Status:** TODO
**Phase:** 3 - Enhanced File Management
**Priority:** High
**Estimated Effort:** 0.5 day
**Dependencies:** TICKET-005 (COMPLETED)

## Detail Section

### Purpose
Add markdown rendering capabilities to the chat interface so agent responses display with proper formatting (headers, lists, code blocks, links, etc.) while maintaining tool call transparency and existing functionality.

### Business Value
- **Better Readability**: Agent responses look professional and formatted
- **Improved User Experience**: Lists, headers, and code blocks display properly
- **Maintained Transparency**: Tool calls still show clearly alongside formatted content
- **Quick Implementation**: Leverages existing chat.js infrastructure

### Acceptance Criteria
- [ ] Agent responses render markdown formatting (headers, lists, links, code blocks)
- [ ] Tool calls remain visually distinct and unaffected by markdown rendering
- [ ] Code syntax highlighting for common languages
- [ ] Preserve existing chat functionality (timestamps, themes, etc.)
- [ ] Handle mixed content (markdown + tool calls in same response)
- [ ] Graceful fallback if markdown parsing fails

## Implementation Section

### Technical Approach
Use **markdown-it.js** library to parse and render markdown in agent messages while preserving the existing chat interface and tool call display system.

### Files to Create/Modify

#### 1. Update `/templates/chat.html` - Add Markdown Library

Add markdown-it CDN and syntax highlighting:

```html
{% block extra_head %}
<!-- Existing icon styles -->
<style>
    .icon-user::before { content: "👤"; }
    .icon-bot::before { content: "🤖"; }
    .icon-tool::before { content: "🔧"; }
    .icon-file::before { content: "📄"; }
    .icon-folder::before { content: "📁"; }
    .icon-search::before { content: "🔍"; }
    .icon-write::before { content: "✏️"; }
    .icon-delete::before { content: "🗑️"; }
</style>

<!-- Markdown rendering libraries -->
<script src="https://cdn.jsdelivr.net/npm/markdown-it@14.0.0/dist/markdown-it.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/highlight.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github.min.css" media="screen and (prefers-color-scheme: light)">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github-dark.min.css" media="screen and (prefers-color-scheme: dark)">

<!-- Markdown-specific styles -->
<style>
    /* Markdown content styling */
    .message-content.markdown {
        line-height: 1.6;
    }

    .message-content.markdown h1,
    .message-content.markdown h2,
    .message-content.markdown h3,
    .message-content.markdown h4,
    .message-content.markdown h5,
    .message-content.markdown h6 {
        margin: 1em 0 0.5em 0;
        font-weight: 600;
    }

    .message-content.markdown h1 { font-size: 1.5em; }
    .message-content.markdown h2 { font-size: 1.3em; }
    .message-content.markdown h3 { font-size: 1.1em; }

    .message-content.markdown ul,
    .message-content.markdown ol {
        margin: 0.5em 0;
        padding-left: 1.5em;
    }

    .message-content.markdown li {
        margin: 0.25em 0;
    }

    .message-content.markdown p {
        margin: 0.5em 0;
    }

    .message-content.markdown code {
        background: rgba(175, 184, 193, 0.2);
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-size: 0.9em;
        font-family: 'Courier New', monospace;
    }

    .message-content.markdown pre {
        background: var(--tool-bg);
        border: 1px solid var(--tool-border);
        border-radius: 6px;
        padding: 1em;
        margin: 1em 0;
        overflow-x: auto;
    }

    .message-content.markdown pre code {
        background: none;
        padding: 0;
        font-size: 0.85em;
    }

    .message-content.markdown blockquote {
        border-left: 3px solid var(--primary-color);
        margin: 1em 0;
        padding-left: 1em;
        font-style: italic;
        color: var(--text-secondary);
    }

    .message-content.markdown a {
        color: var(--primary-color);
        text-decoration: none;
    }

    .message-content.markdown a:hover {
        text-decoration: underline;
    }

    .message-content.markdown table {
        border-collapse: collapse;
        margin: 1em 0;
        width: 100%;
    }

    .message-content.markdown th,
    .message-content.markdown td {
        border: 1px solid var(--border-color);
        padding: 0.5em;
        text-align: left;
    }

    .message-content.markdown th {
        background: var(--tool-bg);
        font-weight: 600;
    }

    /* Dark mode adjustments */
    [data-theme="dark"] .message-content.markdown code {
        background: rgba(255, 255, 255, 0.1);
    }
</style>
{% endblock %}
```

#### 2. Update `/static/js/chat.js` - Add Markdown Processing

Enhance the `ChatInterface` class with markdown rendering:

```javascript
class ChatInterface {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.conversationId = this.generateConversationId();
        this.isProcessing = false;

        // Initialize markdown parser
        this.initializeMarkdown();

        this.initializeEventListeners();
        this.updateTimestamps();
        setInterval(() => this.updateTimestamps(), 60000);
    }

    initializeMarkdown() {
        // Configure markdown-it with syntax highlighting
        this.md = window.markdownit({
            html: false,        // Don't allow raw HTML for security
            xhtmlOut: true,     // Use XHTML-style tags
            breaks: true,       // Convert line breaks to <br>
            linkify: true,      // Auto-convert URLs to links
            typographer: true,  // Enable smart quotes and other typographic replacements
            highlight: function (str, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(str, { language: lang }).value;
                    } catch (__) {}
                }
                return ''; // Use external default escaping
            }
        });

        // Add plugins for enhanced functionality
        if (window.markdownitTaskLists) {
            this.md.use(window.markdownitTaskLists);
        }
    }

    addMessage(role, content, toolCalls = null) {
        const template = document.getElementById(`${role}MessageTemplate`);
        if (!template) {
            console.error(`Template not found for role: ${role}`);
            return;
        }

        const message = template.cloneNode(true);
        message.id = '';
        message.style.display = '';

        // Set content with markdown rendering for assistant messages
        const contentEl = message.querySelector('.message-content');
        if (contentEl) {
            if (role === 'assistant' && this.shouldRenderAsMarkdown(content)) {
                // Render as markdown
                contentEl.innerHTML = this.md.render(content);
                contentEl.classList.add('markdown');
            } else {
                // Plain text for user messages and non-markdown content
                contentEl.textContent = content;
            }
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

    shouldRenderAsMarkdown(content) {
        // Detect if content contains markdown syntax
        const markdownIndicators = [
            /^#{1,6}\s/m,           // Headers
            /^\s*[\*\+\-]\s/m,      // Unordered lists
            /^\s*\d+\.\s/m,         // Ordered lists
            /\*\*.*\*\*/,           // Bold text
            /\*.*\*/,               // Italic text
            /`.*`/,                 // Inline code
            /```[\s\S]*```/,        // Code blocks
            /^\s*>/m,               // Blockquotes
            /\[.*\]\(.*\)/,         // Links
        ];

        return markdownIndicators.some(regex => regex.test(content));
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
        // Note: Tool calls should NOT be rendered as markdown - keep as-is

        toolCalls.forEach(call => {
            const toolCall = this.createToolCallElement(call);
            content.appendChild(toolCall);
        });

        container.appendChild(content);
        this.chatMessages.appendChild(container);
        this.scrollToBottom();
    }

    // ... rest of existing methods remain unchanged
}
```

#### 3. Add Markdown Processing Utilities to `/static/js/main.js`

```javascript
// Markdown-related utility functions

/**
 * Sanitize markdown content for safe rendering
 */
function sanitizeMarkdown(content) {
    // Remove potentially dangerous HTML tags while preserving markdown
    const dangerousTags = /<script|<iframe|<object|<embed|<link|<meta/gi;
    return content.replace(dangerousTags, '');
}

/**
 * Extract and format code blocks from markdown
 */
function extractCodeBlocks(content) {
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)\n```/g;
    const blocks = [];
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
        blocks.push({
            language: match[1] || 'text',
            code: match[2],
            fullMatch: match[0]
        });
    }

    return blocks;
}

/**
 * Convert plain text to markdown-friendly format
 */
function textToMarkdown(text) {
    return text
        .replace(/\n\n/g, '\n\n')  // Preserve paragraph breaks
        .replace(/\n/g, '\n')      // Preserve line breaks
        .trim();
}

/**
 * Copy formatted content to clipboard
 */
async function copyFormattedContent(element) {
    try {
        // Get both plain text and HTML
        const plainText = element.textContent;
        const htmlContent = element.innerHTML;

        if (navigator.clipboard && navigator.clipboard.write) {
            // Modern browsers - copy both formats
            await navigator.clipboard.write([
                new ClipboardItem({
                    'text/plain': new Blob([plainText], { type: 'text/plain' }),
                    'text/html': new Blob([htmlContent], { type: 'text/html' })
                })
            ]);
        } else {
            // Fallback - copy plain text only
            await navigator.clipboard.writeText(plainText);
        }

        showToast('Content copied to clipboard', 'success');
        return true;
    } catch (err) {
        console.error('Failed to copy formatted content:', err);
        showToast('Failed to copy content', 'error');
        return false;
    }
}
```

#### 4. Optional: Enhanced Markdown Features

If you want to add more advanced markdown features later, create `/static/js/markdown-extensions.js`:

```javascript
// Additional markdown extensions

/**
 * Add task list support (if markdown-it-task-lists is not available)
 */
function initializeTaskLists() {
    if (!window.markdownitTaskLists) {
        // Simple task list parsing
        return function(md) {
            md.core.ruler.after('inline', 'task-lists', function(state) {
                const tokens = state.tokens;
                for (let i = 0; i < tokens.length; i++) {
                    const token = tokens[i];
                    if (token.type === 'inline' && token.content) {
                        // Replace task list syntax
                        token.content = token.content
                            .replace(/^\- \[ \] /gm, '☐ ')
                            .replace(/^\- \[x\] /gim, '☑ ');
                    }
                }
            });
        };
    }
    return window.markdownitTaskLists;
}

/**
 * Add file link support for MemoraBot
 */
function addFileLinkSupport() {
    return function(md) {
        md.core.ruler.after('inline', 'file-links', function(state) {
            const tokens = state.tokens;
            for (let i = 0; i < tokens.length; i++) {
                const token = tokens[i];
                if (token.type === 'inline' && token.content) {
                    // Replace file references like {{bucket/filename}}
                    token.content = token.content.replace(
                        /\{\{([^}]+)\}\}/g,
                        '<span class="file-reference" data-file="$1">📄 $1</span>'
                    );
                }
            }
        });
    };
}
```

### Usage Examples

Once implemented, the agent can respond with formatted markdown:

```markdown
I've updated your shopping list! Here's what I added:

## Shopping List
- ✅ Milk (organic)
- ✅ Bread
- 🆕 **Eggs** (added)
- 🆕 **Butter** (added)

### Next Steps
You might also want to add:
1. Check if you need vegetables
2. Review your meal plan for the week

> **Tip**: I can help organize your meals by day if you'd like!

```

The above would render with proper headers, checkmarks, bold text, lists, and blockquotes.

### Testing Steps

1. **Test basic markdown rendering**:
   - Send agent message with headers, lists, bold/italic text
   - Verify proper HTML rendering in chat

2. **Test code block rendering**:
   - Include code blocks in agent responses
   - Verify syntax highlighting works

3. **Test mixed content**:
   - Agent response with both markdown and tool calls
   - Ensure tool calls remain unaffected

4. **Test fallback behavior**:
   - Invalid markdown syntax
   - Ensure graceful degradation

### Verification Checklist
- [ ] Headers (h1-h6) render with proper sizing
- [ ] Lists (ordered/unordered) display correctly
- [ ] Code blocks have syntax highlighting
- [ ] Links are clickable and styled
- [ ] Bold/italic formatting works
- [ ] Tool calls remain visually distinct
- [ ] Theme switching affects markdown styles
- [ ] Copy functionality preserves formatting
- [ ] No security issues with HTML injection

### Related Files
- `/templates/chat.html` - Markdown library inclusion and styles
- `/static/js/chat.js` - Core markdown processing logic
- `/static/js/main.js` - Utility functions
- `/static/css/main.css` - Existing styles (compatible with markdown)

### Performance Considerations
- Markdown-it library is ~90KB minified (acceptable for this feature)
- Rendering is client-side, no server performance impact
- Syntax highlighting adds ~30KB but significantly improves code display

### Next Steps
After completion, proceed to TICKET-008 for file system monitoring API.