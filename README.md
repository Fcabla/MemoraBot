# 🗂️ **MemoraBot** – Your AI File & Note Assistant

**MemoraBot** is an intelligent agent designed to organize, manage, and interact with your files and notes — all through natural language.
It acts as a **memory-focused assistant** that can **read, create, edit, append, and delete files**, organizing information in "buckets" for easy access.

The goal is to provide a conversational AI that **actively manages your knowledge**, similar to how coding assistants help developers, but focused on general information and note handling.

---

## 🚀 Features

* **Natural language interface** – interact with MemoraBot via chat
* **Smart file organization** – dynamically creates "buckets" (files) if none exist
* **Read & search** – finds relevant files before creating new ones
* **Append & edit** – updates existing files intelligently
* **File lifecycle management** – can create, edit, append, and delete files
* **Memory-driven logic** – keeps track of categories and previous actions
* **Extensible design** – easy to add new tools or behaviors

---

## 🎨 User Interface

The application features a clean, chat-focused interface built with Jinja2 templates that provides:

### Main Chat Interface
* **Chat Display Area**: A scrollable message container that shows the complete conversation history
* **Message Types**: All interactions are displayed transparently, including:
  - User messages and inputs
  - MemoraBot responses and confirmations
  - Tool calls (file operations like read, write, edit, delete)
  - Tool responses and results
  - Error messages and system notifications

### Interactive Controls
* **Text Input Area**: A multiline text area where users can type natural language commands and notes
* **Submit Button**: Sends messages to MemoraBot for processing
* **Real-time Updates**: The interface updates dynamically as MemoraBot processes requests and executes file operations

### Conversation Transparency
The UI is designed with full transparency in mind - users can see exactly what MemoraBot is doing behind the scenes. When MemoraBot needs to read a file, create a new bucket, or edit existing content, these tool calls and their responses are displayed in the chat area alongside regular conversation messages. This helps users understand the agent's decision-making process and builds trust in the system.

The interface serves as both a chat application and a comprehensive log of all file operations, making it easy to track what changes have been made to your knowledge base over time.

---

## 🏗️ Tech Stack

* **Python** – core application logic
* **[pydanticAI](https://ai.pydantic.dev/)** – agent orchestration, LLM interaction, and tool definitions
* **FastAPI** – API layer for the chat interaction
* **Jinja2** – server-side rendering for a lightweight frontend
* **uv** – fast Python package manager for dependency handling

---

## 📂 Project Structure (Proposed)

```
memorabot/
│
├── app/
│   ├── main.py            # FastAPI entrypoint
│   ├── agents.py          # MemoraBot logic and pydanticAI setup
│   ├── tools.py           # File manipulation tools (read, write, edit, delete)
│   ├── schemas.py         # Pydantic models for requests/responses
│   └── utils.py           # Helpers for file discovery & categorization
│
├── templates/             # Jinja2 templates (chat interface)
│   └── index.html         # Main chat UI template
│
├── data/                  # Storage folder for "buckets" (created dynamically)
│
├── tests/                 # Unit tests
│
├── pyproject.toml         # uv-managed dependencies
└── README.md
```

---

## 🧠 How MemoraBot Works

1. **User sends a message** describing an idea, note, or instruction.
2. **MemoraBot decides** whether to create, edit, or delete a file based on existing buckets.
3. **Tools are called** via `pydanticAI` to perform the necessary file operations.
4. **Response is rendered** back to the chat, showing the result of the action.
5. **Planning agent integration** – All conversation data (including tool calls and responses) is logged and can be fed to a planning agent for advanced workflow optimization.

> MemoraBot always tries to **reuse existing files** intelligently before creating new ones, keeping your "memory" organized.

---

## 🔄 Planning Agent Integration

The chat interface is designed to capture comprehensive interaction data that can be fed to a planning agent:

* **Complete conversation logs** including user inputs, agent responses, and all tool interactions
* **File operation history** showing what files were created, modified, or deleted
* **Decision traces** revealing MemoraBot's reasoning for file organization choices
* **Performance metrics** such as response times and successful operation counts

This rich dataset enables the planning agent to:
- Optimize file organization strategies
- Predict user needs based on conversation patterns
- Suggest improvements to MemoraBot's decision-making processes
- Automate routine knowledge management tasks

---

## 🧩 Future Ideas

* ✨ File explorer in a sidebar (explore data/)
* ✨ Handle structured note formats (Markdown, YAML, JSON)
* ✨ Versioning & undo actions for safety
* ✨ Advanced search and filtering capabilities
* ✨ Integration with external note-taking systems
* ✨ Export/import functionality for knowledge migration