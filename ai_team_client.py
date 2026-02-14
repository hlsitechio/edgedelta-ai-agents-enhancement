#!/usr/bin/env python3
"""
EdgeDelta AI Team API Client
Provides direct API access to the AI Team chat system, agents, and channels.

Discovered API Domains:
  - chat.ai.edgedelta.com  (threads, messages, channels, activity)
  - agent.ai.edgedelta.com (agents, periodic jobs)
  - api.edgedelta.com      (auth, JWT, org config)

Auth Methods:
  - X-ED-API-Token header  (for api.edgedelta.com)
  - Bearer JWT              (for chat.ai / agent.ai subdomains)
  - Cookie-based session    (browser, get JWT via /v1/cookie_service/get_jwt_from_cookie)
"""

import json
import time
import requests
from typing import Optional

CHAT_API = "https://chat.ai.edgedelta.com/v1"
AGENT_API = "https://agent.ai.edgedelta.com/v1"
MAIN_API = "https://api.edgedelta.com/v1"
AUTH_API = "https://api.edgedelta.com"


class EdgeDeltaAuth:
    """Handle Edge Delta authentication."""

    def __init__(self, org_id: str, api_token: str):
        self.org_id = org_id
        self.api_token = api_token
        self._jwt = None
        self._jwt_expires = 0

    def get_api_headers(self):
        """Headers for api.edgedelta.com (uses API token)."""
        return {
            "X-ED-API-Token": self.api_token,
            "Content-Type": "application/json",
        }

    def login(self, email: str, password: str) -> str:
        """Login with email/password, returns JWT."""
        resp = requests.post(
            f"{AUTH_API}/auth/login",
            json={"username": email, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()
        # The login sets cookies; extract JWT from cookie service
        self._session_cookies = resp.cookies
        return self._refresh_jwt_from_cookies(resp.cookies)

    def _refresh_jwt_from_cookies(self, cookies) -> str:
        resp = requests.get(
            f"{MAIN_API}/cookie_service/get_jwt_from_cookie",
            cookies=cookies,
        )
        resp.raise_for_status()
        self._jwt = resp.json()["bearer_token"]
        self._jwt_expires = time.time() + 35000  # ~10h validity
        return self._jwt

    def get_jwt_headers(self, jwt: Optional[str] = None):
        """Headers for chat.ai / agent.ai (uses Bearer JWT)."""
        token = jwt or self._jwt
        if not token:
            raise ValueError("No JWT available. Call login() first or provide JWT.")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }


class AITeamClient:
    """Edge Delta AI Team API client."""

    def __init__(self, org_id: str, jwt: str):
        self.org_id = org_id
        self.jwt = jwt
        self.headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
        }

    def _chat_url(self, path: str) -> str:
        return f"{CHAT_API}/orgs/{self.org_id}{path}"

    def _agent_url(self, path: str) -> str:
        return f"{AGENT_API}/orgs/{self.org_id}{path}"

    # ── Agents ──────────────────────────────────────────────

    def list_agents(self) -> list:
        """List all AI agents in the org."""
        resp = requests.get(self._agent_url("/agents"), headers=self.headers)
        resp.raise_for_status()
        return resp.json()["data"]

    def get_agent(self, agent_id: str) -> dict:
        """Get a specific agent by ID."""
        agents = self.list_agents()
        for a in agents:
            if a["id"] == agent_id:
                return a
        raise ValueError(f"Agent '{agent_id}' not found")

    def create_agent(
        self,
        name: str,
        description: str,
        system_prompt: str,
        model: str = "claude-opus-4.5",
        role: str = "",
        capabilities: list = None,
        connectors: list = None,
        temperature: float = 0.1,
        priority: int = 10,
    ) -> dict:
        """Create a new AI teammate/agent.

        Args:
            name: Display name (e.g. "Recon Specialist")
            description: Short description of what the agent does
            system_prompt: Full system prompt (masterPrompt) with instructions
            model: LLM model to use (claude-opus-4.5, gpt-5.2, etc.)
            role: Role title (e.g. "Security Reconnaissance Specialist")
            capabilities: List of capability tags
            connectors: List of connector names (edgedelta-mcp, github, etc.)
            temperature: Model temperature (0.0-1.0)
            priority: Agent priority (1-10)

        Returns:
            Created agent dict with id, status, toolConfigurations, etc.
        """
        payload = {
            "name": name,
            "description": description,
            "masterPrompt": system_prompt,
            "model": model,
            "modelTemperature": temperature,
            "status": "active",
            "priority": priority,
            "type": "custom",
            "capabilities": capabilities or [],
            "connectors": connectors or ["edgedelta-mcp", "edgedelta-documentation"],
            "userPrompt": "{{#if memory_context}}\n{{{ memory_context }}}\n\n---\n\n{{/if}}\n{{{ question }}}",
        }
        if role:
            payload["role"] = role

        resp = requests.post(
            self._agent_url("/agents"),
            headers=self.headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["data"]

    def update_agent(self, agent_id: str, **kwargs) -> dict:
        """Update an existing agent. Pass any field to update."""
        resp = requests.put(
            self._agent_url(f"/agents/{agent_id}"),
            headers=self.headers,
            json=kwargs,
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    def delete_agent(self, agent_id: str) -> bool:
        """Delete a custom agent."""
        resp = requests.delete(
            self._agent_url(f"/agents/{agent_id}"),
            headers=self.headers,
        )
        return resp.status_code in (200, 204)

    # ── Channels ────────────────────────────────────────────

    def list_channels(self) -> list:
        """List all channels and DMs."""
        resp = requests.get(self._chat_url("/channels"), headers=self.headers)
        resp.raise_for_status()
        return resp.json()["data"]

    def get_channel(self, channel_id: str) -> dict:
        """Get a specific channel."""
        resp = requests.get(
            self._chat_url(f"/channels/{channel_id}"),
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json().get("data", resp.json())

    # ── Threads & Messages ──────────────────────────────────

    def create_thread(self, channel_id: str, message: str) -> dict:
        """Create a new thread and send the first message.

        This is the primary way to interact with AI agents.
        The 'title' field IS the user message.

        Args:
            channel_id: DM channel ID (e.g. "dm-sre", "dm-security-engineer",
                        or "dm-{agent_uuid}" for custom agents)
            message: The message to send to the agent

        Returns:
            Thread dict with id, state, participants, etc.
        """
        import secrets
        client_id = f"thread:{secrets.token_urlsafe(16)}"
        payload = {
            "clientTempId": client_id,
            "title": message,
        }
        resp = requests.post(
            self._chat_url(f"/channels/{channel_id}/threads"),
            headers=self.headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["data"]

    def get_thread(self, channel_id: str, thread_id: str, message_limit: int = 10000) -> dict:
        """Get a thread with its messages."""
        resp = requests.get(
            self._chat_url(f"/channels/{channel_id}/threads/{thread_id}?messageLimit={message_limit}"),
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    def get_thread_messages(self, channel_id: str, thread_id: str) -> list:
        """Get messages from a thread."""
        resp = requests.get(
            self._chat_url(f"/channels/{channel_id}/threads/{thread_id}/messages"),
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def list_threads(self, channel_id: str, limit: int = 20) -> list:
        """List threads in a channel."""
        resp = requests.get(
            self._chat_url(f"/channels/{channel_id}/threads?limit={limit}&messageLimit=10000"),
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def mark_thread_read(self, channel_id: str, thread_id: str):
        """Mark a thread as read."""
        requests.post(
            self._chat_url(f"/channels/{channel_id}/threads/{thread_id}/mark-read"),
            headers=self.headers,
        )

    # ── Activity ────────────────────────────────────────────

    def get_activity(self, limit: int = 20, lookback: str = "7d", channel_id: str = None) -> list:
        """Get activity feed."""
        params = f"limit={limit}&sort=last-activity"
        if lookback:
            params += f"&lookback={lookback}"
        if channel_id:
            params += f"&channelId={channel_id}"
        resp = requests.get(
            self._chat_url(f"/activity?{params}"),
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_badge_count(self, lookback: str = "7d") -> dict:
        """Get aggregate badge count."""
        resp = requests.get(
            self._chat_url(f"/activity/aggregate-badge-count?lookback={lookback}"),
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()

    # ── AI Models ───────────────────────────────────────────

    def list_models(self, api_token: str = None) -> list:
        """List available AI models. Requires API token auth."""
        headers = {"X-ED-API-Token": api_token, "Content-Type": "application/json"} if api_token else self.headers
        resp = requests.get(
            f"{MAIN_API}/orgs/{self.org_id}/ai/models",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json().get("models", [])

    # ── Connectors ──────────────────────────────────────────

    def list_connectors(self, api_token: str = None) -> list:
        """List AI connectors. Requires API token auth."""
        headers = {"X-ED-API-Token": api_token, "Content-Type": "application/json"} if api_token else self.headers
        resp = requests.get(
            f"{MAIN_API}/orgs/{self.org_id}/ai/connectors",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()

    # ── High-Level Helpers ──────────────────────────────────

    def send_message_and_wait(
        self,
        channel_id: str,
        message: str,
        timeout: int = 120,
        poll_interval: int = 5,
    ) -> dict:
        """Send a message to an agent and wait for the response.

        Args:
            channel_id: DM channel ID
            message: Message text
            timeout: Max seconds to wait for response
            poll_interval: Seconds between polls

        Returns:
            Dict with thread info and agent response messages
        """
        thread = self.create_thread(channel_id, message)
        thread_id = thread["id"]
        print(f"Thread created: {thread_id} (state: {thread['state']})")

        start = time.time()
        while time.time() - start < timeout:
            time.sleep(poll_interval)
            thread_data = self.get_thread(channel_id, thread_id)
            state = thread_data.get("state", "unknown")
            msg_count = thread_data.get("messageCount", 0)
            print(f"  [{int(time.time()-start)}s] state={state}, messages={msg_count}")

            if state in ("resolved", "done") or msg_count >= 2:
                messages = thread_data.get("messages", {}).get("data", [])
                if not messages:
                    messages = self.get_thread_messages(channel_id, thread_id)
                return {
                    "thread": thread_data,
                    "messages": messages,
                    "state": state,
                }

        # Timeout - return what we have
        thread_data = self.get_thread(channel_id, thread_id)
        messages = thread_data.get("messages", {}).get("data", [])
        return {
            "thread": thread_data,
            "messages": messages,
            "state": thread_data.get("state", "timeout"),
        }

    def chat(self, agent_id: str, message: str, timeout: int = 120) -> str:
        """Simple chat interface - send message, get text response.

        Args:
            agent_id: Agent ID (e.g. "sre", "security-engineer", or UUID for custom)
            message: Message to send

        Returns:
            Agent's text response
        """
        channel_id = f"dm-{agent_id}"
        result = self.send_message_and_wait(channel_id, message, timeout=timeout)

        # Extract text from agent response
        for msg in result.get("messages", []):
            if msg.get("role") == "agent":
                text_parts = []
                for part in msg.get("parts", []):
                    if part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                if text_parts:
                    return "\n".join(text_parts)

        return f"[No response yet - state: {result.get('state', 'unknown')}]"
