"""
Jira Client Service
Handles authentication and API interactions with Atlassian Jira
"""

import os
from typing import Any, Dict, List, Optional, Union
import httpx
from atlassian import Jira


class JiraService:
    """Service class for interacting with Jira API."""
    
    def __init__(self):
        """Initialize the Jira service with credentials from environment variables."""
        self.host = os.getenv("ATLASSIAN_HOST")
        self.email = os.getenv("ATLASSIAN_EMAIL") 
        self.token = os.getenv("ATLASSIAN_TOKEN")
        
        if not all([self.host, self.email, self.token]):
            raise ValueError("Missing required environment variables: ATLASSIAN_HOST, ATLASSIAN_EMAIL, ATLASSIAN_TOKEN")
        
        # Remove trailing slash from host if present
        self.host = self.host.rstrip('/')
        
        self.jira = None
        self._http_client = None
    
    async def initialize(self):
        """Initialize the Jira client and HTTP client."""
        try:
            # Initialize Jira client
            self.jira = Jira(
                url=self.host,
                username=self.email,
                password=self.token,
                cloud=True
            )
            
            # Initialize HTTP client for direct API calls
            self._http_client = httpx.AsyncClient(
                auth=(self.email, self.token),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            # Test connection
            await self.test_connection()
            
        except Exception as e:
            raise Exception(f"Failed to initialize Jira service: {e}")
    
    async def test_connection(self):
        """Test the connection to Jira."""
        try:
            # Try to get current user info
            response = await self._http_client.get(f"{self.host}/rest/api/3/myself")
            response.raise_for_status()
            return True
        except Exception as e:
            raise Exception(f"Failed to connect to Jira: {e}")
    
    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
    
    # Issue operations
    async def get_issue(self, issue_key: str, fields: Optional[List[str]] = None, expand: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get a specific issue by key."""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        if expand:
            params["expand"] = ",".join(expand)
        
        response = await self._http_client.get(
            f"{self.host}/rest/api/3/issue/{issue_key}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def search_issues(self, jql: str, fields: Optional[List[str]] = None, expand: Optional[List[str]] = None, 
                          start_at: int = 0, max_results: int = 50) -> Dict[str, Any]:
        """Search for issues using JQL."""
        data = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results
        }
        
        if fields:
            data["fields"] = fields
        if expand:
            data["expand"] = expand
        
        response = await self._http_client.post(
            f"{self.host}/rest/api/3/search",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def create_issue(self, project_key: str, summary: str, description: str, issue_type: str, 
                          parent_key: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create a new issue."""
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {"name": issue_type}
        }
        
        # Add parent for subtasks
        if parent_key:
            fields["parent"] = {"key": parent_key}
        
        # Add any additional fields
        fields.update(kwargs)
        
        data = {"fields": fields}
        
        response = await self._http_client.post(
            f"{self.host}/rest/api/3/issue",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing issue."""
        # Convert simple text fields to ADF format if needed
        update_fields = {}
        for key, value in fields.items():
            if key == "description" and isinstance(value, str):
                update_fields[key] = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": value
                                }
                            ]
                        }
                    ]
                }
            else:
                update_fields[key] = value
        
        data = {"fields": update_fields}
        
        response = await self._http_client.put(
            f"{self.host}/rest/api/3/issue/{issue_key}",
            json=data
        )
        response.raise_for_status()
        return {"success": True}
    
    async def get_issue_transitions(self, issue_key: str) -> Dict[str, Any]:
        """Get available transitions for an issue."""
        response = await self._http_client.get(
            f"{self.host}/rest/api/3/issue/{issue_key}/transitions"
        )
        response.raise_for_status()
        return response.json()
    
    async def transition_issue(self, issue_key: str, transition_id: str) -> Dict[str, Any]:
        """Transition an issue to a new status."""
        data = {
            "transition": {"id": transition_id}
        }
        
        response = await self._http_client.post(
            f"{self.host}/rest/api/3/issue/{issue_key}/transitions",
            json=data
        )
        response.raise_for_status()
        return {"success": True}
    
    # Comment operations
    async def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """Add a comment to an issue."""
        data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        }
        
        response = await self._http_client.post(
            f"{self.host}/rest/api/3/issue/{issue_key}/comment",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def get_comments(self, issue_key: str) -> Dict[str, Any]:
        """Get all comments for an issue."""
        response = await self._http_client.get(
            f"{self.host}/rest/api/3/issue/{issue_key}/comment"
        )
        response.raise_for_status()
        return response.json()
    
    # Worklog operations
    async def add_worklog(self, issue_key: str, time_spent: str, comment: Optional[str] = None, 
                         started: Optional[str] = None) -> Dict[str, Any]:
        """Add a worklog entry to an issue."""
        data = {
            "timeSpent": time_spent
        }
        
        if comment:
            data["comment"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        
        if started:
            data["started"] = started
        
        response = await self._http_client.post(
            f"{self.host}/rest/api/3/issue/{issue_key}/worklog",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    # Project operations
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        response = await self._http_client.get(f"{self.host}/rest/api/3/project")
        response.raise_for_status()
        return response.json()
    
    async def get_project_issue_types(self, project_key: str) -> List[Dict[str, Any]]:
        """Get issue types for a project."""
        response = await self._http_client.get(f"{self.host}/rest/api/3/project/{project_key}")
        response.raise_for_status()
        project_data = response.json()
        return project_data.get("issueTypes", [])
    
    async def get_project_statuses(self, project_key: str) -> List[Dict[str, Any]]:
        """Get statuses for a project."""
        response = await self._http_client.get(f"{self.host}/rest/api/3/project/{project_key}/statuses")
        response.raise_for_status()
        return response.json()
    
    # Sprint operations (Agile API)
    async def get_boards(self) -> Dict[str, Any]:
        """Get all boards."""
        response = await self._http_client.get(f"{self.host}/rest/agile/1.0/board")
        response.raise_for_status()
        return response.json()
    
    async def get_board_sprints(self, board_id: int, state: Optional[str] = None) -> Dict[str, Any]:
        """Get sprints for a board."""
        params = {}
        if state:
            params["state"] = state
        
        response = await self._http_client.get(
            f"{self.host}/rest/agile/1.0/board/{board_id}/sprint",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def get_sprint(self, sprint_id: int) -> Dict[str, Any]:
        """Get a specific sprint."""
        response = await self._http_client.get(f"{self.host}/rest/agile/1.0/sprint/{sprint_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_sprint_issues(self, sprint_id: int) -> Dict[str, Any]:
        """Get issues in a sprint."""
        response = await self._http_client.get(f"{self.host}/rest/agile/1.0/sprint/{sprint_id}/issue")
        response.raise_for_status()
        return response.json()
    
    async def move_issues_to_sprint(self, sprint_id: int, issue_keys: List[str]) -> Dict[str, Any]:
        """Move issues to a sprint."""
        data = {
            "issues": issue_keys
        }
        
        response = await self._http_client.post(
            f"{self.host}/rest/agile/1.0/sprint/{sprint_id}/issue",
            json=data
        )
        response.raise_for_status()
        return {"success": True}
    
    # Issue linking
    async def link_issues(self, inward_issue: str, outward_issue: str, link_type: str) -> Dict[str, Any]:
        """Link two issues."""
        data = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_issue},
            "outwardIssue": {"key": outward_issue}
        }
        
        response = await self._http_client.post(
            f"{self.host}/rest/api/3/issueLink",
            json=data
        )
        response.raise_for_status()
        return {"success": True}
    
    async def get_issue_links(self, issue_key: str) -> Dict[str, Any]:
        """Get links for an issue."""
        issue = await self.get_issue(issue_key, expand=["issuelinks"])
        return {"issuelinks": issue.get("fields", {}).get("issuelinks", [])}
    
    # Issue history
    async def get_issue_changelog(self, issue_key: str) -> Dict[str, Any]:
        """Get changelog for an issue."""
        response = await self._http_client.get(
            f"{self.host}/rest/api/3/issue/{issue_key}",
            params={"expand": "changelog"}
        )
        response.raise_for_status()
        issue_data = response.json()
        return {"changelog": issue_data.get("changelog", {})}
