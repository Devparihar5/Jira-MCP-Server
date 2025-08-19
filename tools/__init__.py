"""
Tools package for Jira MCP Server
Contains all comprehensive tool implementations for Jira operations
"""

from mcp.server import Server
from services.jira_client import JiraService

from .comprehensive_jira_tools import register_comprehensive_jira_tools


def register_all_tools(server: Server, jira_service: JiraService):
    """Register all comprehensive Jira tools with the MCP server."""
    register_comprehensive_jira_tools(server, jira_service)
