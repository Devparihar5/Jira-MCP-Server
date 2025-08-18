"""
Correct MCP Tools Implementation for Jira Server
"""

from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
from services.jira_client import JiraService
from utils.jira_formatter import format_jira_issue


def register_correct_tools(server: Server, jira_service: JiraService):
    """Register Jira tools using the correct MCP approach."""
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List all available Jira tools."""
        return [
            Tool(
                name="get_issue",
                description="Get detailed information about a specific Jira issue including status, assignee, description, and transitions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "The Jira issue key (e.g., 'PROJ-123')"
                        },
                        "fields": {
                            "type": "string",
                            "description": "Comma-separated list of fields to retrieve (optional)"
                        }
                    },
                    "required": ["issue_key"]
                }
            ),
            Tool(
                name="search_issues",
                description="Search for Jira issues using JQL (Jira Query Language)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "jql": {
                            "type": "string",
                            "description": "JQL query string (e.g., 'project = PROJ AND status = \"In Progress\"')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 20)"
                        }
                    },
                    "required": ["jql"]
                }
            ),
            Tool(
                name="create_issue",
                description="Create a new Jira issue in the specified project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "The project key where the issue will be created"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Brief summary/title of the issue"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the issue"
                        },
                        "issue_type": {
                            "type": "string",
                            "description": "Type of issue to create (default: 'Task')"
                        }
                    },
                    "required": ["project_key", "summary", "description"]
                }
            ),
            Tool(
                name="add_comment",
                description="Add a comment to a Jira issue",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "The Jira issue key to add comment to"
                        },
                        "comment": {
                            "type": "string",
                            "description": "The comment text to add"
                        }
                    },
                    "required": ["issue_key", "comment"]
                }
            ),
            Tool(
                name="add_worklog",
                description="Log time spent on a Jira issue",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "The Jira issue key to log time against"
                        },
                        "time_spent": {
                            "type": "string",
                            "description": "Time spent in Jira format (e.g., '3h', '30m', '1h 30m')"
                        },
                        "comment": {
                            "type": "string",
                            "description": "Optional comment describing the work performed"
                        }
                    },
                    "required": ["issue_key", "time_spent"]
                }
            ),
            Tool(
                name="transition_issue",
                description="Transition a Jira issue to a new status (e.g., move from 'In Progress' to 'Testing')",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "The Jira issue key to transition"
                        },
                        "transition_name": {
                            "type": "string",
                            "description": "The name of the transition to perform (e.g., 'Testing', 'Done', 'In Progress')"
                        }
                    },
                    "required": ["issue_key", "transition_name"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Handle tool calls."""
        
        if name == "get_issue":
            try:
                issue_key = arguments.get("issue_key")
                if not issue_key:
                    return [TextContent(type="text", text="❌ issue_key is required")]
                
                fields = arguments.get("fields", "").split(",") if arguments.get("fields") else None
                expand = ["transitions", "changelog", "subtasks", "description"]
                
                issue = await jira_service.get_issue(
                    issue_key=issue_key,
                    fields=[f.strip() for f in fields] if fields else None,
                    expand=expand
                )
                
                formatted_issue = format_jira_issue(issue)
                return [TextContent(type="text", text=formatted_issue)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Failed to get issue: {str(e)}")]
        
        elif name == "search_issues":
            try:
                jql = arguments.get("jql")
                if not jql:
                    return [TextContent(type="text", text="❌ jql is required")]
                
                max_results = min(arguments.get("max_results", 20), 50)
                
                search_result = await jira_service.search_issues(jql=jql, max_results=max_results)
                issues = search_result.get("issues", [])
                total = search_result.get("total", 0)
                
                if not issues:
                    return [TextContent(type="text", text="No issues found matching the search criteria.")]
                
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
        
        elif name == "create_issue":
            try:
                project_key = arguments.get("project_key")
                summary = arguments.get("summary")
                description = arguments.get("description")
                issue_type = arguments.get("issue_type", "Task")
                
                if not all([project_key, summary, description]):
                    return [TextContent(type="text", text="❌ project_key, summary, and description are required")]
                
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
        
        elif name == "add_comment":
            try:
                issue_key = arguments.get("issue_key")
                comment = arguments.get("comment")
                
                if not all([issue_key, comment]):
                    return [TextContent(type="text", text="❌ issue_key and comment are required")]
                
                await jira_service.add_comment(issue_key=issue_key, comment=comment)
                
                success_msg = f"✅ Successfully added comment to {issue_key}\n"
                success_msg += f"💬 Comment: {comment[:100]}{'...' if len(comment) > 100 else ''}"
                
                return [TextContent(type="text", text=success_msg)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Failed to add comment: {str(e)}")]
        
        elif name == "add_worklog":
            try:
                issue_key = arguments.get("issue_key")
                time_spent = arguments.get("time_spent")
                comment = arguments.get("comment", "")
                
                if not all([issue_key, time_spent]):
                    return [TextContent(type="text", text="❌ issue_key and time_spent are required")]
                
                await jira_service.add_worklog(
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
        
        elif name == "transition_issue":
            try:
                issue_key = arguments.get("issue_key")
                transition_name = arguments.get("transition_name")
                
                if not all([issue_key, transition_name]):
                    return [TextContent(type="text", text="❌ issue_key and transition_name are required")]
                
                # Get available transitions for the issue
                transitions_response = await jira_service.get_issue_transitions(issue_key)
                transitions = transitions_response.get("transitions", [])
                
                if not transitions:
                    return [TextContent(type="text", text=f"❌ No transitions available for issue {issue_key}")]
                
                # Find the matching transition (case-insensitive)
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
                
                # Perform the transition
                transition_id = target_transition.get("id")
                await jira_service.transition_issue(
                    issue_key=issue_key,
                    transition_id=transition_id
                )
                
                # Get the target status name
                to_status = target_transition.get("to", {}).get("name", "Unknown")
                
                success_msg = f"✅ Successfully transitioned issue {issue_key}\n"
                success_msg += f"🔄 Transition: {transition_name}\n"
                success_msg += f"📊 New Status: {to_status}"
                
                return [TextContent(type="text", text=success_msg)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Failed to transition issue: {str(e)}")]
        
        else:
            return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
