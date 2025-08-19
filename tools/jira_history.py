"""
Jira History Tools
Tools for viewing issue history and changelog
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from mcp.server import Server
from mcp.types import Tool, TextContent

from services.jira_client import JiraService
from utils.jira_formatter import format_changelog_entry


class GetIssueHistoryInput(BaseModel):
    issue_key: str = Field(description="The unique identifier of the Jira issue to get history for")
    max_results: Optional[int] = Field(default=20, description="Maximum number of history entries to retrieve (default: 20)")


def register_history_tools(server: Server, jira_service: JiraService):
    """Register all history-related tools."""
    
    @server.call_tool()
    async def get_issue_history(arguments: GetIssueHistoryInput) -> List[TextContent]:
        """Retrieve the complete change history and changelog for a Jira issue."""
        try:
            # Get issue changelog
            changelog_response = await jira_service.get_issue_changelog(arguments.issue_key)
            changelog = changelog_response.get("changelog", {})
            histories = changelog.get("histories", [])
            total = changelog.get("total", 0)
            
            if not histories:
                return [TextContent(type="text", text=f"No history found for issue {arguments.issue_key}")]
            
            # Limit results if requested (get most recent entries)
            max_results = arguments.max_results or 20
            if len(histories) > max_results:
                histories = histories[-max_results:]
            
            # Sort by created date (most recent first)
            histories.sort(key=lambda x: x.get("created", ""), reverse=True)
            
            # Format the results
            output = []
            
            # Add header
            if total > len(histories):
                output.append(f"📜 **History for {arguments.issue_key}**: Showing {len(histories)} of {total} entries (most recent)\n")
            else:
                output.append(f"📜 **History for {arguments.issue_key}**: {len(histories)} entr{'ies' if len(histories) != 1 else 'y'}\n")
            
            # Format each history entry
            for i, history in enumerate(histories):
                formatted_entry = format_changelog_entry(history)
                output.append(formatted_entry)
                
                # Add separator between entries (except for the last one)
                if i < len(histories) - 1:
                    output.append("\n" + "-"*50 + "\n")
            
            # Add footer if there are more entries
            if total > len(histories):
                remaining = total - len(histories)
                output.append(f"\n💡 **Note**: {remaining} older entr{'ies' if remaining != 1 else 'y'} not shown. Increase max_results to see more.")
            
            return [TextContent(type="text", text="\n".join(output))]
            
        except Exception as e:
            error_msg = f"Failed to get history for issue {arguments.issue_key}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
