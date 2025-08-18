"""
Comprehensive Tool Handlers for Jira MCP Server
"""

from typing import Any, Dict, List, Optional, Sequence
from mcp.types import TextContent
from services.jira_client import JiraService
from utils.jira_formatter import (
    format_jira_issue, format_jira_sprint, format_jira_comment, 
    format_jira_worklog, format_issue_link, format_changelog_entry
)


async def handle_get_issue(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle get_issue tool call."""
    try:
        issue_key = arguments.get("issue_key")
        if not issue_key:
            return [TextContent(type="text", text="❌ issue_key is required")]
        
        fields = arguments.get("fields", "").split(",") if arguments.get("fields") else None
        expand = arguments.get("expand", "").split(",") if arguments.get("expand") else ["transitions", "changelog", "subtasks", "description"]
        
        issue = await jira_service.get_issue(
            issue_key=issue_key,
            fields=[f.strip() for f in fields] if fields else None,
            expand=[e.strip() for e in expand] if expand else None
        )
        
        formatted_issue = format_jira_issue(issue)
        return [TextContent(type="text", text=formatted_issue)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to get issue: {str(e)}")]


async def handle_create_issue(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle create_issue tool call."""
    try:
        project_key = arguments.get("project_key")
        summary = arguments.get("summary")
        description = arguments.get("description")
        issue_type = arguments.get("issue_type", "Task")
        
        if not all([project_key, summary, description]):
            return [TextContent(type="text", text="❌ project_key, summary, and description are required")]
        
        # Build additional fields
        additional_fields = {}
        if arguments.get("priority"):
            additional_fields["priority"] = {"name": arguments.get("priority")}
        if arguments.get("assignee"):
            additional_fields["assignee"] = {"name": arguments.get("assignee")}
        
        result = await jira_service.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=issue_type,
            **additional_fields
        )
        
        issue_key = result.get("key", "Unknown")
        success_msg = f"✅ Successfully created issue {issue_key}\n"
        success_msg += f"📝 Summary: {summary}\n"
        success_msg += f"🏷️  Type: {issue_type}\n"
        success_msg += f"📁 Project: {project_key}"
        
        if arguments.get("priority"):
            success_msg += f"\n⚡ Priority: {arguments.get('priority')}"
        if arguments.get("assignee"):
            success_msg += f"\n👤 Assignee: {arguments.get('assignee')}"
        
        return [TextContent(type="text", text=success_msg)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to create issue: {str(e)}")]


async def handle_create_child_issue(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle create_child_issue tool call."""
    try:
        parent_issue_key = arguments.get("parent_issue_key")
        summary = arguments.get("summary")
        description = arguments.get("description")
        issue_type = arguments.get("issue_type", "Sub-task")
        
        if not all([parent_issue_key, summary, description]):
            return [TextContent(type="text", text="❌ parent_issue_key, summary, and description are required")]
        
        # Get parent issue to determine project
        parent_issue = await jira_service.get_issue(parent_issue_key)
        project_key = parent_issue["fields"]["project"]["key"]
        
        result = await jira_service.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=issue_type,
            parent_key=parent_issue_key
        )
        
        issue_key = result.get("key", "Unknown")
        success_msg = f"✅ Successfully created child issue {issue_key}\n"
        success_msg += f"📝 Summary: {summary}\n"
        success_msg += f"🏷️  Type: {issue_type}\n"
        success_msg += f"⬆️  Parent: {parent_issue_key}"
        
        return [TextContent(type="text", text=success_msg)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to create child issue: {str(e)}")]


async def handle_update_issue(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle update_issue tool call."""
    try:
        issue_key = arguments.get("issue_key")
        if not issue_key:
            return [TextContent(type="text", text="❌ issue_key is required")]
        
        # Build update fields
        update_fields = {}
        if arguments.get("summary"):
            update_fields["summary"] = arguments.get("summary")
        if arguments.get("description"):
            update_fields["description"] = arguments.get("description")
        if arguments.get("priority"):
            update_fields["priority"] = {"name": arguments.get("priority")}
        if arguments.get("assignee"):
            update_fields["assignee"] = {"name": arguments.get("assignee")}
        
        if not update_fields:
            return [TextContent(type="text", text="❌ At least one field to update must be provided")]
        
        await jira_service.update_issue(issue_key=issue_key, fields=update_fields)
        
        success_msg = f"✅ Successfully updated issue {issue_key}\n"
        for field, value in arguments.items():
            if field != "issue_key" and value:
                success_msg += f"📝 Updated {field}: {value}\n"
        
        return [TextContent(type="text", text=success_msg.rstrip())]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to update issue: {str(e)}")]


async def handle_search_issues(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle search_issues tool call."""
    try:
        jql = arguments.get("jql")
        if not jql:
            return [TextContent(type="text", text="❌ jql is required")]
        
        fields = arguments.get("fields", "").split(",") if arguments.get("fields") else None
        expand = arguments.get("expand", "").split(",") if arguments.get("expand") else ["transitions", "changelog", "subtasks", "description"]
        max_results = min(arguments.get("max_results", 30), 100)
        
        search_result = await jira_service.search_issues(
            jql=jql,
            fields=[f.strip() for f in fields] if fields else None,
            expand=[e.strip() for e in expand] if expand else None,
            max_results=max_results
        )
        
        issues = search_result.get("issues", [])
        total = search_result.get("total", 0)
        
        if not issues:
            return [TextContent(type="text", text="No issues found matching the search criteria.")]
        
        # Format results
        output = []
        if total > len(issues):
            output.append(f"🔍 **Search Results**: Showing {len(issues)} of {total} issues\n")
        else:
            output.append(f"🔍 **Search Results**: Found {len(issues)} issue{'s' if len(issues) != 1 else ''}\n")
        
        # Format each issue
        for i, issue in enumerate(issues):
            formatted_issue = format_jira_issue(issue)
            output.append(formatted_issue)
            
            if i < len(issues) - 1:
                output.append("\n" + "="*50 + "\n")
        
        # Add footer if there are more results
        if total > len(issues):
            remaining = total - len(issues)
            output.append(f"\n💡 **Note**: {remaining} more issue{'s' if remaining != 1 else ''} available. Refine your JQL query or increase max_results to see more.")
        
        return [TextContent(type="text", text="\n".join(output))]
        
    except Exception as e:
        error_msg = f"❌ Failed to search issues: {str(e)}\n\n"
        error_msg += "💡 **JQL Examples**:\n"
        error_msg += "- `project = PROJ AND status = \"In Progress\"`\n"
        error_msg += "- `assignee = currentUser() AND status != Done`\n"
        error_msg += "- `created >= -7d AND project = PROJ`\n"
        error_msg += "- `priority = High AND resolution is EMPTY`"
        return [TextContent(type="text", text=error_msg)]


async def handle_list_issue_types(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle list_issue_types tool call."""
    try:
        project_key = arguments.get("project_key")
        if not project_key:
            return [TextContent(type="text", text="❌ project_key is required")]
        
        issue_types = await jira_service.get_project_issue_types(project_key)
        
        if not issue_types:
            return [TextContent(type="text", text=f"No issue types found for project {project_key}")]
        
        output = [f"📋 **Issue Types for Project {project_key}**\n"]
        
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
        return [TextContent(type="text", text=f"❌ Failed to get issue types: {str(e)}")]


async def handle_transition_issue(jira_service: JiraService, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle transition_issue tool call."""
    try:
        issue_key = arguments.get("issue_key")
        transition_name = arguments.get("transition_name")
        
        if not all([issue_key, transition_name]):
            return [TextContent(type="text", text="❌ issue_key and transition_name are required")]
        
        # Get available transitions
        transitions_response = await jira_service.get_issue_transitions(issue_key)
        transitions = transitions_response.get("transitions", [])
        
        if not transitions:
            return [TextContent(type="text", text=f"❌ No transitions available for issue {issue_key}")]
        
        # Find matching transition
        target_transition = None
        available_transitions = []
        
        for transition in transitions:
            trans_name = transition.get("name", "")
            available_transitions.append(trans_name)
            
            if trans_name.lower() == transition_name.lower():
                target_transition = transition
                break
        
        if not target_transition:
            error_msg = f"❌ Transition '{transition_name}' not found for issue {issue_key}\n\n"
            error_msg += "Available transitions:\n"
            for i, trans_name in enumerate(available_transitions, 1):
                error_msg += f"  {i}. {trans_name}\n"
            return [TextContent(type="text", text=error_msg)]
        
        # Perform transition
        transition_id = target_transition.get("id")
        await jira_service.transition_issue(issue_key=issue_key, transition_id=transition_id)
        
        to_status = target_transition.get("to", {}).get("name", "Unknown")
        success_msg = f"✅ Successfully transitioned issue {issue_key}\n"
        success_msg += f"🔄 Transition: {transition_name}\n"
        success_msg += f"📊 New Status: {to_status}"
        
        return [TextContent(type="text", text=success_msg)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Failed to transition issue: {str(e)}")]
