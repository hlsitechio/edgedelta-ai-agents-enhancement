#!/usr/bin/env python3
"""
EdgeDelta AI Team CLI
Command-line interface for managing AI agents, chatting, and monitoring channels.

Usage:
    python3 ai_team_cli.py <command> [options]

Commands:
    agents              List all AI agents
    agent <id>          Show agent details
    create-agent        Create a custom AI agent
    delete-agent        Delete a custom agent
    update-agent        Update an agent's config
    agent-tools <id>    Show MCP tools assigned to an agent
    clone-agent <id>    Clone an existing agent with a new name

    integrations        List all integrations (connectors)
    create-integration  Create a new integration/connector
    delete-integration  Delete an integration

    channels            List all channels
    channel <id>        Show channel details

    chat <agent>        Send a message to an agent and wait for response
    threads <ch>        List threads in a channel
    thread <ch> <t>     Show thread messages
    search-threads      Search threads across all channels
    activity            Show recent activity

    models              List available AI models
    connectors          List available connectors

    login               Login and get JWT
    status              Check auth status

Environment:
    ED_ORG_ID         Organization ID
    ED_API_TOKEN      API token for api.edgedelta.com
    ED_JWT            JWT for chat.ai/agent.ai (or use login command)
    ED_EMAIL          Email for login
    ED_PASSWORD       Password for login

    Or use --env-file <path> to load from .env file
"""

import argparse
import json
import os
import sys
import time
import secrets
from pathlib import Path

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent))
from ai_team_client import AITeamClient, EdgeDeltaAuth, CHAT_API, AGENT_API, MAIN_API


def load_env_file(path: str) -> dict:
    """Load environment variables from a .env file."""
    env = {}
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env[key.strip()] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        print(f"Error: env file not found: {path}")
        sys.exit(1)
    return env


def get_credentials(args) -> dict:
    """Get credentials from args, env file, or environment variables."""
    creds = {}

    # Load from env file if specified
    if hasattr(args, "env_file") and args.env_file:
        env = load_env_file(args.env_file)
        creds["org_id"] = env.get("ED_ORG_ID") or env.get("EDGEDELTA_ORG_ID", "")
        creds["api_token"] = env.get("ED_API_TOKEN") or env.get("ED_ORG_API_TOKEN", "")
        creds["jwt"] = env.get("ED_JWT", "")
        creds["email"] = env.get("ED_EMAIL", "")
        creds["password"] = env.get("ED_PASSWORD", "")
    else:
        # Check standard env file locations
        for env_path in [
            Path.home() / ".edgedelta.env",
            Path(".env"),
            Path("G:/edge delta/.env"),
        ]:
            if env_path.exists():
                env = load_env_file(str(env_path))
                creds["org_id"] = env.get("ED_ORG_ID") or env.get("EDGEDELTA_ORG_ID", "")
                creds["api_token"] = env.get("ED_API_TOKEN") or env.get("ED_ORG_API_TOKEN", "")
                creds["jwt"] = env.get("ED_JWT", "")
                creds["email"] = env.get("ED_EMAIL", "")
                creds["password"] = env.get("ED_PASSWORD", "")
                if creds.get("org_id"):
                    break

    # Override with environment variables
    creds["org_id"] = os.environ.get("ED_ORG_ID", creds.get("org_id", ""))
    creds["api_token"] = os.environ.get("ED_API_TOKEN", creds.get("api_token", ""))
    creds["jwt"] = os.environ.get("ED_JWT", creds.get("jwt", ""))
    creds["email"] = os.environ.get("ED_EMAIL", creds.get("email", ""))
    creds["password"] = os.environ.get("ED_PASSWORD", creds.get("password", ""))

    # Override with CLI args
    if hasattr(args, "org_id") and args.org_id:
        creds["org_id"] = args.org_id
    if hasattr(args, "api_token") and args.api_token:
        creds["api_token"] = args.api_token
    if hasattr(args, "jwt") and args.jwt:
        creds["jwt"] = args.jwt

    return creds


def get_client(args) -> AITeamClient:
    """Create an AITeamClient from credentials."""
    creds = get_credentials(args)

    if not creds.get("org_id"):
        print("Error: No org_id found. Set ED_ORG_ID or use --org-id")
        sys.exit(1)

    jwt = creds.get("jwt", "")

    # If no JWT, try to login
    if not jwt:
        if creds.get("email") and creds.get("password"):
            print("No JWT found, logging in...")
            auth = EdgeDeltaAuth(creds["org_id"], creds.get("api_token", ""))
            jwt = auth.login(creds["email"], creds["password"])
            print(f"Login successful, JWT obtained")
        elif creds.get("api_token"):
            print("Warning: API token found but no JWT. Some commands need JWT auth.")
            print("Use 'login' command or set ED_JWT to get JWT auth.")
            # For commands that work with API token, we'll handle it
            jwt = ""
        else:
            print("Error: No JWT or login credentials found.")
            print("Set ED_JWT, or ED_EMAIL + ED_PASSWORD, or use --jwt")
            sys.exit(1)

    return AITeamClient(creds["org_id"], jwt)


# ── Commands ─────────────────────────────────────────────────

def cmd_login(args):
    """Login and print JWT."""
    creds = get_credentials(args)
    if not creds.get("org_id"):
        print("Error: No org_id. Set ED_ORG_ID or use --org-id")
        sys.exit(1)

    email = args.email if hasattr(args, "email") and args.email else creds.get("email", "")
    password = args.password if hasattr(args, "password") and args.password else creds.get("password", "")

    if not email or not password:
        print("Error: Email and password required. Use --email/--password or set ED_EMAIL/ED_PASSWORD")
        sys.exit(1)

    auth = EdgeDeltaAuth(creds["org_id"], creds.get("api_token", ""))
    jwt = auth.login(email, password)
    print(f"Login successful!")
    print(f"\nJWT (set as ED_JWT):")
    print(jwt[:80] + "..." if len(jwt) > 80 else jwt)
    print(f"\nExport command:")
    print(f'export ED_JWT="{jwt}"')


def cmd_status(args):
    """Check authentication status."""
    creds = get_credentials(args)
    print(f"Org ID:    {creds.get('org_id', 'NOT SET')}")
    print(f"API Token: {'SET' if creds.get('api_token') else 'NOT SET'}")
    print(f"JWT:       {'SET' if creds.get('jwt') else 'NOT SET'}")
    print(f"Email:     {creds.get('email', 'NOT SET')}")

    if creds.get("api_token"):
        import requests
        try:
            resp = requests.get(
                f"{MAIN_API}/orgs/{creds['org_id']}/ai/models",
                headers={"X-ED-API-Token": creds["api_token"], "Content-Type": "application/json"},
                timeout=10,
            )
            print(f"\nAPI Token auth: {'OK' if resp.status_code == 200 else f'FAILED ({resp.status_code})'}")
        except Exception as e:
            print(f"\nAPI Token auth: ERROR ({e})")

    if creds.get("jwt"):
        import requests
        try:
            resp = requests.get(
                f"{AGENT_API}/orgs/{creds['org_id']}/agents",
                headers={"Authorization": f"Bearer {creds['jwt']}", "Content-Type": "application/json"},
                timeout=10,
            )
            print(f"JWT auth:       {'OK' if resp.status_code == 200 else f'FAILED ({resp.status_code})'}")
        except Exception as e:
            print(f"JWT auth:       ERROR ({e})")


def cmd_agents(args):
    """List all agents."""
    client = get_client(args)
    agents = client.list_agents()
    print(f"\n{'='*80}")
    print(f"AI Agents ({len(agents)} total)")
    print(f"{'='*80}")
    for a in agents:
        status_icon = "O" if a.get("status") == "active" else "x"
        agent_type = a.get("type", "unknown")
        model = a.get("model", "unknown")
        print(f"  [{status_icon}] {a['name']:<30} {model:<20} type={agent_type}")
        print(f"      ID: {a['id']}")
        if a.get("description"):
            desc = a["description"][:70] + "..." if len(a.get("description", "")) > 70 else a.get("description", "")
            print(f"      {desc}")
        print()


def cmd_agent(args):
    """Show agent details."""
    client = get_client(args)
    agent = client.get_agent(args.agent_id)
    print(json.dumps(agent, indent=2, default=str))


def cmd_create_agent(args):
    """Create a new custom agent."""
    client = get_client(args)

    # Read system prompt from file if provided
    system_prompt = args.system_prompt
    if args.prompt_file:
        with open(args.prompt_file, "r") as f:
            system_prompt = f.read()

    if not system_prompt:
        system_prompt = f"You are {args.name}, a custom AI agent for Edge Delta observability platform."

    capabilities = args.capabilities.split(",") if args.capabilities else []
    connectors = args.connectors.split(",") if args.connectors else None

    print(f"Creating agent '{args.name}'...")
    agent = client.create_agent(
        name=args.name,
        description=args.description or f"Custom agent: {args.name}",
        system_prompt=system_prompt,
        model=args.model,
        role=args.role or "",
        capabilities=capabilities,
        connectors=connectors,
        temperature=args.temperature,
        priority=args.priority,
        avatar=args.avatar,
    )
    print(f"\nAgent created successfully!")
    print(f"  ID:    {agent['id']}")
    print(f"  Name:  {agent.get('name', args.name)}")
    print(f"  Model: {agent.get('model', args.model)}")
    print(f"  DM Channel: dm-{agent['id']}")
    print(f"\nChat with: python3 ai_team_cli.py chat {agent['id']} --message 'Hello'")


def cmd_delete_agent(args):
    """Delete a custom agent."""
    client = get_client(args)
    if not args.force:
        confirm = input(f"Delete agent {args.agent_id}? (y/N): ")
        if confirm.lower() != "y":
            print("Cancelled.")
            return
    success = client.delete_agent(args.agent_id)
    print(f"{'Deleted' if success else 'Failed to delete'} agent {args.agent_id}")


def cmd_update_agent(args):
    """Update an agent."""
    client = get_client(args)
    updates = {}
    if args.name:
        updates["name"] = args.name
    if args.description:
        updates["description"] = args.description
    if args.model:
        updates["model"] = args.model
    if args.system_prompt:
        updates["system_prompt"] = args.system_prompt
    if args.prompt_file:
        with open(args.prompt_file, "r") as f:
            updates["system_prompt"] = f.read()
    if args.temperature is not None:
        updates["temperature"] = args.temperature
    if args.status:
        updates["status"] = args.status
    if args.connectors:
        updates["connectors"] = [c.strip() for c in args.connectors.split(",")]

    if not updates:
        print("No updates specified. Use --name, --description, --model, --system-prompt, --connectors, etc.")
        return

    result = client.update_agent(args.agent_id, **updates)
    print(f"Agent {args.agent_id} updated:")
    print(json.dumps(result, indent=2, default=str))


def cmd_channels(args):
    """List all channels."""
    client = get_client(args)
    channels = client.list_channels()
    print(f"\n{'='*80}")
    print(f"Channels ({len(channels)} total)")
    print(f"{'='*80}")
    for ch in channels:
        ch_type = ch.get("type", "unknown")
        name = ch.get("name", ch.get("id", "unknown"))
        print(f"  [{ch_type:<8}] {name:<35} ID: {ch['id']}")
        if ch.get("description"):
            print(f"             {ch['description'][:60]}")
    print()


def cmd_channel(args):
    """Show channel details."""
    client = get_client(args)
    channel = client.get_channel(args.channel_id)
    print(json.dumps(channel, indent=2, default=str))


def cmd_chat(args):
    """Send a message to an agent and wait for response."""
    client = get_client(args)
    agent_id = args.agent_id
    message = args.message

    if not message:
        # Interactive mode
        print(f"Chat with agent '{agent_id}' (Ctrl+C to quit)")
        print(f"{'='*60}")
        while True:
            try:
                message = input("\nYou: ").strip()
                if not message:
                    continue
                print(f"\nSending to {agent_id}...")
                response = client.chat(agent_id, message, timeout=args.timeout)
                print(f"\nAgent: {response}")
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
        return

    # Single message mode
    print(f"Sending to {agent_id}: {message[:60]}{'...' if len(message) > 60 else ''}")

    if args.raw:
        # Return full thread data
        channel_id = f"dm-{agent_id}"
        result = client.send_message_and_wait(channel_id, message, timeout=args.timeout)
        print(json.dumps(result, indent=2, default=str))
    else:
        response = client.chat(agent_id, message, timeout=args.timeout)
        print(f"\n{'='*60}")
        print(response)
        print(f"{'='*60}")


def cmd_threads(args):
    """List threads in a channel."""
    client = get_client(args)
    threads = client.list_threads(args.channel_id, limit=args.limit)
    print(f"\n{'='*80}")
    print(f"Threads in {args.channel_id} ({len(threads)} shown)")
    print(f"{'='*80}")
    for t in threads:
        state = t.get("state", "unknown")
        title = t.get("title", "untitled")[:60]
        msg_count = t.get("messageCount", 0)
        score = t.get("score", "")
        created = t.get("createdAt", "")[:19]
        print(f"  [{state:<12}] {title}")
        print(f"    ID: {t['id']}  msgs: {msg_count}  score: {score}  created: {created}")
        print()


def cmd_thread(args):
    """Show thread messages."""
    client = get_client(args)
    thread = client.get_thread(args.channel_id, args.thread_id)

    print(f"\n{'='*80}")
    print(f"Thread: {thread.get('title', 'untitled')}")
    print(f"State: {thread.get('state', 'unknown')}  Score: {thread.get('score', '')}")
    print(f"{'='*80}\n")

    messages = thread.get("messages", {}).get("data", [])
    if not messages:
        messages = client.get_thread_messages(args.channel_id, args.thread_id)

    for msg in messages:
        role = msg.get("role", "unknown")
        created = msg.get("createdAt", "")[:19]
        print(f"--- {role.upper()} [{created}] ---")
        for part in msg.get("parts", []):
            if part.get("type") == "text":
                print(part.get("text", ""))
            elif part.get("type") == "tool_use":
                tool_name = part.get("toolName", "unknown")
                print(f"  [Tool: {tool_name}]")
            elif part.get("type") == "tool_result":
                print(f"  [Tool result: {str(part.get('result', ''))[:200]}]")
        print()


def cmd_activity(args):
    """Show recent activity."""
    client = get_client(args)
    activities = client.get_activity(limit=args.limit, lookback=args.lookback)
    print(f"\n{'='*80}")
    print(f"Activity ({len(activities)} items, lookback={args.lookback})")
    print(f"{'='*80}")
    for act in activities:
        title = act.get("title", act.get("threadTitle", "untitled"))[:60]
        channel = act.get("channelId", "unknown")
        state = act.get("state", "")
        updated = act.get("lastActivityAt", act.get("updatedAt", ""))[:19]
        print(f"  [{state:<12}] {title}")
        print(f"    channel: {channel}  updated: {updated}")
        print()


def cmd_models(args):
    """List available AI models."""
    creds = get_credentials(args)
    if not creds.get("api_token"):
        print("Error: API token required for models endpoint. Set ED_API_TOKEN.")
        sys.exit(1)

    client = get_client(args)
    models = client.list_models(api_token=creds["api_token"])
    print(f"\n{'='*80}")
    print(f"Available AI Models ({len(models)} total)")
    print(f"{'='*80}")
    for m in models:
        name = m if isinstance(m, str) else m.get("name", m.get("id", str(m)))
        print(f"  - {name}")
    print()


def cmd_agent_tools(args):
    """Show the MCP tools assigned to an agent."""
    client = get_client(args)
    tools = client.get_agent_tools(args.agent_id)

    # Group by connector
    by_connector = {}
    for t in tools:
        conn = t.get("connector", "unknown")
        by_connector.setdefault(conn, []).append(t)

    print(f"\n{'='*80}")
    print(f"MCP Tools for agent {args.agent_id} ({len(tools)} tools)")
    print(f"{'='*80}")
    for connector, connector_tools in by_connector.items():
        print(f"\n  [{connector}] ({len(connector_tools)} tools)")
        for t in connector_tools:
            status = t.get("status", "active")
            name = t.get("toolName", "unknown")
            print(f"    [{status:<8}] {name}")
    print()


def cmd_clone_agent(args):
    """Clone an existing agent."""
    client = get_client(args)
    overrides = {}
    if args.description:
        overrides["description"] = args.description
    if args.system_prompt:
        overrides["system_prompt"] = args.system_prompt
    if args.model:
        overrides["model"] = args.model
    if args.temperature is not None:
        overrides["temperature"] = args.temperature

    print(f"Cloning agent {args.agent_id} as '{args.new_name}'...")
    agent = client.clone_agent(args.agent_id, args.new_name, **overrides)
    print(f"\nAgent cloned successfully!")
    print(f"  ID:    {agent['id']}")
    print(f"  Name:  {agent.get('name', args.new_name)}")
    print(f"  Model: {agent.get('model', 'inherited')}")
    print(f"  DM Channel: dm-{agent['id']}")


def cmd_search_threads(args):
    """Search threads across all channels."""
    client = get_client(args)
    results = client.search_threads(
        lookback=args.lookback,
        state=args.state,
        limit=args.limit,
    )
    print(f"\n{'='*80}")
    state_str = f", state={args.state}" if args.state else ""
    print(f"Thread Search ({len(results)} results, lookback={args.lookback}{state_str})")
    print(f"{'='*80}")
    for r in results:
        title = r.get("title", r.get("threadTitle", "untitled"))[:60]
        channel = r.get("channelId", "unknown")
        state = r.get("state", "")
        updated = r.get("lastActivityAt", r.get("updatedAt", ""))[:19]
        print(f"  [{state:<12}] {title}")
        print(f"    channel: {channel}  updated: {updated}")
        print()


def cmd_connectors(args):
    """List available connectors."""
    creds = get_credentials(args)
    if not creds.get("api_token"):
        print("Error: API token required for connectors endpoint. Set ED_API_TOKEN.")
        sys.exit(1)

    client = get_client(args)
    connectors = client.list_connectors(api_token=creds["api_token"])
    print(f"\n{'='*80}")
    print("Available Connectors")
    print(f"{'='*80}")
    if isinstance(connectors, list):
        for c in connectors:
            name = c if isinstance(c, str) else c.get("name", str(c))
            print(f"  - {name}")
    else:
        print(json.dumps(connectors, indent=2, default=str))
    print()


def cmd_integrations(args):
    """List all integrations."""
    client = get_client(args)
    integrations = client.list_integrations()
    print(f"\n{'='*80}")
    print(f"Integrations ({len(integrations)} total)")
    print(f"{'='*80}")
    for i in integrations:
        name = i.get("name", "unknown")
        display = i.get("displayName", "")
        itype = i.get("type", "unknown")
        status = i.get("eventConnectorConnectionStatus", "unknown")
        creator = i.get("creator", "")
        label = f"{display} ({name})" if display and display != name else name
        print(f"  [{itype:<15}] {label:<40} status: {status}")
        if creator:
            print(f"{'':>20} created by: {creator}")
    print()


def cmd_create_integration(args):
    """Create a new integration/connector."""
    client = get_client(args)
    auth_data = {"authType": args.auth_type}
    if args.server_url:
        auth_data["serverUrl"] = args.server_url
    if args.token:
        auth_data["token"] = args.token

    print(f"Creating integration '{args.name}' (type={args.connector_type})...")
    result = client.create_integration(
        connector_type=args.connector_type,
        name=args.name,
        display_name=args.display_name or args.name,
        auth_data=auth_data,
    )
    print(f"\nIntegration created!")
    print(f"  Name: {result.get('name', args.name)}")
    print(f"  Type: {result.get('type', args.connector_type)}")
    print(f"  Display: {result.get('displayName', '')}")
    print(f"\nAdd to agent: python ai_team_cli.py update-agent <agent_id> --connectors edgedelta-mcp,edgedelta-documentation,{args.name}")


def cmd_delete_integration(args):
    """Delete an integration."""
    client = get_client(args)
    if not args.force:
        confirm = input(f"Delete integration '{args.name}'? (y/N): ")
        if confirm.lower() != "y":
            print("Cancelled.")
            return
    success = client.delete_integration(args.name)
    print(f"{'Deleted' if success else 'Failed to delete'} integration '{args.name}'")


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EdgeDelta AI Team CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Global options
    parser.add_argument("--org-id", help="Organization ID")
    parser.add_argument("--api-token", help="API token")
    parser.add_argument("--jwt", help="JWT token")
    parser.add_argument("--env-file", help="Path to .env file")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # login
    p_login = subparsers.add_parser("login", help="Login and get JWT")
    p_login.add_argument("--email", help="Email address")
    p_login.add_argument("--password", help="Password")

    # status
    subparsers.add_parser("status", help="Check auth status")

    # agents
    subparsers.add_parser("agents", help="List all agents")

    # agent <id>
    p_agent = subparsers.add_parser("agent", help="Show agent details")
    p_agent.add_argument("agent_id", help="Agent ID")

    # create-agent
    p_create = subparsers.add_parser("create-agent", help="Create a custom agent")
    p_create.add_argument("name", help="Agent name")
    p_create.add_argument("--description", help="Agent description")
    p_create.add_argument("--system-prompt", help="System prompt text")
    p_create.add_argument("--prompt-file", help="Read system prompt from file")
    p_create.add_argument("--model", default="claude-opus-4-5-20250414", help="LLM model")
    p_create.add_argument("--role", help="Agent role title")
    p_create.add_argument("--capabilities", help="Comma-separated capabilities")
    p_create.add_argument("--connectors", help="Comma-separated connector names")
    p_create.add_argument("--temperature", type=float, default=0.1, help="Model temperature")
    p_create.add_argument("--priority", type=int, default=10, help="Agent priority")
    p_create.add_argument("--avatar", default="", help="Avatar URL or identifier")

    # delete-agent
    p_delete = subparsers.add_parser("delete-agent", help="Delete a custom agent")
    p_delete.add_argument("agent_id", help="Agent ID to delete")
    p_delete.add_argument("--force", action="store_true", help="Skip confirmation")

    # update-agent
    p_update = subparsers.add_parser("update-agent", help="Update an agent")
    p_update.add_argument("agent_id", help="Agent ID to update")
    p_update.add_argument("--name", help="New name")
    p_update.add_argument("--description", help="New description")
    p_update.add_argument("--model", help="New model")
    p_update.add_argument("--system-prompt", help="New system prompt")
    p_update.add_argument("--prompt-file", help="Read system prompt from file")
    p_update.add_argument("--temperature", type=float, help="New temperature")
    p_update.add_argument("--status", choices=["active", "inactive"], help="New status")
    p_update.add_argument("--connectors", help="Comma-separated connector names (replaces current list)")

    # agent-tools
    p_agent_tools = subparsers.add_parser("agent-tools", help="Show MCP tools for an agent")
    p_agent_tools.add_argument("agent_id", help="Agent ID")

    # clone-agent
    p_clone = subparsers.add_parser("clone-agent", help="Clone an existing agent")
    p_clone.add_argument("agent_id", help="Source agent ID to clone")
    p_clone.add_argument("new_name", help="Name for the cloned agent")
    p_clone.add_argument("--description", help="Override description")
    p_clone.add_argument("--system-prompt", help="Override system prompt")
    p_clone.add_argument("--model", help="Override model")
    p_clone.add_argument("--temperature", type=float, help="Override temperature")

    # search-threads
    p_search = subparsers.add_parser("search-threads", help="Search threads across all channels")
    p_search.add_argument("--lookback", default="7d", help="Time window (e.g. 1h, 24h, 7d)")
    p_search.add_argument("--state", choices=["investigating", "resolved", "done"], help="Filter by state")
    p_search.add_argument("--limit", type=int, default=50, help="Max results")

    # channels
    subparsers.add_parser("channels", help="List all channels")

    # channel <id>
    p_channel = subparsers.add_parser("channel", help="Show channel details")
    p_channel.add_argument("channel_id", help="Channel ID")

    # chat
    p_chat = subparsers.add_parser("chat", help="Chat with an agent")
    p_chat.add_argument("agent_id", help="Agent ID (e.g. sre, security-engineer, or UUID)")
    p_chat.add_argument("--message", "-m", help="Message to send (omit for interactive mode)")
    p_chat.add_argument("--timeout", type=int, default=120, help="Response timeout seconds")
    p_chat.add_argument("--raw", action="store_true", help="Show raw thread data")

    # threads
    p_threads = subparsers.add_parser("threads", help="List threads in a channel")
    p_threads.add_argument("channel_id", help="Channel ID")
    p_threads.add_argument("--limit", type=int, default=20, help="Max threads to show")

    # thread
    p_thread = subparsers.add_parser("thread", help="Show thread messages")
    p_thread.add_argument("channel_id", help="Channel ID")
    p_thread.add_argument("thread_id", help="Thread ID")

    # activity
    p_activity = subparsers.add_parser("activity", help="Show recent activity")
    p_activity.add_argument("--limit", type=int, default=20, help="Max items")
    p_activity.add_argument("--lookback", default="7d", help="Lookback period")

    # models
    subparsers.add_parser("models", help="List available AI models")

    # connectors
    subparsers.add_parser("connectors", help="List available connectors")

    # integrations
    subparsers.add_parser("integrations", help="List all integrations")

    # create-integration
    p_create_int = subparsers.add_parser("create-integration", help="Create a new integration/connector")
    p_create_int.add_argument("connector_type", help="Connector type (custom-mcp, slack, sentry, etc.)")
    p_create_int.add_argument("name", help="Unique integration name")
    p_create_int.add_argument("--display-name", help="Human-readable display name")
    p_create_int.add_argument("--server-url", help="MCP server URL (for custom-mcp)")
    p_create_int.add_argument("--auth-type", default="none", choices=["none", "token", "oAuth"], help="Authentication type")
    p_create_int.add_argument("--token", help="Bearer token (when auth-type is token)")

    # delete-integration
    p_del_int = subparsers.add_parser("delete-integration", help="Delete an integration")
    p_del_int.add_argument("name", help="Integration name to delete")
    p_del_int.add_argument("--force", action="store_true", help="Skip confirmation")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "login": cmd_login,
        "status": cmd_status,
        "agents": cmd_agents,
        "agent": cmd_agent,
        "create-agent": cmd_create_agent,
        "delete-agent": cmd_delete_agent,
        "update-agent": cmd_update_agent,
        "channels": cmd_channels,
        "channel": cmd_channel,
        "chat": cmd_chat,
        "threads": cmd_threads,
        "thread": cmd_thread,
        "activity": cmd_activity,
        "models": cmd_models,
        "connectors": cmd_connectors,
        "integrations": cmd_integrations,
        "create-integration": cmd_create_integration,
        "delete-integration": cmd_delete_integration,
        "agent-tools": cmd_agent_tools,
        "clone-agent": cmd_clone_agent,
        "search-threads": cmd_search_threads,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
