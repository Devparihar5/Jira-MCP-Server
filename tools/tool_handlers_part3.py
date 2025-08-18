"""
Comprehensive Tool Handlers - Part 3: Sprint and Project Management
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


async def handle_list_project_statuses(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle list_project_statuses tool call."""
    try:
        project_key = arguments.get("project_key")
        if not project_key:
            return [TextContent(type="text", text="❌ project_key is required")]
        
        statuses = await jira_service.get_project_statuses(project_key)
        
        if not statuses:
            return [TextContent(type="text", text=f"No statuses found for project {project_key}")]
        
        output = [f"📊 **Statuses for Project {project_key}**\n"]
        
        for status_group in statuses:
            # Get issue type information
            issue_type = status_group.get("issueType", {})
            issue_type_name = issue_type.get("name", "Unknown")
            issue_type_description = issue_type.get("description", "")
            
            # Add issue type header
            output.append(f"🏷️  **{issue_type_name}**")
            if issue_type_description:
                output.append(f"   {issue_type_description}")
            output.append("")
            
            # List statuses for this issue type
            statuses_list = status_group.get("statuses", [])
            if statuses_list:
                for i, status in enumerate(statuses_list):
                    name = status.get("name", "Unknown")
                    description = status.get("description", "")
                    category = status.get("statusCategory", {}).get("name", "")
                    
                    # Use different icons based on status category
                    if category == "Done":
                        icon = "✅"
                    elif category == "In Progress":
                        icon = "🔄"
                    elif category == "To Do":
                        icon = "📋"
                    else:
                        icon = "📊"
                    
                    output.append(f"   {icon} **{name}**")
                    if description:
                        output.append(f"      {description}")
                    if category:
                        output.append(f"      Category: {category}")
                    
                    if i < len(statuses_list) - 1:
                        output.append("")
            else:
                output.append("   No statuses available")
            
            output.append("\n" + "-"*40 + "\n")
        
        return [TextContent(type="text", text="\n".join(output))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to get project statuses: {str(e)}")]


async def handle_get_boards(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle get_boards tool call."""
    try:
        project_key = arguments.get("project_key")
        
        boards_response = await jira_service.get_boards()
        boards = boards_response.get("values", [])
        
        if not boards:
            return [TextContent(type="text", text="No boards found")]
        
        # Filter by project if specified
        if project_key:
            filtered_boards = []
            for board in boards:
                location = board.get("location", {})
                if location.get("projectKey") == project_key:
                    filtered_boards.append(board)
            boards = filtered_boards
            
            if not boards:
                return [TextContent(type="text", text=f"No boards found for project {project_key}")]
        
        output = []
        if project_key:
            output.append(f"📋 **Boards for Project {project_key}**\n")
        else:
            output.append(f"📋 **All Boards ({len(boards)} total)**\n")
        
        for i, board in enumerate(boards):
            board_id = board.get("id", "Unknown")
            name = board.get("name", "Unnamed Board")
            board_type = board.get("type", "Unknown")
            location = board.get("location", {})
            project_name = location.get("projectName", "Unknown Project")
            project_key_board = location.get("projectKey", "Unknown")
            
            output.append(f"{i+1}. **{name}** (ID: {board_id})")
            output.append(f"   📊 Type: {board_type}")
            output.append(f"   📁 Project: {project_name} ({project_key_board})")
            
            if i < len(boards) - 1:
                output.append("")
        
        return [TextContent(type="text", text="\n".join(output))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to get boards: {str(e)}")]
