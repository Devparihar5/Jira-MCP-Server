"""
Jira Relationship Tools
Tools for managing issue relationships and links
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from mcp.server import Server
from mcp.types import Tool, TextContent

from services.jira_client import JiraService
from utils.jira_formatter import format_issue_link


class LinkIssuesInput(BaseModel):
    inward_issue: str = Field(description="The key of the inward issue (e.g., 'PROJ-123')")
    outward_issue: str = Field(description="The key of the outward issue (e.g., 'PROJ-456')")
    link_type: str = Field(description="The type of link relationship (e.g., 'Blocks', 'Duplicates', 'Relates')")


class GetRelatedIssuesInput(BaseModel):
    issue_key: str = Field(description="The unique identifier of the Jira issue to get related issues for")


def register_relationship_tools(server: Server, jira_service: JiraService):
    """Register all relationship-related tools."""
    
    @server.call_tool()
    async def link_issues(arguments: LinkIssuesInput) -> List[TextContent]:
        """Create a link relationship between two Jira issues."""
        try:
            # Create the issue link
            await jira_service.link_issues(
                inward_issue=arguments.inward_issue,
                outward_issue=arguments.outward_issue,
                link_type=arguments.link_type
            )
            
            success_msg = f"✅ Successfully linked issues\n"
            success_msg += f"🔗 Link Type: {arguments.link_type}\n"
            success_msg += f"📥 Inward Issue: {arguments.inward_issue}\n"
            success_msg += f"📤 Outward Issue: {arguments.outward_issue}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            error_msg = f"Failed to link issues {arguments.inward_issue} and {arguments.outward_issue}: {str(e)}\n\n"
            error_msg += "💡 **Common Link Types**:\n"
            error_msg += "- `Blocks` - First issue blocks the second\n"
            error_msg += "- `Cloners` - Issues are clones of each other\n"
            error_msg += "- `Duplicate` - Issues are duplicates\n"
            error_msg += "- `Relates` - Issues are related\n"
            error_msg += "- `Causes` - First issue causes the second\n"
            
            return [TextContent(type="text", text=error_msg)]
    
    @server.call_tool()
    async def get_related_issues(arguments: GetRelatedIssuesInput) -> List[TextContent]:
        """Get all issues that are linked to or related to a specific issue."""
        try:
            # Get issue links
            links_response = await jira_service.get_issue_links(arguments.issue_key)
            issue_links = links_response.get("issuelinks", [])
            
            if not issue_links:
                return [TextContent(type="text", text=f"No related issues found for {arguments.issue_key}")]
            
            # Format the results
            output = []
            output.append(f"🔗 **Related Issues for {arguments.issue_key}**\n")
            
            # Group links by type
            link_groups = {}
            for link in issue_links:
                link_type = link.get("type", {})
                type_name = link_type.get("name", "Unknown")
                
                if type_name not in link_groups:
                    link_groups[type_name] = []
                link_groups[type_name].append(link)
            
            # Format each group
            for link_type, links in link_groups.items():
                output.append(f"📋 **{link_type} ({len(links)})**")
                output.append("")
                
                for i, link in enumerate(links):
                    formatted_link = format_issue_link(link)
                    output.append(f"  {i+1}. {formatted_link}")
                
                output.append("")
            
            # Add summary
            total_links = len(issue_links)
            output.append(f"📊 **Summary**: {total_links} related issue{'s' if total_links != 1 else ''} found")
            
            return [TextContent(type="text", text="\n".join(output))]
            
        except Exception as e:
            error_msg = f"Failed to get related issues for {arguments.issue_key}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
