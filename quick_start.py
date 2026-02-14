#!/usr/bin/env python3
"""
EdgeDelta AI Team Quick Start
Demonstrates the full API workflow: auth -> agents -> chat -> custom agent.

Usage:
    python3 quick_start.py

Requires ED_ORG_ID and either ED_JWT or (ED_EMAIL + ED_PASSWORD) in environment.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ai_team_client import AITeamClient, EdgeDeltaAuth
from agent_prompts import PROMPTS, create_agent_from_template, list_templates


def main():
    # ── Get credentials ──────────────────────────────────────
    org_id = os.environ.get("ED_ORG_ID")
    jwt = os.environ.get("ED_JWT")
    api_token = os.environ.get("ED_API_TOKEN")
    email = os.environ.get("ED_EMAIL")
    password = os.environ.get("ED_PASSWORD")

    # Try .env file
    env_path = Path("G:/edge delta/.env")
    if not org_id and env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k == "ED_ORG_ID":
                        org_id = v
                    elif k in ("ED_API_TOKEN", "ED_ORG_API_TOKEN"):
                        api_token = v
                    elif k == "ED_JWT":
                        jwt = v
                    elif k == "ED_EMAIL":
                        email = v
                    elif k == "ED_PASSWORD":
                        password = v

    if not org_id:
        print("Set ED_ORG_ID environment variable or create G:/edge delta/.env")
        sys.exit(1)

    # ── Authenticate ─────────────────────────────────────────
    if not jwt and email and password:
        print("Logging in...")
        auth = EdgeDeltaAuth(org_id, api_token or "")
        jwt = auth.login(email, password)
        print(f"JWT obtained")

    if not jwt:
        print("Set ED_JWT or ED_EMAIL+ED_PASSWORD")
        sys.exit(1)

    client = AITeamClient(org_id, jwt)

    # ── 1. List agents ───────────────────────────────────────
    print(f"\n{'='*60}")
    print("1. LISTING AGENTS")
    print(f"{'='*60}")
    agents = client.list_agents()
    for a in agents:
        print(f"  [{a.get('type', '?'):<8}] {a['name']:<30} model={a.get('model', '?')}")

    # ── 2. List channels ─────────────────────────────────────
    print(f"\n{'='*60}")
    print("2. LISTING CHANNELS")
    print(f"{'='*60}")
    channels = client.list_channels()
    for ch in channels:
        print(f"  [{ch.get('type', '?'):<8}] {ch.get('name', ch['id'])}")

    # ── 3. Check activity ────────────────────────────────────
    print(f"\n{'='*60}")
    print("3. RECENT ACTIVITY")
    print(f"{'='*60}")
    activity = client.get_activity(limit=5)
    for act in activity:
        title = act.get("title", act.get("threadTitle", "?"))[:50]
        state = act.get("state", "?")
        print(f"  [{state:<12}] {title}")

    # ── 4. Chat with SRE agent ───────────────────────────────
    print(f"\n{'='*60}")
    print("4. CHATTING WITH SRE AGENT")
    print(f"{'='*60}")
    print("  Sending: 'Give me a quick status summary'")
    response = client.chat("sre", "Give me a quick status summary", timeout=90)
    print(f"  Response ({len(response)} chars):")
    # Show first 500 chars
    print(f"  {response[:500]}{'...' if len(response) > 500 else ''}")

    # ── 5. Available templates ───────────────────────────────
    print(f"\n{'='*60}")
    print("5. AVAILABLE AGENT TEMPLATES")
    print(f"{'='*60}")
    for t in list_templates():
        print(f"  {t['name']:<25} {t['description'][:50]}")

    # ── 6. Create custom agent from template ─────────────────
    print(f"\n{'='*60}")
    print("6. CREATING CUSTOM AGENT (log-analyst template)")
    print(f"{'='*60}")
    agent = create_agent_from_template(client, "log-analyst")
    print(f"  Created: {agent['name']} (ID: {agent['id']})")
    print(f"  DM Channel: dm-{agent['id']}")

    # ── 7. Chat with custom agent ────────────────────────────
    print(f"\n{'='*60}")
    print("7. CHATTING WITH CUSTOM AGENT")
    print(f"{'='*60}")
    print("  Sending: 'What log sources are available?'")
    response = client.chat(agent["id"], "What log sources are available?", timeout=90)
    print(f"  Response ({len(response)} chars):")
    print(f"  {response[:500]}{'...' if len(response) > 500 else ''}")

    # ── 8. Cleanup ───────────────────────────────────────────
    print(f"\n{'='*60}")
    print("8. CLEANUP")
    print(f"{'='*60}")
    deleted = client.delete_agent(agent["id"])
    print(f"  Deleted test agent: {'OK' if deleted else 'FAILED'}")

    print(f"\n{'='*60}")
    print("QUICK START COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
