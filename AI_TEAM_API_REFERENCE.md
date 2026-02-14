# EdgeDelta AI Team API Reference

Complete API documentation for Edge Delta's AI Team system.
Covers all 3 API domains, authentication flows, and data schemas.

## API Domains

| Domain | Purpose | Auth Method |
|--------|---------|-------------|
| `api.edgedelta.com` | Main API (auth, orgs, config) | `X-ED-API-Token` header |
| `chat.ai.edgedelta.com` | Chat API (threads, messages, channels) | `Bearer JWT` |
| `agent.ai.edgedelta.com` | Agent API (agent CRUD, periodic jobs) | `Bearer JWT` |

## Authentication

### Method 1: API Token (Main API only)
```
Header: X-ED-API-Token: <token>
```
Works for `api.edgedelta.com` endpoints. Does NOT work for chat.ai or agent.ai.

### Method 2: Bearer JWT (Chat & Agent APIs)
```
Header: Authorization: Bearer <jwt>
```
Required for `chat.ai.edgedelta.com` and `agent.ai.edgedelta.com`.

### Getting a JWT

**Option A: Email/Password Login**
```
POST https://api.edgedelta.com/auth/login
Body: {"username": "email@example.com", "password": "password"}
```
Returns session cookies, then:
```
GET https://api.edgedelta.com/v1/cookie_service/get_jwt_from_cookie
Cookies: <session cookies from login>
```
Returns: `{"bearer_token": "<JWT>"}`

**Option B: From Browser Session**
If already logged in via browser, cookies can be used to get JWT via the cookie_service endpoint.

## Agent API

Base: `https://agent.ai.edgedelta.com/v1/orgs/{org_id}`

### List Agents
```
GET /agents
Response: {"data": [<agent>, ...]}
```

### Create Agent
```
POST /agents
Body: {
    "name": "Agent Name",
    "description": "What it does",
    "masterPrompt": "System prompt...",
    "model": "claude-opus-4-5-20250414",
    "modelTemperature": 0.1,
    "status": "active",
    "priority": 10,
    "type": "custom",
    "capabilities": [],
    "connectors": ["edgedelta-mcp", "edgedelta-documentation"],
    "userPrompt": "{{#if memory_context}}\n{{{ memory_context }}}\n\n---\n\n{{/if}}\n{{{ question }}}"
}
Response: {"data": <created_agent>}
```

### Update Agent
```
PUT /agents/{agent_id}
Body: {<fields to update>}
Response: {"data": <updated_agent>}
```

### Delete Agent
```
DELETE /agents/{agent_id}
Response: 200 or 204
```

### Agent Object Fields
```json
{
    "id": "01XXXX...",
    "name": "Agent Name",
    "description": "Description",
    "avatar": "",
    "masterPrompt": "System prompt...",
    "userPrompt": "{{#if memory_context}}...",
    "model": "claude-opus-4-5-20250414",
    "modelTemperature": 0.1,
    "status": "active",
    "priority": 10,
    "type": "custom|default",
    "role": "Role Title",
    "capabilities": [],
    "connectors": ["edgedelta-mcp"],
    "toolConfigurations": [
        {
            "toolName": "get_log_search",
            "connector": "edgedelta-mcp",
            "status": "active"
        }
    ],
    "createdAt": "2026-02-13T...",
    "updatedAt": "2026-02-13T..."
}
```

### Known Models
- `claude-opus-4-5-20250414` (Claude Opus 4.5)
- `gpt-5.2` (GPT-5.2)
- `mistral-large-latest` (Mistral Large)
- `llama-3-70b` (Llama 3 70B)

### Known Connectors
- `edgedelta-mcp` - EdgeDelta MCP tools (log search, metrics, pipelines, etc.)
- `edgedelta-documentation` - EdgeDelta docs search

## Chat API

Base: `https://chat.ai.edgedelta.com/v1/orgs/{org_id}`

### List Channels
```
GET /channels
Response: {"data": [<channel>, ...]}
```

### Get Channel
```
GET /channels/{channel_id}
Response: {"data": <channel>}
```

### Channel Types
- Regular channels: `alerts`, `code-issues`, `security-issues`
- DM channels: `dm-sre`, `dm-security-engineer`, `dm-{agent_uuid}`
- Internal DMs: `dm-system`

### Create Thread (Send Message)
```
POST /channels/{channel_id}/threads
Body: {
    "clientTempId": "thread:{random_string}",
    "title": "Your message text goes here"
}
Response: {"data": <thread>}
```

**Important**: The `title` field IS the user's message. The `clientTempId` is required.

### Get Thread
```
GET /channels/{channel_id}/threads/{thread_id}?messageLimit=10000
Response: {"data": <thread_with_messages>}
```

### Get Thread Messages
```
GET /channels/{channel_id}/threads/{thread_id}/messages
Response: {"data": [<message>, ...]}
```

### List Threads
```
GET /channels/{channel_id}/threads?limit=20&messageLimit=10000
Response: {"data": [<thread>, ...]}
```

### Mark Thread Read
```
POST /channels/{channel_id}/threads/{thread_id}/mark-read
```

### Thread Object Fields
```json
{
    "id": "01XXXX...",
    "title": "User's message",
    "state": "investigating|resolved|done",
    "score": 92,
    "severity": "low|medium|high|critical",
    "messageCount": 2,
    "createdAt": "2026-02-13T...",
    "updatedAt": "2026-02-13T...",
    "participants": [...],
    "messages": {"data": [<message>, ...]},
    "summary": "Thread summary text",
    "tags": [...]
}
```

### Message Object Fields
```json
{
    "id": "01XXXX...",
    "role": "user|agent",
    "createdAt": "2026-02-13T...",
    "parts": [
        {"type": "text", "text": "Message content"},
        {"type": "tool_use", "toolName": "get_log_search", "input": {...}},
        {"type": "tool_result", "result": {...}}
    ]
}
```

## Activity API

Base: `https://chat.ai.edgedelta.com/v1/orgs/{org_id}`

### Get Activity Feed
```
GET /activity?limit=20&sort=last-activity&lookback=7d
GET /activity?limit=20&sort=last-activity&lookback=7d&channelId=dm-sre
Response: {"data": [<activity_item>, ...]}
```

### Get Badge Count
```
GET /activity/aggregate-badge-count?lookback=7d
Response: {"totalUnread": 5, ...}
```

## Main API (AI Endpoints)

Base: `https://api.edgedelta.com/v1/orgs/{org_id}`

### List AI Models
```
GET /ai/models
Headers: X-ED-API-Token: <token>
Response: {"models": [...]}
```

### List AI Connectors
```
GET /ai/connectors
Headers: X-ED-API-Token: <token>
Response: [...]
```

## Default Agents (Built-in)

| Agent | Model | Type | Purpose |
|-------|-------|------|---------|
| SRE | Claude Opus 4.5 | default | Site reliability engineering |
| Security Engineer | Claude Opus 4.5 | default | Security analysis |
| Oncall AI | GPT-5.2 | default | Triage and routing (super agent) |
| Work Tracker | Claude Opus 4.5 | default | Task tracking |
| Channel Determiner | GPT-5.2 | default | Route messages to channels |
| Code Analyzer | GPT-5.2 | default | Code analysis |
| Connector Creator | GPT-5.2 | default | Create MCP connectors |
| Event Normalizer | GPT-5.2 | default | Normalize events |
| Importance Evaluator | GPT-5.2 | default | Score thread importance |
| Result Evaluator | GPT-5.2 | default | Evaluate agent results |
| Teammate Creator | GPT-5.2 | default | Create new agents |
| Thread Summarizer | GPT-5.2 | default | Summarize threads |
| Thread Title Determiner | GPT-5.2 | default | Generate thread titles |

## Error Handling

- `400` - Bad request (check payload format)
- `401` - Unauthorized (JWT expired or invalid)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found (wrong endpoint or ID)
- `500` - Server error (check for known issues like persisting_cursor_settings)

## Rate Limits

No explicit rate limits documented, but recommended:
- Poll no faster than every 5 seconds
- Limit concurrent thread creation
- Cache agent/channel lists (they change infrequently)
