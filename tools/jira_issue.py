"""
Jira Issue Tools
Tools for managing Jira issues - get, create, update, and list issue types
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from mcp.server import Server
from mcp.types import Tool, TextContent

from services.jira_client import JiraService
from utils.jira_formatter import format_jira_issue


class GetIssueInput(BaseModel):
    issue_key: str = Field(description="The unique identifier of the Jira issue (e.g., KP-2, PROJ-123)")
    fields: Optional[str] = Field(default=None, description="Comma-separated list of fields to retrieve (e.g., 'summary,status,assignee'). If not specified, all fields are returned.")
    expand: Optional[str] = Field(default=None, description="Comma-separated list of fields to expand for additional details (e.g., 'transitions,changelog,subtasks,description').")


class CreateIssueInput(BaseModel):
    project_key: str = Field(description="The project key where the issue will be created (e.g., 'PROJ', 'KP')")
    summary: str = Field(description="Brief summary/title of the issue")
    description: str = Field(description="Detailed description of the issue")
    issue_type: str = Field(description="Type of issue to create (e.g., 'Bug', 'Task', 'Story')")


class CreateChildIssueInput(BaseModel):
    parent_issue_key: str = Field(description="The key of the parent issue (e.g., 'PROJ-123')")
    summary: str = Field(description="Brief summary/title of the child issue")
    description: str = Field(description="Detailed description of the child issue")
    issue_type: Optional[str] = Field(default="Sub-task", description="Type of child issue to create (defaults to 'Sub-task')")


class UpdateIssueInput(BaseModel):
    issue_key: str = Field(description="The unique identifier of the Jira issue to update")
    summary: Optional[str] = Field(default=None, description="New summary/title for the issue")
    description: Optional[str] = Field(default=None, description="New description for the issue")


class ListIssueTypesInput(BaseModel):
    project_key: str = Field(description="The project key to get issue types for (e.g., 'PROJ', 'KP')")


def register_issue_tools(server: Server, jira_service: JiraService):
    """Register all issue-related tools."""
    
    # Define get_issue tool
    get_issue_tool = Tool(
        name="get_issue",
        description="Retrieve detailed information about a specific Jira issue including its status, assignee, description, subtasks, and available transitions",
        inputSchema=GetIssueInput.model_json_schema()
    )
    
    @server.call_tool()
    async def get_issue(arguments: dict) -> List[TextContent]:
        """Get issue handler."""
        try:
            # Validate input
            input_data = GetIssueInput(**arguments)
            
            # Parse fields and expand parameters
            fields = None
            if input_data.fields:
                fields = [f.strip() for f in input_data.fields.split(",")]
            
            expand = ["transitions", "changelog", "subtasks", "description"]
            if input_data.expand:
                expand = [e.strip() for e in input_data.expand.split(",")]
            
            # Get the issue
            issue = await jira_service.get_issue(
                issue_key=input_data.issue_key,
                fields=fields,
                expand=expand
            )
            
            # Format the issue for display
            formatted_issue = format_jira_issue(issue)
            
            return [TextContent(type="text", text=formatted_issue)]
            
        except Exception as e:
            error_msg = f"Failed to get issue {arguments.get('issue_key', 'unknown')}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
    
    # Define create_issue tool
    create_issue_tool = Tool(
        name="create_issue",
        description="Create a new Jira issue in the specified project with the given details",
        inputSchema=CreateIssueInput.model_json_schema()
    )
    
    @server.call_tool()
    async def create_issue(arguments: dict) -> List[TextContent]:
        """Create issue handler."""
        try:
            # Validate input
            input_data = CreateIssueInput(**arguments)
            
            # Create the issue
            result = await jira_service.create_issue(
                project_key=input_data.project_key,
                summary=input_data.summary,
                description=input_data.description,
                issue_type=input_data.issue_type
            )
            
            issue_key = result.get("key", "Unknown")
            issue_id = result.get("id", "Unknown")
            
            success_msg = f"✅ Successfully created issue {issue_key} (ID: {issue_id})\n"
            success_msg += f"📝 Summary: {input_data.summary}\n"
            success_msg += f"🏷️  Type: {input_data.issue_type}\n"
            success_msg += f"📁 Project: {input_data.project_key}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            error_msg = f"Failed to create issue in project {arguments.get('project_key', 'unknown')}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
    
    # Define create_child_issue tool
    create_child_issue_tool = Tool(
        name="create_child_issue",
        description="Create a child issue (subtask) under an existing parent issue",
        inputSchema=CreateChildIssueInput.model_json_schema()
    )
    
    @server.call_tool()
    async def create_child_issue(arguments: dict) -> List[TextContent]:
        """Create child issue handler."""
        try:
            # Validate input
            input_data = CreateChildIssueInput(**arguments)
            
            # Get parent issue to determine project
            parent_issue = await jira_service.get_issue(input_data.parent_issue_key)
            project_key = parent_issue["fields"]["project"]["key"]
            
            # Create the child issue
            result = await jira_service.create_issue(
                project_key=project_key,
                summary=input_data.summary,
                description=input_data.description,
                issue_type=input_data.issue_type,
                parent_key=input_data.parent_issue_key
            )
            
            issue_key = result.get("key", "Unknown")
            issue_id = result.get("id", "Unknown")
            
            success_msg = f"✅ Successfully created child issue {issue_key} (ID: {issue_id})\n"
            success_msg += f"📝 Summary: {input_data.summary}\n"
            success_msg += f"🏷️  Type: {input_data.issue_type}\n"
            success_msg += f"⬆️  Parent: {input_data.parent_issue_key}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            error_msg = f"Failed to create child issue under {arguments.get('parent_issue_key', 'unknown')}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
    
    # Define update_issue tool
    update_issue_tool = Tool(
        name="update_issue",
        description="Update an existing Jira issue with new information",
        inputSchema=UpdateIssueInput.model_json_schema()
    )
    
    @server.call_tool()
    async def update_issue(arguments: dict) -> List[TextContent]:
        """Update issue handler."""
        try:
            # Validate input
            input_data = UpdateIssueInput(**arguments)
            
            # Build update fields
            update_fields = {}
            if input_data.summary:
                update_fields["summary"] = input_data.summary
            if input_data.description:
                update_fields["description"] = input_data.description
            
            if not update_fields:
                return [TextContent(type="text", text="No fields specified for update")]
            
            # Update the issue
            await jira_service.update_issue(
                issue_key=input_data.issue_key,
                fields=update_fields
            )
            
            success_msg = f"✅ Successfully updated issue {input_data.issue_key}\n"
            if input_data.summary:
                success_msg += f"📝 Updated summary: {input_data.summary}\n"
            if input_data.description:
                success_msg += f"📄 Updated description: {input_data.description[:100]}{'...' if len(input_data.description) > 100 else ''}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            error_msg = f"Failed to update issue {arguments.get('issue_key', 'unknown')}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
    
    # Define list_issue_types tool
    list_issue_types_tool = Tool(
        name="list_issue_types",
        description="List all available issue types for a specific project",
        inputSchema=ListIssueTypesInput.model_json_schema()
    )
    
    @server.call_tool()
    async def list_issue_types(arguments: dict) -> List[TextContent]:
        """List issue types handler."""
        try:
            # Validate input
            input_data = ListIssueTypesInput(**arguments)
            
            # Get issue types for the project
            issue_types = await jira_service.get_project_issue_types(input_data.project_key)
            
            if not issue_types:
                return [TextContent(type="text", text=f"No issue types found for project {input_data.project_key}")]
            
            output = [f"📋 **Issue Types for Project {input_data.project_key}**\n"]
            
            for issue_type in issue_types:
                name = issue_type.get("name", "Unknown")
                description = issue_type.get("description", "No description")
                subtask = issue_type.get("subtask", False)
                
                type_indicator = "📋" if subtask else "🎫"
                output.append(f"{type_indicator} **{name}**")
                if description:
                    output.append(f"   {description}")
                output.append("")
            
            return [TextContent(type="text", text="\n".join(output))]
            
        except Exception as e:
            error_msg = f"Failed to get issue types for project {arguments.get('project_key', 'unknown')}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
