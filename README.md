# Jira MCP Server

A comprehensive Python-based MCP (Model Context Protocol) server for Atlassian Jira that enables AI assistants like Claude to interact with Jira seamlessly. This enterprise-grade solution provides full-featured Jira integration with robust error handling, multiple deployment modes, and extensive tool coverage.

## Features

### Core Issue Management
- **Get detailed issue information** with customizable fields and expansions
- **Create new issues** with full field support and validation
- **Create child issues (subtasks)** with automatic parent linking
- **Update existing issues** with partial field updates and conflict resolution
- **Search issues** using powerful JQL (Jira Query Language) with result formatting
- **List available issue types** for any project with metadata
- **Transition issues** through workflow states with validation

### Advanced Issue Operations
- **Move issues to sprints** (bulk operations up to 50 issues)
- **Link issues** with relationship types (blocks, duplicates, relates to, etc.)
- **Get related issues** and their complete relationship graph
- **Retrieve issue history** and detailed change logs
- **Track workflow transitions** and state changes

### Comments & Time Tracking
- **Add comments** to issues with rich text formatting
- **Retrieve all comments** from issues with threading support
- **Add worklogs** with flexible time tracking and custom start times
- **Time format support** (3h, 30m, 1h 30m, 2d 4h, etc.)
- **Worklog management** with automatic time calculations

### Sprint & Project Management
- **List all sprints** for boards or projects with status filtering
- **Get active sprint** information with issue details
- **Get detailed sprint information** by ID with metrics
- **List project statuses** and available transitions
- **Get boards** with project associations and permissions
- **Sprint analytics** and progress tracking

### Enterprise Features
- **Async/await architecture** for high-performance operations
- **Comprehensive error handling** with detailed debugging information
- **Stdio mode deployment** optimized for MCP clients
- **Docker containerization** with security best practices
- **Environment-based configuration** with validation
- **Rich response formatting** optimized for AI consumption
- **Type safety** with Pydantic models and validation
- **Bulk operations** with progress tracking and error recovery

## Installation

### Prerequisites

- Python 3.11 or higher
- Atlassian account with Jira access
- API token from Atlassian

### Option 1: Using pip (Recommended)

```bash
# Clone the repository
git clone https://github.com/Devparihar5/Jira-MCP-Server.git
cd Jira-MCP-Server

# Create virtual environment
python -m .venv venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using Docker

```bash
# Build the image
docker build -t jira-mcp-python .

# Run with environment variables
docker run --rm -i \
  -e ATLASSIAN_HOST=https://your-company.atlassian.net \
  -e ATLASSIAN_EMAIL=your-email@company.com \
  -e ATLASSIAN_TOKEN=your-api-token \
  jira-mcp-python
```

## Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
ATLASSIAN_HOST=https://your-company.atlassian.net
ATLASSIAN_EMAIL=your-email@company.com
ATLASSIAN_TOKEN=your-api-token
```

### Getting Your API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **"Create API token"**
3. Give it a name like "Jira MCP Python"
4. **Copy the token** (you won't see it again!)

## Usage

### Stdio Mode (Default)

```bash
python main.py --env .env
```

### HTTP Server Mode

```bash
# Start HTTP server on default port 8000
python main.py --http --env .env

# Start HTTP server on custom port
python main.py --http --port 3000 --env .env
```

## Configuration

### Cursor Configuration

#### For Stdio Mode:
```json
{
  "mcpServers": {
    "jira": {
      "command": "python",
      "args": ["/path/to/python-jira-mcp/main.py", "--env", "/path/to/.env"],
      "cwd": "/path/to/python-jira-mcp"
    }
  }
}
```

#### For HTTP Server Mode:
```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything", "http://localhost:8000/sse"]
    }
  }
}
```

#### For Docker (Stdio Mode):
```json
{
  "mcpServers": {
    "jira": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ATLASSIAN_HOST=https://your-company.atlassian.net",
        "-e", "ATLASSIAN_EMAIL=your-email@company.com",
        "-e", "ATLASSIAN_TOKEN=your-api-token",
        "jira-mcp-python"
      ]
    }
  }
}
```

#### For Docker (HTTP Mode):
```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything", "http://localhost:8000/sse"]
    }
  }
}
```

## Available Tools

The Python implementation provides 19 comprehensive tools for complete Jira integration:

### Issue Management Tools
- `get_issue` - Get detailed issue information with customizable fields
- `create_issue` - Create a new issue with full field support
- `create_child_issue` - Create a subtask with automatic parent linking
- `update_issue` - Update issue fields with conflict resolution
- `list_issue_types` - List available issue types for projects
- `transition_issue` - Transition issue through workflow states

### Search & Query Tools
- `search_issues` - Search issues with JQL and advanced filtering

### Sprint Management Tools
- `list_sprints` - List sprints for boards/projects with status filtering
- `get_sprint` - Get detailed sprint information by ID
- `get_active_sprint` - Get currently active sprint with metrics
- `move_issues_to_sprint` - Move multiple issues to sprint (bulk operations)

### Project & Status Tools
- `list_project_statuses` - List available statuses and transitions
- `get_boards` - Get boards with project associations

### Comment & Time Tracking Tools
- `add_comment` - Add comments with rich text formatting
- `get_comments` - Get all comments with threading support
- `add_worklog` - Log time with flexible format support

### Relationship & History Tools
- `link_issues` - Link issues with relationship types
- `get_related_issues` - Get complete relationship graph
- `get_issue_history` - Get detailed change history and transitions

## Usage Examples

Once configured, you can ask Claude to help with Jira tasks:

### Issue Management
- *"Create a new bug ticket for the login issue"*
- *"Show me details for ticket PROJ-123"*
- *"Move ticket PROJ-456 to In Progress"*
- *"Add a comment to PROJ-789 saying the fix is ready"*

### Sprint Management
- *"What's in our current sprint?"*
- *"Move these 3 tickets to the next sprint: PROJ-1, PROJ-2, PROJ-3"*
- *"Show me all tickets assigned to John in the current sprint"*

### Reporting & Analysis
- *"Show me all bugs created this week"*
- *"List all tickets that are blocked"*
- *"What tickets are ready for testing?"*

## Development

### Project Structure

```
jira-mcp/
├── main.py                           # Entry point with stdio/HTTP modes
├── requirements.txt                  # Dependencies
├── .env.example                     # Environment template
├── Dockerfile                       # Docker containerization
├── services/
│   ├── __init__.py
│   └── jira_client.py              # Async Jira API client
├── tools/                          # Comprehensive MCP tools
│   ├── __init__.py                 # Tool registration
│   ├── comprehensive_jira_tools.py # Main tool definitions
│   ├── tool_handlers.py            # Core issue handlers
│   ├── comment_time_handlers.py    # Comment & worklog handlers
│   ├── relationship_history_handlers.py # Link & history handlers
│   ├── sprint_handlers.py          # Sprint management handlers
│   └── project_handlers.py         # Project & status handlers
└── utils/
    ├── __init__.py
    └── jira_formatter.py           # AI-optimized formatting
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run code quality checks
6. Commit your changes (`git commit -m 'feat: add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Atlassian Python API](https://github.com/atlassian-api/atlassian-python-api) for Jira integration
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) for MCP protocol support
