"""
Jira Worklog Tools
Tools for time tracking and worklog management
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from mcp.server import Server
from mcp.types import Tool, TextContent

from services.jira_client import JiraService
from utils.jira_formatter import format_jira_worklog


class AddWorklogInput(BaseModel):
    issue_key: str = Field(description="The unique identifier of the Jira issue to log time against")
    time_spent: str = Field(description="Time spent in Jira format (e.g., '3h', '30m', '1h 30m', '2d 4h')")
    comment: Optional[str] = Field(default=None, description="Optional comment describing the work performed")
    started: Optional[str] = Field(default=None, description="When the work started (ISO format, e.g., '2023-12-01T09:00:00.000+0000'). Defaults to now.")


def register_worklog_tools(server: Server, jira_service: JiraService):
    """Register all worklog-related tools."""
    
    def _format_time_for_jira(time_str: str) -> str:
        """Convert various time formats to Jira-compatible format."""
        # Jira accepts formats like: 3h, 30m, 1h 30m, 2d 4h, etc.
        # This function normalizes common input formats
        time_str = time_str.strip().lower()
        
        # Replace common variations
        replacements = {
            'hour': 'h',
            'hours': 'h',
            'hr': 'h',
            'hrs': 'h',
            'minute': 'm',
            'minutes': 'm',
            'min': 'm',
            'mins': 'm',
            'day': 'd',
            'days': 'd',
        }
        
        for old, new in replacements.items():
            time_str = time_str.replace(old, new)
        
        return time_str
    
    def _get_current_iso_time() -> str:
        """Get current time in ISO format for Jira."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000+0000")
    
    @server.call_tool()
    async def add_worklog(arguments: AddWorklogInput) -> List[TextContent]:
        """Add a worklog entry to track time spent on an issue."""
        try:
            # Format time for Jira
            formatted_time = _format_time_for_jira(arguments.time_spent)
            
            # Use current time if started time not provided
            started_time = arguments.started
            if not started_time:
                started_time = _get_current_iso_time()
            
            # Add the worklog
            worklog = await jira_service.add_worklog(
                issue_key=arguments.issue_key,
                time_spent=formatted_time,
                comment=arguments.comment,
                started=started_time
            )
            
            # Format success message
            success_msg = f"✅ Successfully logged time for issue {arguments.issue_key}\n"
            success_msg += f"⏱️  Time Spent: {formatted_time}\n"
            
            if arguments.comment:
                comment_preview = arguments.comment[:100] + "..." if len(arguments.comment) > 100 else arguments.comment
                success_msg += f"💭 Comment: {comment_preview}\n"
            
            # Add worklog ID if available
            worklog_id = worklog.get("id")
            if worklog_id:
                success_msg += f"🆔 Worklog ID: {worklog_id}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            error_msg = f"Failed to add worklog to issue {arguments.issue_key}: {str(e)}\n\n"
            error_msg += "💡 **Time Format Examples**:\n"
            error_msg += "- `3h` (3 hours)\n"
            error_msg += "- `30m` (30 minutes)\n"
            error_msg += "- `1h 30m` (1 hour 30 minutes)\n"
            error_msg += "- `2d` (2 days)\n"
            error_msg += "- `1d 4h` (1 day 4 hours)\n"
            
            return [TextContent(type="text", text=error_msg)]
