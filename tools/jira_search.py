"""
Jira Search Tools
Tools for searching Jira issues using JQL (Jira Query Language)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from mcp.server import Server
from mcp.types import Tool, TextContent

from services.jira_client import JiraService
from utils.jira_formatter import format_jira_issue


class SearchIssueInput(BaseModel):
    jql: str = Field(description="JQL query string (e.g., 'project = KP AND status = \"In Progress\"')")
    fields: Optional[str] = Field(default=None, description="Comma-separated list of fields to retrieve (e.g., 'summary,status,assignee'). If not specified, all fields are returned.")
    expand: Optional[str] = Field(default=None, description="Comma-separated list of fields to expand for additional details (e.g., 'transitions,changelog,subtasks,description').")
    max_results: Optional[int] = Field(default=30, description="Maximum number of results to return (default: 30, max: 100)")


def register_search_tools(server: Server, jira_service: JiraService):
    """Register all search-related tools."""
    
    @server.call_tool()
    async def search_issue(arguments: SearchIssueInput) -> List[TextContent]:
        """Search for Jira issues using JQL (Jira Query Language). Returns key details like summary, status, assignee, and priority for matching issues."""
        try:
            # Parse fields and expand parameters
            fields = None
            if arguments.fields:
                fields = [f.strip() for f in arguments.fields.split(",")]
            
            expand = ["transitions", "changelog", "subtasks", "description"]
            if arguments.expand:
                expand = [e.strip() for e in arguments.expand.split(",")]
            
            # Limit max_results to prevent overwhelming responses
            max_results = min(arguments.max_results or 30, 100)
            
            # Search for issues
            search_result = await jira_service.search_issues(
                jql=arguments.jql,
                fields=fields,
                expand=expand,
                max_results=max_results
            )
            
            issues = search_result.get("issues", [])
            total = search_result.get("total", 0)
            
            if not issues:
                return [TextContent(type="text", text="No issues found matching the search criteria.")]
            
            # Format the results
            output = []
            
            # Add summary header
            if total > len(issues):
                output.append(f"🔍 **Search Results**: Showing {len(issues)} of {total} issues\n")
            else:
                output.append(f"🔍 **Search Results**: Found {len(issues)} issue{'s' if len(issues) != 1 else ''}\n")
            
            # Format each issue
            for i, issue in enumerate(issues):
                formatted_issue = format_jira_issue(issue)
                output.append(formatted_issue)
                
                # Add separator between issues (except for the last one)
                if i < len(issues) - 1:
                    output.append("\n" + "="*50 + "\n")
            
            # Add footer if there are more results
            if total > len(issues):
                remaining = total - len(issues)
                output.append(f"\n💡 **Note**: {remaining} more issue{'s' if remaining != 1 else ''} available. Refine your JQL query or increase max_results to see more.")
            
            return [TextContent(type="text", text="\n".join(output))]
            
        except Exception as e:
            error_msg = f"Failed to search issues with JQL '{arguments.jql}': {str(e)}"
            
            # Provide helpful JQL examples on error
            error_msg += "\n\n💡 **JQL Examples**:"
            error_msg += "\n- `project = PROJ AND status = \"In Progress\"`"
            error_msg += "\n- `assignee = currentUser() AND status != Done`"
            error_msg += "\n- `created >= -7d AND project = PROJ`"
            error_msg += "\n- `status changed to \"Done\" during (-1w, now())`"
            error_msg += "\n- `priority = High AND resolution is EMPTY`"
            
            return [TextContent(type="text", text=error_msg)]
