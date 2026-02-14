# Edge Delta AI Agents Enhancement

Adds **20 new MCP tools** to the [EdgeDelta MCP Server](https://github.com/edgedelta/edgedelta-mcp-server) for AI Team agent management, chat, and activity monitoring.

The official MCP server has 22 tools for observability data (logs, metrics, traces, pipelines, dashboards). This enhancement extends it with full programmatic access to Edge Delta's **AI Team** system - the agents, the chat, the channels - everything that was previously only available through the browser UI.

---

## What This Adds

| Capability | Before | After |
|---|---|---|
| Total MCP tools | 22 | **42** |
| Create AI agents | Browser UI only (15 steps) | **1 API call** |
| Chat with agents | Browser UI only | **1 API call** |
| List/manage agents | Browser UI only | **Programmatic** |
| Monitor activity | Browser UI only | **Programmatic** |
| Batch operations | Not possible | **Script anything** |
| CI/CD integration | Not possible | **Fully supported** |
| Scheduled agent tasks | Not possible | **Cron + script** |

---

## The 20 New Tools

### Agent Management
| Tool | What it does |
|---|---|
| `get_agents` | List all AI agents (built-in + custom) |
| `get_agent` | Get full agent details (system prompt, model, tools, config) |
| `create_agent` | Create a custom AI agent with any model, prompt, and connectors |
| `update_agent` | Update agent name, prompt, model, temperature, status |
| `delete_agent` | Delete a custom agent |
| `get_agent_tools` | List the MCP tools assigned to a specific agent |
| `clone_agent` | Duplicate an existing agent with a new name and optional overrides |

### Chat
| Tool | What it does |
|---|---|
| `chat_agent` | Send a message to any agent and get the response back |
| `create_thread` | Send a message without waiting (fire-and-forget) |
| `get_thread` | Get a thread with all its messages, state, and score |
| `get_thread_messages` | Get just the messages from a thread |
| `get_threads` | List recent threads in a channel |
| `mark_thread_read` | Mark a thread as read |
| `search_threads` | Search threads across all channels by time window and state |

### Channels & Activity
| Tool | What it does |
|---|---|
| `get_channels` | List all channels (alerts, code-issues, security-issues, agent DMs) |
| `get_channel` | Get channel details |
| `get_activity` | Get activity feed (all agent interactions) |
| `get_badge_count` | Get unread notification count |

### Models & Connectors
| Tool | What it does |
|---|---|
| `get_ai_models` | List available models (Claude, GPT, Mistral, Llama) |
| `get_ai_connectors` | List connectors that agents can use |

---

## How It Works

Edge Delta's AI Team runs on **3 API domains**:

| Domain | What | Auth |
|---|---|---|
| `api.edgedelta.com` | Main API (auth, models, connectors) | API Token |
| `chat.ai.edgedelta.com` | Chat (threads, messages, channels, activity) | JWT |
| `agent.ai.edgedelta.com` | Agents (create, update, delete, list) | JWT |

The official MCP server only covers the first one. This enhancement covers all three.

### Authentication

The chat and agent APIs require a JWT (not the API token). Getting one:

```
1. POST api.edgedelta.com/auth/login         -> session cookies
2. GET  api.edgedelta.com/v1/cookie_service/get_jwt_from_cookie  -> JWT
```

The client library handles this automatically:

```python
auth = EdgeDeltaAuth(org_id, api_token)
jwt = auth.login(email, password)
client = AITeamClient(org_id, jwt)
```

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/hlsitechio/edgedelta-ai-agents-enhancement.git
cd edgedelta-ai-agents-enhancement
pip install requests
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your Edge Delta credentials
```

### 3. Verify

```bash
python3 ai_team_cli.py status
```

### 4. Try it

```bash
# List all agents
python3 ai_team_cli.py agents

# Chat with the SRE agent
python3 ai_team_cli.py chat sre -m "Give me a quick status summary"

# Create a custom agent
python3 ai_team_cli.py create-agent "My Agent" \
    --model claude-opus-4-5-20250414 \
    --system-prompt "You are a helpful observability assistant"

# Run the full test suite
python3 test_ai_team.py --env-file .env
```

---

## Creating an Agent: Before vs After

### Before (Browser UI) - 15+ steps

1. Open browser
2. Go to app.edgedelta.com
3. Sign in
4. Wait for load
5. Click AI Team
6. Click Teammates
7. Click Create
8. Type agent name
9. Type description
10. Select model from dropdown
11. Write system prompt
12. Select connectors
13. Set temperature
14. Set priority
15. Click Create

Then to chat: navigate to DM, type message, click send, wait.

**Creating 5 agents = 75+ clicks. Automating it = impossible.**

### After (This Enhancement) - 1 call

```python
agent = client.create_agent(
    name="Security Recon",
    description="Threat analysis using observability data",
    system_prompt="You are a security specialist...",
    model="claude-opus-4-5-20250414",
)
response = client.chat(agent["id"], "Scan for threats in the last 24h")
```

**Creating 5 agents = a loop. Automating it = trivial.**

---

## Files

| File | What |
|---|---|
| `ai_team_client.py` | Core Python client - all API calls |
| `ai_team_cli.py` | CLI tool - 18 commands |
| `ai_team_mcp_tools.py` | 20 MCP tool definitions + handler |
| `test_ai_team.py` | Test suite - 16 automated tests |
| `agent_prompts.py` | 6 ready-to-deploy agent templates |
| `quick_start.py` | End-to-end demo script |
| `AI_TEAM_API_REFERENCE.md` | Full API reference |
| `.env.example` | Config template |

---

## Agent Templates

6 pre-built agents ready to deploy:

| Template | What it does |
|---|---|
| `security-recon` | Threat analysis, IOC detection, attack surface mapping |
| `log-analyst` | Log pattern detection, anomaly identification |
| `metrics-monitor` | Performance analysis, alerting thresholds |
| `incident-responder` | Incident investigation, root cause, remediation |
| `pipeline-advisor` | Pipeline design and optimization |
| `cost-optimizer` | Volume analysis, cost reduction |

```python
from agent_prompts import create_agent_from_template
agent = create_agent_from_template(client, "security-recon")
```

---

## Built-in Agents

Edge Delta ships with 13 agents:

| Agent | Model | Purpose |
|-------|-------|---------|
| SRE | Claude Opus 4.5 | Site reliability |
| Security Engineer | Claude Opus 4.5 | Security analysis |
| Oncall AI | GPT-5.2 | Triage and routing |
| Work Tracker | Claude Opus 4.5 | Task tracking |
| Code Analyzer | GPT-5.2 | Code analysis |
| + 8 internal agents | GPT-5.2 | Scoring, summarizing, routing |

---

## Writing System Prompts

The system prompt (`masterPrompt`) is the most important part of an agent. It defines what the agent does, how it thinks, and what tools it uses.

### Prompt Structure

A good Edge Delta agent prompt has 4 sections:

```
1. Identity      - Who you are and what platform you're on
2. Capabilities  - What you can do with Edge Delta's tools
3. Approach      - Step-by-step methodology
4. Output Format - How to structure responses
```

### Example

```python
agent = client.create_agent(
    name="Log Analyst",
    description="Deep log analysis and pattern detection",
    system_prompt="""You are a Log Analysis Expert on the Edge Delta observability platform.

## Capabilities
- Search logs using Edge Delta's log search
- Identify error patterns and root causes
- Detect anomalous log volumes
- Correlate events across services

## Approach
1. Start with broad log searches to understand the data
2. Narrow down using patterns, time ranges, filters
3. Use log pattern analysis to group similar events
4. Identify root causes by tracing event chains

## Output Format
- **Summary**: What was found
- **Patterns**: Specific patterns identified
- **Root Cause**: Most likely cause with evidence
- **Recommendations**: Next steps
""",
    model="claude-opus-4-5-20250414",
    temperature=0.1,
)
```

See `agent_prompts.py` for 6 complete, ready-to-deploy prompt templates.

---

## Choosing a Model

Edge Delta supports multiple LLM providers. Pick based on your use case:

| Model | Best For | Speed | Cost |
|-------|----------|-------|------|
| `claude-opus-4-5-20250414` | Complex analysis, security, reasoning | Slower | Higher |
| `gpt-5.2` | General purpose, fast triage, routing | Fast | Medium |
| `mistral-large-latest` | EU data residency, multilingual | Fast | Lower |
| `llama-3-70b` | Self-hosted, privacy-sensitive workloads | Fast | Lowest |

```python
# List all available models in your org
models = client.list_models(api_token="your-api-token")
```

**Rules of thumb:**
- **Security analysis, incident response** → Claude Opus 4.5 (best reasoning)
- **Triage, routing, quick answers** → GPT-5.2 (fast, good enough)
- **Cost-sensitive batch operations** → Mistral or Llama
- **Temperature**: Keep at `0.1` for factual analysis, use `0.2-0.3` for creative tasks

---

## Periodic / Scheduled Tasks

Agents can be triggered on a schedule using cron, CI/CD, or any task scheduler. Since everything is an API call, automation is straightforward.

### Cron Example

```bash
# Every hour: ask the SRE agent for a health check
0 * * * * cd /path/to/repo && python3 -c "
from ai_team_client import AITeamClient
client = AITeamClient('YOUR_ORG_ID', 'YOUR_JWT')
print(client.chat('sre', 'Give me a quick health check of all systems'))
" >> /var/log/ed-health.log 2>&1
```

### Daily Security Scan

```python
#!/usr/bin/env python3
"""Daily security scan - run via cron at 6 AM."""
from ai_team_client import AITeamClient

client = AITeamClient("YOUR_ORG_ID", "YOUR_JWT")

# Ask security agent to scan last 24 hours
response = client.chat(
    "security-engineer",
    "Scan all logs from the last 24 hours for security threats, "
    "suspicious IPs, failed auth attempts, and anomalies. "
    "Provide a severity-ranked summary."
)
print(response)
```

### CI/CD Integration

```yaml
# GitHub Actions - post-deploy verification
- name: Verify deployment
  run: |
    pip install requests
    python3 -c "
    from ai_team_client import AITeamClient
    client = AITeamClient('${{ secrets.ED_ORG_ID }}', '${{ secrets.ED_JWT }}')
    result = client.chat('sre', 'Check if the latest deployment caused any errors in the last 15 minutes')
    print(result)
    "
```

### Batch Operations

```python
# Create 5 specialized agents in a loop
templates = ["security-recon", "log-analyst", "metrics-monitor",
             "incident-responder", "cost-optimizer"]

from agent_prompts import create_agent_from_template
for name in templates:
    agent = create_agent_from_template(client, name)
    print(f"Created: {agent['name']} ({agent['id']})")
```

**Note:** JWTs expire after ~10 hours. For long-running scheduled tasks, include a login step to refresh the JWT before making API calls.

---

## How We Found the APIs

The AI Team APIs are not publicly documented. We found them by inspecting network traffic from the Edge Delta web app using browser developer tools:

1. **Open Edge Delta** in Chrome, press **F12** > **Network tab**
2. **Navigate to AI Team** - see requests to `chat.ai.edgedelta.com` and `agent.ai.edgedelta.com`
3. **Log in** - see the auth flow: `POST /auth/login` -> cookies -> `GET /cookie_service/get_jwt_from_cookie` -> JWT
4. **Send a message** - see the thread creation: `POST /channels/{id}/threads` with `{"clientTempId":"...","title":"message"}`
5. **Create a teammate** - see the agent creation: `POST /agents` with full config payload

Anyone with an Edge Delta account can verify this in under 5 minutes.

---

## How to Verify

```bash
# Run the automated test suite - creates agent, chats, verifies, cleans up
python3 test_ai_team.py --org-id <your-org> --email <your-email> --password <your-pass>
```

Or manually with curl:

```bash
# Get JWT
curl -s -c cookies.txt -X POST https://api.edgedelta.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"you@example.com","password":"yourpass"}'

JWT=$(curl -s -b cookies.txt https://api.edgedelta.com/v1/cookie_service/get_jwt_from_cookie | python3 -c "import sys,json; print(json.load(sys.stdin)['bearer_token'])")

# List agents
curl -s https://agent.ai.edgedelta.com/v1/orgs/YOUR_ORG_ID/agents \
  -H "Authorization: Bearer $JWT" | python3 -m json.tool
```

---

## Integration with EdgeDelta MCP Server

The official [edgedelta-mcp-server](https://github.com/edgedelta/edgedelta-mcp-server) is written in Go. To integrate these tools:

1. Port `ai_team_client.py` to Go (matching their `pkg/tools/` pattern)
2. Add JWT auth alongside existing API token auth
3. Register new tools in `server/server.go` via `AddCustomTools()`
4. Add `chat.ai.edgedelta.com` and `agent.ai.edgedelta.com` as API targets

The tool definitions in `ai_team_mcp_tools.py` provide the exact schemas for Go implementation.

---

## Known Limitations

- **JWT expires** after ~10 hours - needs refresh for long-running processes
- **Polling, not streaming** - responses are polled via HTTP (the UI uses WebSockets)
- **Rate limits** - undocumented, avoid aggressive polling
- **Go port needed** - official server is Go, this reference implementation is Python

---

## License

MIT
