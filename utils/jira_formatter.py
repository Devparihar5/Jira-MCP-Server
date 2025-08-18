"""
Jira Formatter Utility
Provides consistent formatting for Jira data structures
"""

from typing import Any, Dict, List, Optional
from datetime import datetime


def format_jira_issue(issue: Dict[str, Any]) -> str:
    """Format a Jira issue for display."""
    fields = issue.get("fields", {})
    
    # Basic information
    key = issue.get("key", "Unknown")
    summary = fields.get("summary", "No summary")
    status = fields.get("status", {}).get("name", "Unknown")
    issue_type = fields.get("issuetype", {}).get("name", "Unknown")
    priority = fields.get("priority", {}).get("name", "None")
    
    # Assignee and reporter
    assignee = fields.get("assignee")
    assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
    
    reporter = fields.get("reporter")
    reporter_name = reporter.get("displayName", "Unknown") if reporter else "Unknown"
    
    # Dates
    created = fields.get("created", "")
    updated = fields.get("updated", "")
    
    if created:
        created = format_datetime(created)
    if updated:
        updated = format_datetime(updated)
    
    # Description
    description = extract_text_from_adf(fields.get("description"))
    if not description:
        description = "No description"
    
    # Project
    project = fields.get("project", {})
    project_name = project.get("name", "Unknown")
    project_key = project.get("key", "Unknown")
    
    # Build the formatted output
    output = []
    output.append(f"🎫 **{key}**: {summary}")
    output.append(f"📊 **Status**: {status}")
    output.append(f"🏷️  **Type**: {issue_type}")
    output.append(f"⚡ **Priority**: {priority}")
    output.append(f"👤 **Assignee**: {assignee_name}")
    output.append(f"📝 **Reporter**: {reporter_name}")
    output.append(f"📁 **Project**: {project_name} ({project_key})")
    
    if created:
        output.append(f"📅 **Created**: {created}")
    if updated:
        output.append(f"🔄 **Updated**: {updated}")
    
    output.append(f"📄 **Description**: {description}")
    
    # Add subtasks if present
    subtasks = fields.get("subtasks", [])
    if subtasks:
        output.append("📋 **Subtasks**:")
        for subtask in subtasks:
            subtask_key = subtask.get("key", "Unknown")
            subtask_summary = subtask.get("fields", {}).get("summary", "No summary")
            subtask_status = subtask.get("fields", {}).get("status", {}).get("name", "Unknown")
            output.append(f"  - {subtask_key}: {subtask_summary} ({subtask_status})")
    
    # Add parent if present
    parent = fields.get("parent")
    if parent:
        parent_key = parent.get("key", "Unknown")
        parent_summary = parent.get("fields", {}).get("summary", "No summary")
        output.append(f"⬆️  **Parent**: {parent_key}: {parent_summary}")
    
    # Add available transitions if present
    transitions = issue.get("transitions", [])
    if transitions:
        transition_names = [t.get("name", "Unknown") for t in transitions]
        output.append(f"🔄 **Available Transitions**: {', '.join(transition_names)}")
    
    return "\n".join(output)


def format_jira_sprint(sprint: Dict[str, Any]) -> str:
    """Format a Jira sprint for display."""
    sprint_id = sprint.get("id", "Unknown")
    name = sprint.get("name", "Unnamed Sprint")
    state = sprint.get("state", "Unknown")
    
    start_date = sprint.get("startDate", "")
    end_date = sprint.get("endDate", "")
    complete_date = sprint.get("completeDate", "")
    
    if start_date:
        start_date = format_datetime(start_date)
    if end_date:
        end_date = format_datetime(end_date)
    if complete_date:
        complete_date = format_datetime(complete_date)
    
    goal = sprint.get("goal", "No goal set")
    
    output = []
    output.append(f"🏃 **Sprint {sprint_id}**: {name}")
    output.append(f"📊 **State**: {state}")
    output.append(f"🎯 **Goal**: {goal}")
    
    if start_date:
        output.append(f"🚀 **Start Date**: {start_date}")
    if end_date:
        output.append(f"🏁 **End Date**: {end_date}")
    if complete_date:
        output.append(f"✅ **Completed**: {complete_date}")
    
    return "\n".join(output)


def format_jira_comment(comment: Dict[str, Any]) -> str:
    """Format a Jira comment for display."""
    author = comment.get("author", {})
    author_name = author.get("displayName", "Unknown")
    
    created = comment.get("created", "")
    if created:
        created = format_datetime(created)
    
    body = extract_text_from_adf(comment.get("body"))
    if not body:
        body = "No content"
    
    output = []
    output.append(f"💬 **{author_name}** ({created})")
    output.append(f"{body}")
    
    return "\n".join(output)


def format_jira_worklog(worklog: Dict[str, Any]) -> str:
    """Format a Jira worklog for display."""
    author = worklog.get("author", {})
    author_name = author.get("displayName", "Unknown")
    
    time_spent = worklog.get("timeSpent", "Unknown")
    started = worklog.get("started", "")
    
    if started:
        started = format_datetime(started)
    
    comment = extract_text_from_adf(worklog.get("comment"))
    
    output = []
    output.append(f"⏱️  **{author_name}** logged {time_spent}")
    if started:
        output.append(f"📅 **Started**: {started}")
    if comment:
        output.append(f"💭 **Comment**: {comment}")
    
    return "\n".join(output)


def format_issue_link(link: Dict[str, Any]) -> str:
    """Format an issue link for display."""
    link_type = link.get("type", {})
    type_name = link_type.get("name", "Unknown")
    
    inward_issue = link.get("inwardIssue")
    outward_issue = link.get("outwardIssue")
    
    if inward_issue:
        key = inward_issue.get("key", "Unknown")
        summary = inward_issue.get("fields", {}).get("summary", "No summary")
        status = inward_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        direction = link_type.get("inward", "relates to")
        return f"🔗 {direction} {key}: {summary} ({status})"
    elif outward_issue:
        key = outward_issue.get("key", "Unknown")
        summary = outward_issue.get("fields", {}).get("summary", "No summary")
        status = outward_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        direction = link_type.get("outward", "relates to")
        return f"🔗 {direction} {key}: {summary} ({status})"
    
    return f"🔗 {type_name} (Unknown issue)"


def format_changelog_entry(entry: Dict[str, Any]) -> str:
    """Format a changelog entry for display."""
    author = entry.get("author", {})
    author_name = author.get("displayName", "Unknown")
    
    created = entry.get("created", "")
    if created:
        created = format_datetime(created)
    
    items = entry.get("items", [])
    
    output = []
    output.append(f"📝 **{author_name}** ({created})")
    
    for item in items:
        field = item.get("field", "Unknown")
        from_string = item.get("fromString", "")
        to_string = item.get("toString", "")
        
        if from_string and to_string:
            output.append(f"  - Changed {field}: {from_string} → {to_string}")
        elif to_string:
            output.append(f"  - Set {field}: {to_string}")
        elif from_string:
            output.append(f"  - Removed {field}: {from_string}")
        else:
            output.append(f"  - Modified {field}")
    
    return "\n".join(output)


def extract_text_from_adf(adf_content: Optional[Dict[str, Any]]) -> str:
    """Extract plain text from Atlassian Document Format (ADF)."""
    if not adf_content:
        return ""
    
    def extract_text_recursive(node: Dict[str, Any]) -> str:
        if not isinstance(node, dict):
            return ""
        
        text_parts = []
        
        # If this is a text node, return its text
        if node.get("type") == "text":
            return node.get("text", "")
        
        # If this node has content, process it recursively
        content = node.get("content", [])
        if isinstance(content, list):
            for child in content:
                text_parts.append(extract_text_recursive(child))
        
        return "".join(text_parts)
    
    return extract_text_recursive(adf_content).strip()


def format_datetime(datetime_str: str) -> str:
    """Format a datetime string for display."""
    try:
        # Parse ISO format datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError):
        return datetime_str


def format_time_duration(seconds: int) -> str:
    """Format time duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds > 0:
            return f"{minutes}m {remaining_seconds}s"
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes > 0:
            return f"{hours}h {remaining_minutes}m"
        return f"{hours}h"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
