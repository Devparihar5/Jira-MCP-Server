"""
Sprint and Project Management Tool Handlers
"""

from typing import Any, Dict, List, Optional, Sequence
from mcp.types import TextContent
from services.jira_client import JiraService
from utils.jira_formatter import format_jira_sprint, format_jira_issue


async def _get_board_id_from_project(jira_service: JiraService, project_key: str) -> Optional[int]:
    """Helper function to get board ID from project key."""
    try:
        boards_response = await jira_service.get_boards()
        boards = boards_response.get("values", [])
        
        for board in boards:
            location = board.get("location", {})
            if location.get("projectKey") == project_key:
                return board.get("id")
        
        # If no exact match, try to find a board that might be related
        for board in boards:
            board_name = board.get("name", "").lower()
            if project_key.lower() in board_name:
                return board.get("id")
        
        return None
    except Exception:
        return None


async def handle_list_sprints(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle list_sprints tool call."""
    try:
        board_id = arguments.get("board_id")
        project_key = arguments.get("project_key")
        state = arguments.get("state")
        
        # If no board_id provided, try to get it from project_key
        if not board_id and project_key:
            board_id = await _get_board_id_from_project(jira_service, project_key)
            if not board_id:
                return [TextContent(type="text", text=f"Could not find a board for project {project_key}")]
        
        if not board_id:
            return [TextContent(type="text", text="Either board_id or project_key must be provided")]
        
        sprints_response = await jira_service.get_board_sprints(board_id=board_id, state=state)
        sprints = sprints_response.get("values", [])
        
        if not sprints:
            state_filter = f" with state '{state}'" if state else ""
            return [TextContent(type="text", text=f"No sprints found for board {board_id}{state_filter}")]
        
        output = []
        state_filter = f" ({state})" if state else ""
        output.append(f"🏃 **Sprints for Board {board_id}{state_filter}**\n")
        
        for i, sprint in enumerate(sprints):
            formatted_sprint = format_jira_sprint(sprint)
            output.append(formatted_sprint)
            
            if i < len(sprints) - 1:
                output.append("\n" + "-"*30 + "\n")
        
        return [TextContent(type="text", text="\n".join(output))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to list sprints: {str(e)}")]


async def handle_get_active_sprint(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle get_active_sprint tool call."""
    try:
        board_id = arguments.get("board_id")
        project_key = arguments.get("project_key")
        
        # If no board_id provided, try to get it from project_key
        if not board_id and project_key:
            board_id = await _get_board_id_from_project(jira_service, project_key)
            if not board_id:
                return [TextContent(type="text", text=f"Could not find a board for project {project_key}")]
        
        if not board_id:
            return [TextContent(type="text", text="Either board_id or project_key must be provided")]
        
        sprints_response = await jira_service.get_board_sprints(board_id=board_id, state="active")
        sprints = sprints_response.get("values", [])
        
        if not sprints:
            return [TextContent(type="text", text=f"No active sprint found for board {board_id}")]
        
        # Get the first active sprint (there should typically be only one)
        active_sprint = sprints[0]
        sprint_id = active_sprint.get("id")
        
        # Get detailed sprint information with issues
        return await handle_get_sprint(jira_service, {"sprint_id": sprint_id})
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to get active sprint: {str(e)}")]


async def handle_get_sprint(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle get_sprint tool call."""
    try:
        sprint_id = arguments.get("sprint_id")
        if not sprint_id:
            return [TextContent(type="text", text="❌ sprint_id is required")]
        
        # Get sprint details
        sprint = await jira_service.get_sprint(sprint_id)
        
        # Get issues in the sprint
        sprint_issues_response = await jira_service.get_sprint_issues(sprint_id)
        issues = sprint_issues_response.get("issues", [])
        
        output = []
        formatted_sprint = format_jira_sprint(sprint)
        output.append(formatted_sprint)
        
        # Add issues in the sprint
        if issues:
            output.append(f"\n📋 **Issues in Sprint ({len(issues)} total)**\n")
            
            for i, issue in enumerate(issues):
                key = issue.get("key", "Unknown")
                fields = issue.get("fields", {})
                summary = fields.get("summary", "No summary")
                status = fields.get("status", {}).get("name", "Unknown")
                assignee = fields.get("assignee")
                assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
                
                output.append(f"  {i+1}. **{key}**: {summary}")
                output.append(f"     📊 Status: {status} | 👤 Assignee: {assignee_name}")
                
                if i < len(issues) - 1:
                    output.append("")
        else:
            output.append("\n📋 **No issues in this sprint**")
        
        return [TextContent(type="text", text="\n".join(output))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to get sprint: {str(e)}")]


async def handle_move_issues_to_sprint(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle move_issues_to_sprint tool call."""
    try:
        sprint_id = arguments.get("sprint_id")
        issue_keys = arguments.get("issue_keys", [])
        
        if not sprint_id:
            return [TextContent(type="text", text="❌ sprint_id is required")]
        
        if not issue_keys:
            return [TextContent(type="text", text="❌ issue_keys list is required")]
        
        # Limit the number of issues to prevent overwhelming the API
        if len(issue_keys) > 50:
            return [TextContent(type="text", text="❌ Cannot move more than 50 issues at once. Please split into smaller batches.")]
        
        await jira_service.move_issues_to_sprint(sprint_id=sprint_id, issue_keys=issue_keys)
        
        issue_list = ", ".join(issue_keys)
        success_msg = f"✅ Successfully moved {len(issue_keys)} issue{'s' if len(issue_keys) != 1 else ''} to sprint {sprint_id}\n"
        success_msg += f"📋 Issues moved: {issue_list}"
        
        return [TextContent(type="text", text=success_msg)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to move issues to sprint: {str(e)}")]
