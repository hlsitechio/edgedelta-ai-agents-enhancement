#!/usr/bin/env python3
"""
EdgeDelta AI Team MCP Tool Definitions
Defines tool schemas for the EdgeDelta MCP server to expose AI Team functionality.

These tool definitions can be added to the edgedelta-mcp-server to provide
AI Team agent management, chat, and monitoring capabilities.

Tool Categories:
    - Agent Management: create, list, get, update, delete, clone agents, get agent tools
    - Chat: send messages, get responses, manage threads, search threads
    - Channels: list channels, get channel info
    - Activity: monitor agent activity, badge counts
    - Models: list available AI models
"""

# Tool definitions following MCP tool schema format
AI_TEAM_TOOLS = [
    # ── Agent Management ─────────────────────────────────────
    {
        "name": "ai_team_list_agents",
        "description": "List all AI Team agents in the organization. Returns agent names, IDs, models, status, and types.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ai_team_get_agent",
        "description": "Get detailed information about a specific AI Team agent including its system prompt, model, connectors, and tool configurations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "The agent ID (UUID or short name like 'sre', 'security-engineer')",
                },
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "ai_team_create_agent",
        "description": "Create a new custom AI Team agent with specified name, model, system prompt, and connectors. The agent will automatically be assigned EdgeDelta MCP tools.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Display name for the agent (e.g., 'Log Analyzer')",
                },
                "description": {
                    "type": "string",
                    "description": "Short description of what the agent does",
                },
                "system_prompt": {
                    "type": "string",
                    "description": "Full system prompt / master prompt with agent instructions",
                },
                "model": {
                    "type": "string",
                    "description": "LLM model to use. Options: claude-opus-4-5-20250414, gpt-5.2, mistral-large-latest, llama-3-70b",
                    "default": "claude-opus-4-5-20250414",
                },
                "role": {
                    "type": "string",
                    "description": "Role title (e.g., 'Security Specialist')",
                },
                "connectors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Connector names (default: edgedelta-mcp, edgedelta-documentation)",
                },
                "temperature": {
                    "type": "number",
                    "description": "Model temperature 0.0-1.0 (default: 0.1)",
                    "default": 0.1,
                },
            },
            "required": ["name", "description", "system_prompt"],
        },
    },
    {
        "name": "ai_team_update_agent",
        "description": "Update an existing AI Team agent's configuration. Only provide fields you want to change.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID to update",
                },
                "name": {"type": "string", "description": "New display name"},
                "description": {"type": "string", "description": "New description"},
                "system_prompt": {"type": "string", "description": "New system prompt"},
                "model": {"type": "string", "description": "New model"},
                "temperature": {"type": "number", "description": "New temperature"},
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive"],
                    "description": "Agent status",
                },
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "ai_team_delete_agent",
        "description": "Delete a custom AI Team agent. Built-in agents cannot be deleted.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID to delete",
                },
            },
            "required": ["agent_id"],
        },
    },
    # ── Chat ─────────────────────────────────────────────────
    {
        "name": "ai_team_chat",
        "description": "Send a message to an AI Team agent and wait for the response. This creates a new thread and polls until the agent responds.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID to chat with (e.g., 'sre', 'security-engineer', or custom agent UUID)",
                },
                "message": {
                    "type": "string",
                    "description": "Message to send to the agent",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Max seconds to wait for response (default: 120)",
                    "default": 120,
                },
            },
            "required": ["agent_id", "message"],
        },
    },
    {
        "name": "ai_team_create_thread",
        "description": "Create a new thread (send a message) in a channel without waiting for response. Returns thread ID for later polling.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "string",
                    "description": "Channel ID (e.g., 'dm-sre', 'dm-security-engineer', 'dm-{agent_uuid}')",
                },
                "message": {
                    "type": "string",
                    "description": "Message to send",
                },
            },
            "required": ["channel_id", "message"],
        },
    },
    {
        "name": "ai_team_get_thread",
        "description": "Get a thread with its messages, state, score, and metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "string",
                    "description": "Channel ID",
                },
                "thread_id": {
                    "type": "string",
                    "description": "Thread ID",
                },
            },
            "required": ["channel_id", "thread_id"],
        },
    },
    {
        "name": "ai_team_get_thread_messages",
        "description": "Get all messages from a specific thread.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "Channel ID"},
                "thread_id": {"type": "string", "description": "Thread ID"},
            },
            "required": ["channel_id", "thread_id"],
        },
    },
    {
        "name": "ai_team_list_threads",
        "description": "List recent threads in a channel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "Channel ID"},
                "limit": {
                    "type": "integer",
                    "description": "Max threads to return (default: 20)",
                    "default": 20,
                },
            },
            "required": ["channel_id"],
        },
    },
    # ── Channels ─────────────────────────────────────────────
    {
        "name": "ai_team_list_channels",
        "description": "List all AI Team channels including regular channels (alerts, code-issues, security-issues) and DM channels for each agent.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ai_team_get_channel",
        "description": "Get detailed information about a specific channel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "Channel ID"},
            },
            "required": ["channel_id"],
        },
    },
    # ── Activity ─────────────────────────────────────────────
    {
        "name": "ai_team_get_activity",
        "description": "Get recent AI Team activity feed showing threads, messages, and agent interactions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max items (default: 20)",
                    "default": 20,
                },
                "lookback": {
                    "type": "string",
                    "description": "Lookback period (default: 7d)",
                    "default": "7d",
                },
                "channel_id": {
                    "type": "string",
                    "description": "Filter by channel ID (optional)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "ai_team_get_badge_count",
        "description": "Get aggregate badge count for unread AI Team notifications.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lookback": {
                    "type": "string",
                    "description": "Lookback period (default: 7d)",
                    "default": "7d",
                },
            },
            "required": [],
        },
    },
    # ── Models ───────────────────────────────────────────────
    {
        "name": "ai_team_list_models",
        "description": "List available AI models that can be used for agents.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ai_team_list_connectors",
        "description": "List available AI connectors (MCP tools, documentation sources) that agents can use.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    # ── Agent Tools ─────────────────────────────────────────────
    {
        "name": "ai_team_get_agent_tools",
        "description": "Get the MCP tools assigned to a specific agent. Returns the tool configurations including tool name, connector, and status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID to get tools for",
                },
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "ai_team_clone_agent",
        "description": "Clone an existing agent with a new name. Copies all configuration (prompt, model, connectors, temperature, etc.) from the source agent. Any field can be overridden.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Source agent ID to clone from",
                },
                "new_name": {
                    "type": "string",
                    "description": "Name for the cloned agent",
                },
                "description": {"type": "string", "description": "Override description (optional)"},
                "system_prompt": {"type": "string", "description": "Override system prompt (optional)"},
                "model": {"type": "string", "description": "Override model (optional)"},
                "temperature": {"type": "number", "description": "Override temperature (optional)"},
            },
            "required": ["agent_id", "new_name"],
        },
    },
    {
        "name": "ai_team_search_threads",
        "description": "Search threads across all channels. Filter by time window and thread state (investigating, resolved, done).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lookback": {
                    "type": "string",
                    "description": "Time window (e.g. '1h', '24h', '7d'). Default: '7d'",
                    "default": "7d",
                },
                "state": {
                    "type": "string",
                    "enum": ["investigating", "resolved", "done"],
                    "description": "Filter by thread state (optional)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 50)",
                    "default": 50,
                },
            },
            "required": [],
        },
    },
]


def tool_handler(tool_name: str, args: dict, client) -> dict:
    """
    Handle MCP tool calls by dispatching to the AITeamClient.

    Args:
        tool_name: The MCP tool name
        args: Tool arguments
        client: AITeamClient instance

    Returns:
        Tool result dict
    """
    handlers = {
        "ai_team_list_agents": lambda: client.list_agents(),
        "ai_team_get_agent": lambda: client.get_agent(args["agent_id"]),
        "ai_team_create_agent": lambda: client.create_agent(
            name=args["name"],
            description=args["description"],
            system_prompt=args["system_prompt"],
            model=args.get("model", "claude-opus-4-5-20250414"),
            role=args.get("role", ""),
            connectors=args.get("connectors"),
            temperature=args.get("temperature", 0.1),
        ),
        "ai_team_update_agent": lambda: client.update_agent(
            args["agent_id"],
            **{k: v for k, v in args.items() if k != "agent_id" and v is not None},
        ),
        "ai_team_delete_agent": lambda: client.delete_agent(args["agent_id"]),
        "ai_team_chat": lambda: client.chat(
            args["agent_id"],
            args["message"],
            timeout=args.get("timeout", 120),
        ),
        "ai_team_create_thread": lambda: client.create_thread(
            args["channel_id"],
            args["message"],
        ),
        "ai_team_get_thread": lambda: client.get_thread(
            args["channel_id"],
            args["thread_id"],
        ),
        "ai_team_get_thread_messages": lambda: client.get_thread_messages(
            args["channel_id"],
            args["thread_id"],
        ),
        "ai_team_list_threads": lambda: client.list_threads(
            args["channel_id"],
            limit=args.get("limit", 20),
        ),
        "ai_team_list_channels": lambda: client.list_channels(),
        "ai_team_get_channel": lambda: client.get_channel(args["channel_id"]),
        "ai_team_get_activity": lambda: client.get_activity(
            limit=args.get("limit", 20),
            lookback=args.get("lookback", "7d"),
            channel_id=args.get("channel_id"),
        ),
        "ai_team_get_badge_count": lambda: client.get_badge_count(
            lookback=args.get("lookback", "7d"),
        ),
        "ai_team_list_models": lambda: client.list_models(),
        "ai_team_list_connectors": lambda: client.list_connectors(),
        "ai_team_get_agent_tools": lambda: client.get_agent_tools(args["agent_id"]),
        "ai_team_clone_agent": lambda: client.clone_agent(
            args["agent_id"],
            args["new_name"],
            **{k: v for k, v in args.items() if k not in ("agent_id", "new_name") and v is not None},
        ),
        "ai_team_search_threads": lambda: client.search_threads(
            lookback=args.get("lookback", "7d"),
            state=args.get("state"),
            limit=args.get("limit", 50),
        ),
    }

    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        result = handler()
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


def print_tool_manifest():
    """Print the tool definitions as JSON for MCP registration."""
    import json
    print(json.dumps({"tools": AI_TEAM_TOOLS}, indent=2))


if __name__ == "__main__":
    print_tool_manifest()
