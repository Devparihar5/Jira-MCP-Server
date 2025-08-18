"""
Comprehensive Tool Handlers - Part 2: Comments, Time Tracking, Relationships, and Sprint Management
"""

from typing import Any, Dict, List, Optional, Sequence
from mcp.types import TextContent
from services.jira_client import JiraService
from utils.jira_formatter import (
    format_jira_issue, format_jira_sprint, format_jira_comment, 
    format_jira_worklog, format_issue_link, format_changelog_entry
)


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


async def handle_link_issues(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle link_issues tool call."""
    try:
        inward_issue = arguments.get("inward_issue")
        outward_issue = arguments.get("outward_issue")
        link_type = arguments.get("link_type")
        
        if not all([inward_issue, outward_issue, link_type]):
            return [TextContent(type="text", text="❌ inward_issue, outward_issue, and link_type are required")]
        
        await jira_service.link_issues(
            inward_issue=inward_issue,
            outward_issue=outward_issue,
            link_type=link_type
        )
        
        success_msg = f"✅ Successfully linked issues\n"
        success_msg += f"🔗 Link Type: {link_type}\n"
        success_msg += f"📥 Inward Issue: {inward_issue}\n"
        success_msg += f"📤 Outward Issue: {outward_issue}"
        
        return [TextContent(type="text", text=success_msg)]
        
    except Exception as e:
        error_msg = f"❌ Failed to link issues: {str(e)}\n\n"
        error_msg += "💡 **Common Link Types**:\n"
        error_msg += "- `Blocks` - First issue blocks the second\n"
        error_msg += "- `Cloners` - Issues are clones of each other\n"
        error_msg += "- `Duplicate` - Issues are duplicates\n"
        error_msg += "- `Relates` - Issues are related\n"
        error_msg += "- `Causes` - First issue causes the second"
        return [TextContent(type="text", text=error_msg)]


async def handle_get_related_issues(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle get_related_issues tool call."""
    try:
        issue_key = arguments.get("issue_key")
        if not issue_key:
            return [TextContent(type="text", text="❌ issue_key is required")]
        
        links_response = await jira_service.get_issue_links(issue_key)
        issue_links = links_response.get("issuelinks", [])
        
        if not issue_links:
            return [TextContent(type="text", text=f"No related issues found for {issue_key}")]
        
        output = [f"🔗 **Related Issues for {issue_key}**\n"]
        
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
        
        total_links = len(issue_links)
        output.append(f"📊 **Summary**: {total_links} related issue{'s' if total_links != 1 else ''} found")
        
        return [TextContent(type="text", text="\n".join(output))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to get related issues: {str(e)}")]


async def handle_get_issue_history(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle get_issue_history tool call."""
    try:
        issue_key = arguments.get("issue_key")
        if not issue_key:
            return [TextContent(type="text", text="❌ issue_key is required")]
        
        max_results = arguments.get("max_results", 20)
        
        changelog_response = await jira_service.get_issue_changelog(issue_key)
        changelog = changelog_response.get("changelog", {})
        histories = changelog.get("histories", [])
        total = changelog.get("total", 0)
        
        if not histories:
            return [TextContent(type="text", text=f"No history found for issue {issue_key}")]
        
        # Limit results if requested (get most recent entries)
        if len(histories) > max_results:
            histories = histories[-max_results:]
        
        # Sort by created date (most recent first)
        histories.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        output = []
        if total > len(histories):
            output.append(f"📜 **History for {issue_key}**: Showing {len(histories)} of {total} entries (most recent)\n")
        else:
            output.append(f"📜 **History for {issue_key}**: {len(histories)} entr{'ies' if len(histories) != 1 else 'y'}\n")
        
        # Format each history entry
        for i, history in enumerate(histories):
            formatted_entry = format_changelog_entry(history)
            output.append(formatted_entry)
            
            if i < len(histories) - 1:
                output.append("\n" + "-"*50 + "\n")
        
        if total > len(histories):
            remaining = total - len(histories)
            output.append(f"\n💡 **Note**: {remaining} older entr{'ies' if remaining != 1 else 'y'} not shown.")
        
        return [TextContent(type="text", text="\n".join(output))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to get issue history: {str(e)}")]
