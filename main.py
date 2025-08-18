#!/usr/bin/env python3
"""
Jira MCP Server - Python Implementation
A Model Context Protocol server for Atlassian Jira integration
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server

from services.jira_client import JiraService
from tools import register_all_tools


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
    print(f'      "args": ["{os.path.abspath("main.py")}", "--env", "{os.path.abspath(".env")}"],')
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


async def run_stdio_server(server: Server):
    """Run the server in stdio mode."""
    async with stdio_server() as streams:
        await server.run(
            streams[0], streams[1], 
            server.create_initialization_options()
        )


async def main():
    """Main entry point for the Jira MCP server."""
    parser = argparse.ArgumentParser(description="Jira MCP Server")
    parser.add_argument("--env", help="Path to environment file (optional when environment variables are set directly)")
    parser.add_argument("--http-port", type=int, help="Port for HTTP server (basic HTTP mode - use stdio for full MCP support)")
    
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
    
    # Create MCP server
    server = Server("jira-mcp")
    
    # Register all tools
    register_all_tools(server, jira_service)
    print("✅ All Jira tools registered")
    
    try:
        if args.http_port:
            # HTTP mode - basic server for testing
            print(f"🚀 Starting Jira MCP Server in HTTP mode on port {args.http_port}")
            print("⚠️  Note: HTTP mode provides basic endpoints but full MCP functionality requires stdio mode")
            print(f"📡 Server will be available at: http://localhost:{args.http_port}")
            print("🔍 Available endpoints:")
            print(f"  - http://localhost:{args.http_port}/ (server info)")
            print(f"  - http://localhost:{args.http_port}/health (health check)")
            print(f"  - http://localhost:{args.http_port}/mcp (MCP endpoint - limited)")
            print()
            
            from http_server import run_http_server
            await run_http_server(server, args.http_port)
        else:
            # Stdio mode - full MCP support
            print_stdio_instructions()
            await run_stdio_server(server)
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
