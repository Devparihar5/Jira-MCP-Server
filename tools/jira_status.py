"""
Jira Status Tools
Tools for managing and viewing issue statuses
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from mcp.server import Server
from mcp.types import Tool, TextContent

from services.jira_client import JiraService


class ListProjectStatusesInput(BaseModel):
    project_key: str = Field(description="The project key to get statuses for (e.g., 'PROJ', 'KP')")


def register_status_tools(server: Server, jira_service: JiraService):
    """Register all status-related tools."""
    
    @server.call_tool()
    async def list_project_statuses(arguments: ListProjectStatusesInput) -> List[TextContent]:
        """List all available statuses for a specific project, organized by issue type."""
        try:
            # Get project statuses
            statuses = await jira_service.get_project_statuses(arguments.project_key)
            
            if not statuses:
                return [TextContent(type="text", text=f"No statuses found for project {arguments.project_key}")]
            
            # Format the results
            output = []
            output.append(f"📊 **Statuses for Project {arguments.project_key}**\n")
            
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
                        
                        # Add spacing between statuses
                        if i < len(statuses_list) - 1:
                            output.append("")
                else:
                    output.append("   No statuses available")
                
                # Add spacing between issue types
                output.append("\n" + "-"*40 + "\n")
            
            return [TextContent(type="text", text="\n".join(output))]
            
        except Exception as e:
            error_msg = f"Failed to get statuses for project {arguments.project_key}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
