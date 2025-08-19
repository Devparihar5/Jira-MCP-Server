#!/usr/bin/env python3
"""
Jira MCP Server - Python Implementation (FastMCP)
A Model Context Protocol server for Atlassian Jira integration using FastMCP
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from mcp.server import FastMCP

from services.jira_client import JiraService
from tools.comprehensive_jira_tools import *


def check_required_env_vars() -> list[str]:
    """Check for required environment variables and return missing ones."""
    required_envs = ["ATLASSIAN_HOST", "ATLASSIAN_EMAIL", "ATLASSIAN_TOKEN"]
    missing_envs = []
    
    for env in required_envs:
        if not os.getenv(env):
            missing_envs.append(env)
    
    return missing_envs


def print_setup_instructions(missing_envs: list[str]) -> None:
    """Print setup instructions for missing environment variables."""
    print("❌ Configuration Error: Missing required environment variables")
    print()
    print("Missing variables:")
    for env in missing_envs:
        print(f"  - {env}")
    print()
    print("📋 Setup Instructions:")
    print("1. Get your Atlassian API token from: https://id.atlassian.com/manage-profile/security/api-tokens")
    print("2. Set the environment variables:")
    print()
    print("   Option A - Using .env file:")
    print("   Create a .env file with:")
    print("   ATLASSIAN_HOST=https://your-domain.atlassian.net")
    print("   ATLASSIAN_EMAIL=your-email@example.com")
    print("   ATLASSIAN_TOKEN=your-api-token")
    print()
    print("   Option B - Using environment variables:")
    print("   export ATLASSIAN_HOST=https://your-domain.atlassian.net")
    print("   export ATLASSIAN_EMAIL=your-email@example.com")
    print("   export ATLASSIAN_TOKEN=your-api-token")
    print()


def print_http_instructions(port: int) -> None:
    """Print HTTP server configuration instructions."""
    print()
    print(f"🚀 Starting Jira MCP Server in HTTP mode on port {port}...")
    print()
    print("📋 HTTP Server Configuration:")
    print(f"Server will be available at: http://localhost:{port}")
    print(f"SSE endpoint: http://localhost:{port}/sse")
    print()
    print("📋 Cursor Configuration for HTTP mode:")
    print("Add the following to your Cursor MCP settings (.cursor/mcp.json):")
    print()
    print("```json")
    print("{")
    print('  "mcpServers": {')
    print('    "jira": {')
    print(f'      "command": "npx",')
    print(f'      "args": ["-y", "@modelcontextprotocol/server-everything", "http://localhost:{port}/sse"]')
    print("    }")
    print("  }")
    print("}")
    print("```")
    print()
    print("💡 Tips:")
    print("- Make sure the server is running before starting Cursor")
    print("- Restart Cursor after adding the configuration")
    print("- Test the connection by asking Claude: 'List my Jira projects'")
    print()
    print(f"🔄 Server starting on http://localhost:{port}...")


def print_stdio_instructions() -> None:
    """Print stdio server configuration instructions."""
    print()
    print("🚀 Starting Jira MCP Server in stdio mode...")
    print()
    print("📋 Cursor Configuration:")
    print("Add the following to your Cursor MCP settings (.cursor/mcp.json):")
    print()
    print("```json")
    print("{")
    print('  "mcpServers": {')
    print('    "jira": {')
    print('      "command": "python",')
    print(f'      "args": ["{os.path.abspath("main_fastmcp.py")}", "--env", "{os.path.abspath(".env")}"],')
    print(f'      "cwd": "{os.path.abspath(".")}"')
    print("    }")
    print("  }")
    print("}")
    print("```")
    print()
    print("💡 Tips:")
    print("- Restart Cursor after adding the configuration")
    print("- Test the connection by asking Claude: 'List my Jira projects'")
    print("- Use '@jira' in Cursor to reference Jira-related context")
    print()
    print("🔄 Server starting in stdio mode...")


async def main():
    """Main entry point for the Jira MCP server."""
    parser = argparse.ArgumentParser(description="Jira MCP Server")
    parser.add_argument("--env", help="Path to environment file (optional when environment variables are set directly)")
    parser.add_argument("--http", action="store_true", help="Run in HTTP server mode instead of stdio mode")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP server (default: 8000)")
    
    args = parser.parse_args()
    
    # Load environment file if specified
    if args.env:
        try:
            load_dotenv(args.env)
            print(f"✅ Loaded environment variables from {args.env}")
        except Exception as e:
            print(f"⚠️  Warning: Error loading env file {args.env}: {e}")
    
    # Check required environment variables
    missing_envs = check_required_env_vars()
    if missing_envs:
        print_setup_instructions(missing_envs)
        sys.exit(1)
    
    print("✅ All required environment variables are set")
    print(f"🔗 Connected to: {os.getenv('ATLASSIAN_HOST')}")
    
    # Initialize Jira service
    try:
        jira_service = JiraService()
        await jira_service.initialize()
        print("✅ Jira service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Jira service: {e}")
        sys.exit(1)
    
    # Create FastMCP server
    mcp = FastMCP("jira-mcp")
    
    # Helper function to convert TextContent results to dict
    def convert_result(result):
        """Convert TextContent result to dict for FastMCP."""
        if isinstance(result, list) and len(result) > 0:
            return {"content": result[0].text}
        return {"content": "No results found"}
    
    # Register all tools using FastMCP decorators
    @mcp.tool()
    async def get_issue(issue_key: str, expand: str = "changelog,renderedFields") -> dict:
        """Get detailed information about a Jira issue."""
        arguments = {"issue_key": issue_key, "expand": expand}
        result = await handle_get_issue(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def create_issue(
        project_key: str,
        summary: str,
        issue_type: str,
        description: str = "",
        priority: str = "Medium",
        assignee: str = "",
        labels: list[str] = None,
        components: list[str] = None,
        custom_fields: dict = None
    ) -> dict:
        """Create a new Jira issue."""
        arguments = {
            "project_key": project_key,
            "summary": summary,
            "issue_type": issue_type,
            "description": description,
            "priority": priority,
            "assignee": assignee,
            "labels": labels or [],
            "components": components or [],
            "custom_fields": custom_fields or {}
        }
        result = await handle_create_issue(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def search_issues(
        jql: str = "",
        project: str = "",
        status: str = "",
        assignee: str = "",
        issue_type: str = "",
        max_results: int = 50,
        fields: str = "summary,status,assignee,priority,created,updated"
    ) -> dict:
        """Search for Jira issues using JQL or simple filters."""
        arguments = {
            "jql": jql,
            "project": project,
            "status": status,
            "assignee": assignee,
            "issue_type": issue_type,
            "max_results": max_results,
            "fields": fields
        }
        result = await handle_search_issues(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def update_issue(
        issue_key: str,
        summary: str = "",
        description: str = "",
        priority: str = "",
        assignee: str = "",
        labels: list[str] = None,
        components: list[str] = None,
        custom_fields: dict = None
    ) -> dict:
        """Update an existing Jira issue."""
        arguments = {
            "issue_key": issue_key,
            "summary": summary,
            "description": description,
            "priority": priority,
            "assignee": assignee,
            "labels": labels or [],
            "components": components or [],
            "custom_fields": custom_fields or {}
        }
        result = await handle_update_issue(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def transition_issue(issue_key: str, transition_name: str, comment: str = "") -> dict:
        """Transition a Jira issue to a new status."""
        arguments = {
            "issue_key": issue_key,
            "transition_name": transition_name,
            "comment": comment
        }
        result = await handle_transition_issue(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def add_comment(issue_key: str, comment: str) -> dict:
        """Add a comment to a Jira issue."""
        arguments = {"issue_key": issue_key, "comment": comment}
        result = await handle_add_comment(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def get_comments(issue_key: str) -> dict:
        """Get all comments from a Jira issue."""
        arguments = {"issue_key": issue_key}
        result = await handle_get_comments(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def add_worklog(
        issue_key: str,
        time_spent: str,
        comment: str = "",
        start_date: str = ""
    ) -> dict:
        """Add a worklog entry to a Jira issue."""
        arguments = {
            "issue_key": issue_key,
            "time_spent": time_spent,
            "comment": comment,
            "start_date": start_date
        }
        result = await handle_add_worklog(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def list_sprints(board_id: int = 0, project_key: str = "", state: str = "active") -> dict:
        """List sprints for a board or project."""
        arguments = {
            "board_id": board_id,
            "project_key": project_key,
            "state": state
        }
        result = await handle_list_sprints(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def get_active_sprint(board_id: int = 0, project_key: str = "") -> dict:
        """Get the currently active sprint for a board or project."""
        arguments = {
            "board_id": board_id,
            "project_key": project_key
        }
        result = await handle_get_active_sprint(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def move_issues_to_sprint(sprint_id: int, issue_keys: list[str]) -> dict:
        """Move issues to a specific sprint."""
        arguments = {
            "sprint_id": sprint_id,
            "issue_keys": issue_keys
        }
        result = await handle_move_issues_to_sprint(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def get_boards(project_key: str = "") -> dict:
        """Get all boards, optionally filtered by project."""
        arguments = {"project_key": project_key}
        result = await handle_get_boards(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def list_issue_types(project_key: str) -> dict:
        """List available issue types for a project."""
        arguments = {"project_key": project_key}
        result = await handle_list_issue_types(jira_service, arguments)
        return convert_result(result)
    
    @mcp.tool()
    async def list_project_statuses(project_key: str) -> dict:
        """List available statuses for a project."""
        arguments = {"project_key": project_key}
        result = await handle_list_project_statuses(jira_service, arguments)
        return convert_result(result)
    
    print("✅ All Jira tools registered")
    
    try:
        if args.http:
            # Run HTTP server mode
            print_http_instructions(args.port)
            import uvicorn
            app = mcp.sse_app()
            config = uvicorn.Config(app=app, host="0.0.0.0", port=args.port, log_level="info")
            server = uvicorn.Server(config)
            await server.serve()
        else:
            # Run stdio mode (default)
            print_stdio_instructions()
            await mcp.run_stdio_async()
    finally:
        # Clean up
        await jira_service.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Jira MCP Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
