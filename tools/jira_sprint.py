"""
Jira Sprint Tools
Tools for managing sprints - list, get details, and move issues to sprints
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from mcp.server import Server
from mcp.types import Tool, TextContent

from services.jira_client import JiraService
from utils.jira_formatter import format_jira_sprint, format_jira_issue


class ListSprintsInput(BaseModel):
    board_id: Optional[int] = Field(default=None, description="Board ID to get sprints from")
    project_key: Optional[str] = Field(default=None, description="Project key to find board and get sprints (alternative to board_id)")
    state: Optional[str] = Field(default=None, description="Filter sprints by state: 'active', 'closed', 'future'")


class GetSprintInput(BaseModel):
    sprint_id: int = Field(description="The ID of the sprint to retrieve")


class GetActiveSprintInput(BaseModel):
    board_id: Optional[int] = Field(default=None, description="Board ID to get active sprint from")
    project_key: Optional[str] = Field(default=None, description="Project key to find board and get active sprint (alternative to board_id)")


class MoveIssuesToSprintInput(BaseModel):
    sprint_id: int = Field(description="The ID of the sprint to move issues to")
    issue_keys: List[str] = Field(description="List of issue keys to move to the sprint (e.g., ['PROJ-1', 'PROJ-2'])")


def register_sprint_tools(server: Server, jira_service: JiraService):
    """Register all sprint-related tools."""
    
    async def _get_board_id_from_project(project_key: str) -> Optional[int]:
        """Helper function to get board ID from project key."""
        try:
            boards_response = await jira_service.get_boards()
            boards = boards_response.get("values", [])
            
            for board in boards:
                # Check if this board is associated with the project
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
    
    @server.call_tool()
    async def list_sprints(arguments: ListSprintsInput) -> List[TextContent]:
        """List all sprints for a board or project, optionally filtered by state (active, closed, future)."""
        try:
            board_id = arguments.board_id
            
            # If no board_id provided, try to get it from project_key
            if not board_id and arguments.project_key:
                board_id = await _get_board_id_from_project(arguments.project_key)
                if not board_id:
                    return [TextContent(type="text", text=f"Could not find a board for project {arguments.project_key}")]
            
            if not board_id:
                return [TextContent(type="text", text="Either board_id or project_key must be provided")]
            
            # Get sprints for the board
            sprints_response = await jira_service.get_board_sprints(
                board_id=board_id,
                state=arguments.state
            )
            
            sprints = sprints_response.get("values", [])
            
            if not sprints:
                state_filter = f" with state '{arguments.state}'" if arguments.state else ""
                return [TextContent(type="text", text=f"No sprints found for board {board_id}{state_filter}")]
            
            # Format the results
            output = []
            
            # Add header
            state_filter = f" ({arguments.state})" if arguments.state else ""
            output.append(f"🏃 **Sprints for Board {board_id}{state_filter}**\n")
            
            # Format each sprint
            for i, sprint in enumerate(sprints):
                formatted_sprint = format_jira_sprint(sprint)
                output.append(formatted_sprint)
                
                # Add separator between sprints (except for the last one)
                if i < len(sprints) - 1:
                    output.append("\n" + "-"*30 + "\n")
            
            return [TextContent(type="text", text="\n".join(output))]
            
        except Exception as e:
            error_msg = f"Failed to list sprints: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
    
    @server.call_tool()
    async def get_sprint(arguments: GetSprintInput) -> List[TextContent]:
        """Get detailed information about a specific sprint including its issues."""
        try:
            # Get sprint details
            sprint = await jira_service.get_sprint(arguments.sprint_id)
            
            # Get issues in the sprint
            sprint_issues_response = await jira_service.get_sprint_issues(arguments.sprint_id)
            issues = sprint_issues_response.get("issues", [])
            
            # Format the sprint
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
            error_msg = f"Failed to get sprint {arguments.sprint_id}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
    
    @server.call_tool()
    async def get_active_sprint(arguments: GetActiveSprintInput) -> List[TextContent]:
        """Get the currently active sprint for a board or project."""
        try:
            board_id = arguments.board_id
            
            # If no board_id provided, try to get it from project_key
            if not board_id and arguments.project_key:
                board_id = await _get_board_id_from_project(arguments.project_key)
                if not board_id:
                    return [TextContent(type="text", text=f"Could not find a board for project {arguments.project_key}")]
            
            if not board_id:
                return [TextContent(type="text", text="Either board_id or project_key must be provided")]
            
            # Get active sprints for the board
            sprints_response = await jira_service.get_board_sprints(
                board_id=board_id,
                state="active"
            )
            
            sprints = sprints_response.get("values", [])
            
            if not sprints:
                return [TextContent(type="text", text=f"No active sprint found for board {board_id}")]
            
            # Get the first active sprint (there should typically be only one)
            active_sprint = sprints[0]
            sprint_id = active_sprint.get("id")
            
            # Get detailed sprint information with issues
            return await get_sprint(GetSprintInput(sprint_id=sprint_id))
            
        except Exception as e:
            error_msg = f"Failed to get active sprint: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
    
    @server.call_tool()
    async def move_issues_to_sprint(arguments: MoveIssuesToSprintInput) -> List[TextContent]:
        """Move multiple issues to a specific sprint (up to 50 issues at once)."""
        try:
            # Limit the number of issues to prevent overwhelming the API
            if len(arguments.issue_keys) > 50:
                return [TextContent(type="text", text="Cannot move more than 50 issues at once. Please split into smaller batches.")]
            
            if not arguments.issue_keys:
                return [TextContent(type="text", text="No issue keys provided")]
            
            # Move issues to sprint
            await jira_service.move_issues_to_sprint(
                sprint_id=arguments.sprint_id,
                issue_keys=arguments.issue_keys
            )
            
            # Format success message
            issue_list = ", ".join(arguments.issue_keys)
            success_msg = f"✅ Successfully moved {len(arguments.issue_keys)} issue{'s' if len(arguments.issue_keys) != 1 else ''} to sprint {arguments.sprint_id}\n"
            success_msg += f"📋 Issues moved: {issue_list}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            error_msg = f"Failed to move issues to sprint {arguments.sprint_id}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
