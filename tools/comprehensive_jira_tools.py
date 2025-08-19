"""
Complete Comprehensive Jira MCP Tools Implementation
All features from the original Go implementation with proper organization
"""

from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
from services.jira_client import JiraService

# Import all handlers
from .tool_handlers import (
    handle_get_issue, handle_create_issue, handle_create_child_issue,
    handle_update_issue, handle_search_issues, handle_list_issue_types,
    handle_transition_issue
)
from .comment_time_handlers import (
    handle_add_comment, handle_get_comments, handle_add_worklog
)
from .relationship_history_handlers import (
    handle_link_issues, handle_get_related_issues, handle_get_issue_history
)
from .sprint_handlers import (
    handle_list_sprints, handle_get_active_sprint, handle_get_sprint,
    handle_move_issues_to_sprint
)
from .project_handlers import (
    handle_list_project_statuses, handle_get_boards
)


def register_comprehensive_jira_tools(server: Server, jira_service: JiraService):
    """Register all comprehensive Jira tools with the MCP server."""
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List all available comprehensive Jira tools."""
        return [
            # Issue Management Tools
            Tool(
                name="get_issue",
                description="Get detailed information about a specific Jira issue including status, assignee, description, subtasks, and available transitions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "The Jira issue key (e.g., 'PROJ-123')"},
                        "fields": {"type": "string", "description": "Comma-separated list of fields to retrieve (optional)"},
                        "expand": {"type": "string", "description": "Comma-separated list of fields to expand (optional)"}
                    },
                    "required": ["issue_key"]
                }
            ),
            Tool(
                name="create_issue",
                description="Create a new Jira issue in the specified project with full field support",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {"type": "string", "description": "The project key where the issue will be created"},
                        "summary": {"type": "string", "description": "Brief summary/title of the issue"},
                        "description": {"type": "string", "description": "Detailed description of the issue"},
                        "issue_type": {"type": "string", "description": "Type of issue to create (default: 'Task')"},
                        "priority": {"type": "string", "description": "Priority level (optional)"},
                        "assignee": {"type": "string", "description": "Assignee username or email (optional)"}
                    },
                    "required": ["project_key", "summary", "description"]
                }
            ),
            Tool(
                name="create_child_issue",
                description="Create a child issue (subtask) under an existing parent issue with automatic parent linking",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent_issue_key": {"type": "string", "description": "The key of the parent issue"},
                        "summary": {"type": "string", "description": "Brief summary/title of the child issue"},
                        "description": {"type": "string", "description": "Detailed description of the child issue"},
                        "issue_type": {"type": "string", "description": "Type of child issue (default: 'Sub-task')"}
                    },
                    "required": ["parent_issue_key", "summary", "description"]
                }
            ),
            Tool(
                name="update_issue",
                description="Update an existing Jira issue with partial field updates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "The Jira issue key to update"},
                        "summary": {"type": "string", "description": "New summary/title (optional)"},
                        "description": {"type": "string", "description": "New description (optional)"},
                        "priority": {"type": "string", "description": "New priority (optional)"},
                        "assignee": {"type": "string", "description": "New assignee (optional)"}
                    },
                    "required": ["issue_key"]
                }
            ),
            Tool(
                name="search_issues",
                description="Search for Jira issues using powerful JQL (Jira Query Language)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "jql": {"type": "string", "description": "JQL query string"},
                        "fields": {"type": "string", "description": "Comma-separated list of fields to retrieve (optional)"},
                        "expand": {"type": "string", "description": "Comma-separated list of fields to expand (optional)"},
                        "max_results": {"type": "integer", "description": "Maximum number of results (default: 30, max: 100)"}
                    },
                    "required": ["jql"]
                }
            ),
            Tool(
                name="list_issue_types",
                description="List all available issue types for any project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {"type": "string", "description": "The project key to get issue types for"}
                    },
                    "required": ["project_key"]
                }
            ),
            Tool(
                name="transition_issue",
                description="Transition issues through workflow states",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "The Jira issue key to transition"},
                        "transition_name": {"type": "string", "description": "The name of the transition to perform"}
                    },
                    "required": ["issue_key", "transition_name"]
                }
            ),
            
            # Comments & Time Tracking Tools
            Tool(
                name="add_comment",
                description="Add comments to issues",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "The Jira issue key"},
                        "comment": {"type": "string", "description": "The comment text to add"}
                    },
                    "required": ["issue_key", "comment"]
                }
            ),
            Tool(
                name="get_comments",
                description="Retrieve all comments from issues",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "The Jira issue key"},
                        "max_results": {"type": "integer", "description": "Maximum number of comments to retrieve (default: 20)"}
                    },
                    "required": ["issue_key"]
                }
            ),
            Tool(
                name="add_worklog",
                description="Add worklogs with time tracking and custom start times. Supports flexible time formats (3h, 30m, 1h 30m, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string", "description": "The Jira issue key"},
                        "time_spent": {"type": "string", "description": "Time spent in Jira format (e.g., '3h', '30m', '1h 30m')"},
                        "comment": {"type": "string", "description": "Optional comment describing the work"},
                        "started": {"type": "string", "description": "When work started (ISO format, optional)"}
                    },
                    "required": ["issue_key", "time_spent"]
                }
            ),
            
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
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Handle all comprehensive tool calls with proper routing."""
        
        # Issue Management Tools
        if name == "get_issue":
            return await handle_get_issue(jira_service, arguments)
        elif name == "create_issue":
            return await handle_create_issue(jira_service, arguments)
        elif name == "create_child_issue":
            return await handle_create_child_issue(jira_service, arguments)
        elif name == "update_issue":
            return await handle_update_issue(jira_service, arguments)
        elif name == "search_issues":
            return await handle_search_issues(jira_service, arguments)
        elif name == "list_issue_types":
            return await handle_list_issue_types(jira_service, arguments)
        elif name == "transition_issue":
            return await handle_transition_issue(jira_service, arguments)
        
        # Comments & Time Tracking Tools
        elif name == "add_comment":
            return await handle_add_comment(jira_service, arguments)
        elif name == "get_comments":
            return await handle_get_comments(jira_service, arguments)
        elif name == "add_worklog":
            return await handle_add_worklog(jira_service, arguments)
        
        # Issue Relationships & History Tools
        elif name == "link_issues":
            return await handle_link_issues(jira_service, arguments)
        elif name == "get_related_issues":
            return await handle_get_related_issues(jira_service, arguments)
        elif name == "get_issue_history":
            return await handle_get_issue_history(jira_service, arguments)
        
        # Sprint & Project Management Tools
        elif name == "list_sprints":
            return await handle_list_sprints(jira_service, arguments)
        elif name == "get_active_sprint":
            return await handle_get_active_sprint(jira_service, arguments)
        elif name == "get_sprint":
            return await handle_get_sprint(jira_service, arguments)
        elif name == "move_issues_to_sprint":
            return await handle_move_issues_to_sprint(jira_service, arguments)
        elif name == "list_project_statuses":
            return await handle_list_project_statuses(jira_service, arguments)
        elif name == "get_boards":
            return await handle_get_boards(jira_service, arguments)
        
        else:
            return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
