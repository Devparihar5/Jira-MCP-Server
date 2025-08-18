"""
Project Management Tool Handlers
"""

from typing import Any, Dict, List, Optional, Sequence
from mcp.types import TextContent
from services.jira_client import JiraService


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
