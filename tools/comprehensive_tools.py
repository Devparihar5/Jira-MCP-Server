"""
Comprehensive Jira MCP Tools Implementation
All features from the original Go implementation
"""

from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
from services.jira_client import JiraService
from utils.jira_formatter import format_jira_issue, format_jira_sprint, format_jira_comment, format_jira_worklog, format_issue_link, format_changelog_entry


def register_comprehensive_tools(server: Server, jira_service: JiraService):
    """Register all comprehensive Jira tools."""
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List all available Jira tools."""
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
            )
        ]
