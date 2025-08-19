"""
Comment and Time Tracking Tool Handlers
"""

from typing import Any, Dict, List, Optional, Sequence
from mcp.types import TextContent
from services.jira_client import JiraService
from utils.jira_formatter import format_jira_comment, format_jira_worklog


async def handle_add_comment(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle add_comment tool call."""
    try:
        issue_key = arguments.get("issue_key")
        comment = arguments.get("comment")
        
        if not all([issue_key, comment]):
            return [TextContent(type="text", text="❌ issue_key and comment are required")]
        
        result = await jira_service.add_comment(issue_key=issue_key, comment=comment)
        
        success_msg = f"✅ Successfully added comment to {issue_key}\n"
        success_msg += f"💬 Comment: {comment[:100]}{'...' if len(comment) > 100 else ''}"
        
        return [TextContent(type="text", text=success_msg)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to add comment: {str(e)}")]


async def handle_get_comments(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle get_comments tool call."""
    try:
        issue_key = arguments.get("issue_key")
        if not issue_key:
            return [TextContent(type="text", text="❌ issue_key is required")]
        
        max_results = arguments.get("max_results", 20)
        
        comments_response = await jira_service.get_comments(issue_key)
        comments = comments_response.get("comments", [])
        total = comments_response.get("total", 0)
        
        if not comments:
            return [TextContent(type="text", text=f"No comments found for issue {issue_key}")]
        
        # Limit results if requested
        if len(comments) > max_results:
            comments = comments[-max_results:]  # Get most recent comments
        
        output = []
        if total > len(comments):
            output.append(f"💬 **Comments for {issue_key}**: Showing {len(comments)} of {total} comments (most recent)\n")
        else:
            output.append(f"💬 **Comments for {issue_key}**: {len(comments)} comment{'s' if len(comments) != 1 else ''}\n")
        
        # Format each comment
        for i, comment in enumerate(comments):
            formatted_comment = format_jira_comment(comment)
            output.append(formatted_comment)
            
            if i < len(comments) - 1:
                output.append("\n" + "-"*40 + "\n")
        
        if total > len(comments):
            remaining = total - len(comments)
            output.append(f"\n💡 **Note**: {remaining} older comment{'s' if remaining != 1 else ''} not shown.")
        
        return [TextContent(type="text", text="\n".join(output))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to get comments: {str(e)}")]


async def handle_add_worklog(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle add_worklog tool call."""
    try:
        issue_key = arguments.get("issue_key")
        time_spent = arguments.get("time_spent")
        
        if not all([issue_key, time_spent]):
            return [TextContent(type="text", text="❌ issue_key and time_spent are required")]
        
        comment = arguments.get("comment")
        started = arguments.get("started")
        
        result = await jira_service.add_worklog(
            issue_key=issue_key,
            time_spent=time_spent,
            comment=comment,
            started=started
        )
        
        success_msg = f"✅ Successfully logged time for {issue_key}\n"
        success_msg += f"⏱️  Time: {time_spent}"
        if comment:
            success_msg += f"\n💭 Comment: {comment}"
        if started:
            success_msg += f"\n📅 Started: {started}"
        
        return [TextContent(type="text", text=success_msg)]
        
    except Exception as e:
        error_msg = f"❌ Failed to add worklog: {str(e)}\n\n"
        error_msg += "💡 **Time Format Examples**:\n"
        error_msg += "- `3h` (3 hours)\n"
        error_msg += "- `30m` (30 minutes)\n"
        error_msg += "- `1h 30m` (1 hour 30 minutes)\n"
        error_msg += "- `2d` (2 days)\n"
        error_msg += "- `1d 4h` (1 day 4 hours)"
        return [TextContent(type="text", text=error_msg)]
