"""
Jira Transition Tools
Tools for transitioning issues through workflow states
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from mcp.server import Server
from mcp.types import Tool, TextContent

from services.jira_client import JiraService


class TransitionIssueInput(BaseModel):
    issue_key: str = Field(description="The unique identifier of the Jira issue to transition")
    transition_name: str = Field(description="The name of the transition to perform (e.g., 'In Progress', 'Done', 'Close Issue')")


def register_transition_tools(server: Server, jira_service: JiraService):
    """Register all transition-related tools."""
    
    @server.call_tool()
    async def transition_issue(arguments: TransitionIssueInput) -> List[TextContent]:
        """Transition a Jira issue through its workflow to a new status."""
        try:
            # Get available transitions for the issue
            transitions_response = await jira_service.get_issue_transitions(arguments.issue_key)
            transitions = transitions_response.get("transitions", [])
            
            if not transitions:
                return [TextContent(type="text", text=f"No transitions available for issue {arguments.issue_key}")]
            
            # Find the matching transition
            target_transition = None
            available_transitions = []
            
            for transition in transitions:
                transition_name = transition.get("name", "")
                available_transitions.append(transition_name)
                
                # Case-insensitive match
                if transition_name.lower() == arguments.transition_name.lower():
                    target_transition = transition
                    break
            
            if not target_transition:
                error_msg = f"Transition '{arguments.transition_name}' not found for issue {arguments.issue_key}\n\n"
                error_msg += "Available transitions:\n"
                for i, trans_name in enumerate(available_transitions, 1):
                    error_msg += f"  {i}. {trans_name}\n"
                return [TextContent(type="text", text=error_msg)]
            
            # Perform the transition
            transition_id = target_transition.get("id")
            await jira_service.transition_issue(
                issue_key=arguments.issue_key,
                transition_id=transition_id
            )
            
            # Get the target status name
            to_status = target_transition.get("to", {}).get("name", "Unknown")
            
            success_msg = f"✅ Successfully transitioned issue {arguments.issue_key}\n"
            success_msg += f"🔄 Transition: {arguments.transition_name}\n"
            success_msg += f"📊 New Status: {to_status}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            error_msg = f"Failed to transition issue {arguments.issue_key}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
