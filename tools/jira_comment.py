"""
Jira Comment Tools
Tools for managing comments on Jira issues
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from mcp.server import Server
from mcp.types import Tool, TextContent

from services.jira_client import JiraService
from utils.jira_formatter import format_jira_comment


class AddCommentInput(BaseModel):
    issue_key: str = Field(description="The unique identifier of the Jira issue to add a comment to")
    comment: str = Field(description="The comment text to add to the issue")


class GetCommentsInput(BaseModel):
    issue_key: str = Field(description="The unique identifier of the Jira issue to retrieve comments from")
    max_results: Optional[int] = Field(default=20, description="Maximum number of comments to retrieve (default: 20)")


def register_comment_tools(server: Server, jira_service: JiraService):
    """Register all comment-related tools."""
    
    @server.call_tool()
    async def add_comment(arguments: AddCommentInput) -> List[TextContent]:
        """Add a comment to a Jira issue."""
        try:
            # Add the comment
            comment_result = await jira_service.add_comment(
                issue_key=arguments.issue_key,
                comment=arguments.comment
            )
            
            # Format success message
            comment_id = comment_result.get("id", "Unknown")
            author = comment_result.get("author", {})
            author_name = author.get("displayName", "Unknown")
            
            success_msg = f"✅ Successfully added comment to issue {arguments.issue_key}\n"
            success_msg += f"💬 Comment ID: {comment_id}\n"
            success_msg += f"👤 Author: {author_name}\n"
            
            # Show preview of comment
            comment_preview = arguments.comment[:150] + "..." if len(arguments.comment) > 150 else arguments.comment
            success_msg += f"📝 Comment: {comment_preview}"
            
            return [TextContent(type="text", text=success_msg)]
            
        except Exception as e:
            error_msg = f"Failed to add comment to issue {arguments.issue_key}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
    
    @server.call_tool()
    async def get_comments(arguments: GetCommentsInput) -> List[TextContent]:
        """Retrieve all comments from a Jira issue."""
        try:
            # Get comments for the issue
            comments_response = await jira_service.get_comments(arguments.issue_key)
            comments = comments_response.get("comments", [])
            total = comments_response.get("total", 0)
            
            if not comments:
                return [TextContent(type="text", text=f"No comments found for issue {arguments.issue_key}")]
            
            # Limit results if requested
            max_results = arguments.max_results or 20
            if len(comments) > max_results:
                comments = comments[-max_results:]  # Get the most recent comments
            
            # Format the results
            output = []
            
            # Add header
            if total > len(comments):
                output.append(f"💬 **Comments for {arguments.issue_key}**: Showing {len(comments)} of {total} comments (most recent)\n")
            else:
                output.append(f"💬 **Comments for {arguments.issue_key}**: {len(comments)} comment{'s' if len(comments) != 1 else ''}\n")
            
            # Format each comment
            for i, comment in enumerate(comments):
                formatted_comment = format_jira_comment(comment)
                output.append(formatted_comment)
                
                # Add separator between comments (except for the last one)
                if i < len(comments) - 1:
                    output.append("\n" + "-"*40 + "\n")
            
            # Add footer if there are more comments
            if total > len(comments):
                remaining = total - len(comments)
                output.append(f"\n💡 **Note**: {remaining} older comment{'s' if remaining != 1 else ''} not shown. Increase max_results to see more.")
            
            return [TextContent(type="text", text="\n".join(output))]
            
        except Exception as e:
            error_msg = f"Failed to get comments for issue {arguments.issue_key}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
