# Jira MCP Server - Python Implementation

A Python-based MCP (Model Context Protocol) server for Atlassian Jira that enables AI assistants like Claude to interact with Jira. This is a complete Python rewrite of the original Go implementation, providing the same comprehensive functionality with Python's ecosystem benefits.

## Features

### Issue Management
- **Get detailed issue information** with customizable fields and expansions
- **Create new issues** with full field support
- **Create child issues (subtasks)** with automatic parent linking
- **Update existing issues** with partial field updates
- **Search issues** using powerful JQL (Jira Query Language)
- **List available issue types** for any project
- **Transition issues** through workflow states
- **Move issues to sprints** (up to 50 issues at once)

### Comments & Time Tracking
- **Add comments** to issues
- **Retrieve all comments** from issues
- **Add worklogs** with time tracking and custom start times
- **Flexible time format support** (3h, 30m, 1h 30m, etc.)

### Issue Relationships & History
- **Link issues** with relationship types (blocks, duplicates, relates to)
- **Get related issues** and their relationships
- **Retrieve complete issue history** and change logs
- **Track issue transitions** and workflow changes

### Sprint & Project Management
- **List all sprints** for boards or projects
- **Get active sprint** information
- **Get detailed sprint information** by ID
- **List project statuses** and available transitions
- **Board and project integration** with automatic discovery

### Advanced Features
- **Bulk operations** support (move multiple issues to sprint)
- **Flexible parameter handling** (board_id or project_key)
- **Rich formatting** of responses for AI consumption
- **Error handling** with detailed debugging information
- **Async/await support** for better performance
- **Type safety** with Pydantic models

## Installation

### Prerequisites

- Python 3.11 or higher
- Atlassian account with Jira access
- API token from Atlassian

### Option 1: Using pip (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd python-jira-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

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

### HTTP Mode (for development/testing)

```bash
python main.py --env .env --http-port 3000
```

Then configure your MCP client to connect to `http://localhost:3000/mcp`.

## Cursor Configuration

Add this to your Cursor MCP settings (`.cursor/mcp.json`):

### For Stdio Mode:
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

### For HTTP Mode:
```json
{
  "mcpServers": {
    "jira": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

### For Docker:
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

## Available Tools

The Python implementation provides all the same tools as the Go version:

### Issue Tools
- `get_issue` - Get detailed issue information
- `create_issue` - Create a new issue
- `create_child_issue` - Create a subtask
- `update_issue` - Update issue fields
- `list_issue_types` - List available issue types

### Search Tools
- `search_issue` - Search issues with JQL

### Sprint Tools
- `list_sprints` - List sprints for a board/project
- `get_sprint` - Get detailed sprint information
- `get_active_sprint` - Get currently active sprint
- `move_issues_to_sprint` - Move issues to a sprint

### Status & Transition Tools
- `list_project_statuses` - List available statuses
- `transition_issue` - Transition issue to new status

### Comment Tools
- `add_comment` - Add comment to issue
- `get_comments` - Get all comments from issue

### Worklog Tools
- `add_worklog` - Log time spent on issue

### Relationship Tools
- `link_issues` - Link two issues together
- `get_related_issues` - Get all related issues

### History Tools
- `get_issue_history` - Get complete change history

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
Jira-MCP-Server/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── services/
│   ├── __init__.py
│   └── jira_client.py     # Jira API client
├── tools/                 # MCP tools
│   ├── __init__.py
│   ├── jira_issue.py
│   ├── jira_search.py
│   ├── jira_sprint.py
│   ├── jira_status.py
│   ├── jira_transition.py
│   ├── jira_worklog.py
│   ├── jira_comment.py
│   ├── jira_history.py
│   └── jira_relationship.py
└── utils/
    ├── __init__.py
    └── jira_formatter.py   # Output formatting
```

### Debug Mode

Run with debug logging:

```bash
python main.py --env .env --http-port 3000
```

Then check the console output for detailed error messages.

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
