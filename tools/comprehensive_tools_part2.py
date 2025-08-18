"""
Comprehensive Jira MCP Tools - Part 2: Additional Tool Definitions
"""

from mcp.types import Tool

def get_additional_tools():
    """Get additional tool definitions for relationships, history, and sprint management."""
    return [
        # Issue Relationships & History Tools
        Tool(
            name="link_issues",
            description="Link issues with relationship types (blocks, duplicates, relates to)",
            inputSchema={
                "type": "object",
                "properties": {
                    "inward_issue": {"type": "string", "description": "The key of the inward issue"},
                    "outward_issue": {"type": "string", "description": "The key of the outward issue"},
                    "link_type": {"type": "string", "description": "Type of link (e.g., 'Blocks', 'Duplicates', 'Relates')"}
                },
                "required": ["inward_issue", "outward_issue", "link_type"]
            }
        ),
        Tool(
            name="get_related_issues",
            description="Get related issues and their relationships",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "The Jira issue key to get related issues for"}
                },
                "required": ["issue_key"]
            }
        ),
        Tool(
            name="get_issue_history",
            description="Retrieve complete issue history and change logs, track issue transitions and workflow changes",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "The Jira issue key"},
                    "max_results": {"type": "integer", "description": "Maximum number of history entries (default: 20)"}
                },
                "required": ["issue_key"]
            }
        ),
        # Sprint & Project Management Tools
        Tool(
            name="list_sprints",
            description="List all sprints for boards or projects with flexible parameter handling",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "integer", "description": "Board ID to get sprints from (optional)"},
                    "project_key": {"type": "string", "description": "Project key to find board and get sprints (alternative to board_id)"},
                    "state": {"type": "string", "description": "Filter sprints by state: 'active', 'closed', 'future' (optional)"}
                },
                "required": []
            }
        ),
        Tool(
            name="get_active_sprint",
            description="Get active sprint information with board and project integration",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "integer", "description": "Board ID (optional)"},
                    "project_key": {"type": "string", "description": "Project key (alternative to board_id)"}
                },
                "required": []
            }
        ),
        Tool(
            name="get_sprint",
            description="Get detailed sprint information by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "sprint_id": {"type": "integer", "description": "The ID of the sprint to retrieve"}
                },
                "required": ["sprint_id"]
            }
        ),
        Tool(
            name="move_issues_to_sprint",
            description="Move issues to sprints with bulk operations support (up to 50 issues at once)",
            inputSchema={
                "type": "object",
                "properties": {
                    "sprint_id": {"type": "integer", "description": "The ID of the sprint to move issues to"},
                    "issue_keys": {"type": "array", "items": {"type": "string"}, "description": "List of issue keys to move"}
                },
                "required": ["sprint_id", "issue_keys"]
            }
        ),
        Tool(
            name="list_project_statuses",
            description="List project statuses and available transitions",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {"type": "string", "description": "The project key to get statuses for"}
                },
                "required": ["project_key"]
            }
        ),
        Tool(
            name="get_boards",
            description="List all boards with automatic discovery for board and project integration",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {"type": "string", "description": "Filter boards by project key (optional)"}
                },
                "required": []
            }
        )
    ]
