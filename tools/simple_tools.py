"""
Simplified Jira Tools for MCP Server
Using a more straightforward approach for tool registration
"""

from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from services.jira_client import JiraService
from utils.jira_formatter import format_jira_issue


def register_simple_tools(server: Server, jira_service: JiraService):
    """Register simplified Jira tools."""
    
    # Tool 1: Get Issue
    @server.call_tool()
    async def get_issue(issue_key: str, fields: str = "", expand: str = "") -> List[TextContent]:
        """Get detailed information about a Jira issue."""
        try:
            # Parse parameters
            field_list = [f.strip() for f in fields.split(",")] if fields else None
            expand_list = [e.strip() for e in expand.split(",")] if expand else ["transitions", "changelog", "subtasks", "description"]
            
            # Get the issue
            issue = await jira_service.get_issue(
                issue_key=issue_key,
                fields=field_list,
                expand=expand_list
            )
            
            # Format and return
            formatted_issue = format_jira_issue(issue)
            return [TextContent(type="text", text=formatted_issue)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Failed to get issue {issue_key}: {str(e)}")]
    
    # Tool 2: Search Issues
    @server.call_tool()
    async def search_issues(jql: str, max_results: int = 20) -> List[TextContent]:
        """Search for Jira issues using JQL."""
        try:
            # Search for issues
            search_result = await jira_service.search_issues(
                jql=jql,
                max_results=min(max_results, 50)
            )
            
            issues = search_result.get("issues", [])
            total = search_result.get("total", 0)
            
            if not issues:
                return [TextContent(type="text", text="No issues found matching the search criteria.")]
            
            # Format results
            output = [f"🔍 **Search Results**: Found {len(issues)} of {total} issues\n"]
            
            for i, issue in enumerate(issues):
                key = issue.get("key", "Unknown")
                summary = issue.get("fields", {}).get("summary", "No summary")
                status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                assignee = issue.get("fields", {}).get("assignee")
                assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
                
                output.append(f"{i+1}. **{key}**: {summary}")
                output.append(f"   📊 Status: {status} | 👤 Assignee: {assignee_name}")
                output.append("")
            
            return [TextContent(type="text", text="\n".join(output))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Failed to search issues: {str(e)}")]
    
    # Tool 3: Create Issue
    @server.call_tool()
    async def create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> List[TextContent]:
        """Create a new Jira issue."""
        try:
            result = await jira_service.create_issue(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type
            )
            
            issue_key = result.get("key", "Unknown")
            success_msg = f"✅ Successfully created issue {issue_key}\n"
            success_msg += f"📝 Summary: {summary}\n"
            success_msg += f"🏷️  Type: {issue_type}\n"
            success_msg += f"📁 Project: {project_key}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Failed to create issue: {str(e)}")]
    
    # Tool 4: Add Comment
    @server.call_tool()
    async def add_comment(issue_key: str, comment: str) -> List[TextContent]:
        """Add a comment to a Jira issue."""
        try:
            result = await jira_service.add_comment(issue_key=issue_key, comment=comment)
            
            success_msg = f"✅ Successfully added comment to {issue_key}\n"
            success_msg += f"💬 Comment: {comment[:100]}{'...' if len(comment) > 100 else ''}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Failed to add comment: {str(e)}")]
    
    # Tool 5: Add Worklog
    @server.call_tool()
    async def add_worklog(issue_key: str, time_spent: str, comment: str = "") -> List[TextContent]:
        """Log time spent on a Jira issue."""
        try:
            result = await jira_service.add_worklog(
                issue_key=issue_key,
                time_spent=time_spent,
                comment=comment if comment else None
            )
            
            success_msg = f"✅ Successfully logged time for {issue_key}\n"
            success_msg += f"⏱️  Time: {time_spent}"
            if comment:
                success_msg += f"\n💭 Comment: {comment}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Failed to log time: {str(e)}")]
    
    # Tool 6: Transition Issue
    @server.call_tool()
    async def transition_issue(issue_key: str, transition_name: str) -> List[TextContent]:
        """Transition a Jira issue to a new status."""
        try:
            # Get available transitions
            transitions_response = await jira_service.get_issue_transitions(issue_key)
            transitions = transitions_response.get("transitions", [])
            
            # Find matching transition
            target_transition = None
            for transition in transitions:
                if transition.get("name", "").lower() == transition_name.lower():
                    target_transition = transition
                    break
            
            if not target_transition:
                available = [t.get("name", "") for t in transitions]
                return [TextContent(type="text", text=f"❌ Transition '{transition_name}' not found. Available: {', '.join(available)}")]
            
            # Perform transition
            await jira_service.transition_issue(issue_key, target_transition.get("id"))
            
            success_msg = f"✅ Successfully transitioned {issue_key}\n"
            success_msg += f"🔄 Transition: {transition_name}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Failed to transition issue: {str(e)}")]
