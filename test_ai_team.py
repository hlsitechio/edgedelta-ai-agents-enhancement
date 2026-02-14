#!/usr/bin/env python3
"""
EdgeDelta AI Team API Test Suite
Verifies all discovered endpoints work correctly.

Usage:
    python3 test_ai_team.py --org-id <id> --jwt <token> [--api-token <token>]
    python3 test_ai_team.py --env-file <path>

Tests:
    1. Agent API (agent.ai.edgedelta.com)
       - List agents
       - Get agent details
       - Create custom agent
       - Update agent
       - Delete agent

    2. Chat API (chat.ai.edgedelta.com)
       - List channels
       - Get channel details
       - Create thread (send message)
       - Get thread
       - Get thread messages
       - List threads
       - Get activity
       - Get badge count

    3. Main API (api.edgedelta.com)
       - List models
       - List connectors
"""

import json
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ai_team_client import AITeamClient, EdgeDeltaAuth, CHAT_API, AGENT_API, MAIN_API


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []

    def test(self, name: str, func, *args, **kwargs):
        """Run a test and record result."""
        print(f"  Testing: {name}...", end=" ", flush=True)
        try:
            result = func(*args, **kwargs)
            if result is not None:
                self.passed += 1
                self.results.append(("PASS", name, None))
                print("PASS")
                return result
            else:
                self.failed += 1
                self.results.append(("FAIL", name, "Returned None"))
                print("FAIL (returned None)")
                return None
        except Exception as e:
            self.failed += 1
            self.results.append(("FAIL", name, str(e)))
            print(f"FAIL ({e})")
            return None

    def skip(self, name: str, reason: str):
        self.skipped += 1
        self.results.append(("SKIP", name, reason))
        print(f"  Testing: {name}... SKIP ({reason})")

    def report(self):
        print(f"\n{'='*80}")
        print("TEST RESULTS")
        print(f"{'='*80}")
        for status, name, detail in self.results:
            icon = {"PASS": "[OK]", "FAIL": "[!!]", "SKIP": "[--]"}[status]
            line = f"  {icon} {name}"
            if detail:
                line += f" - {detail}"
            print(line)
        print(f"\n  Passed: {self.passed}  Failed: {self.failed}  Skipped: {self.skipped}")
        print(f"{'='*80}")
        return self.failed == 0


def load_env(path: str) -> dict:
    env = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def run_tests(org_id: str, jwt: str, api_token: str = None):
    runner = TestRunner()
    client = AITeamClient(org_id, jwt)

    print(f"\n{'='*80}")
    print(f"EdgeDelta AI Team API Tests")
    print(f"Org: {org_id}")
    print(f"JWT: {jwt[:20]}...")
    print(f"{'='*80}")

    # ── Agent API Tests ──────────────────────────────────────
    print(f"\n--- Agent API (agent.ai.edgedelta.com) ---")

    agents = runner.test("List agents", client.list_agents)
    if agents:
        print(f"    Found {len(agents)} agents")

        # Pick first agent for detail test
        first_agent = agents[0]
        agent_detail = runner.test(
            f"Get agent '{first_agent['name']}'",
            client.get_agent,
            first_agent["id"],
        )

    # Create a test agent
    test_agent = runner.test(
        "Create custom agent",
        client.create_agent,
        name="Test Agent (auto-cleanup)",
        description="Temporary test agent - will be deleted",
        system_prompt="You are a test agent. Reply with 'Test successful' to any message.",
        model="claude-opus-4-5-20250414",
        temperature=0.1,
    )

    test_agent_id = None
    cloned_agent_id = None
    if test_agent:
        test_agent_id = test_agent["id"]
        print(f"    Created agent: {test_agent_id}")

        # Update agent
        runner.test(
            "Update agent description",
            client.update_agent,
            test_agent_id,
            description="Updated test description",
        )

        # Get agent tools
        tools = runner.test(
            "Get agent tools",
            client.get_agent_tools,
            test_agent_id,
        )
        if tools is not None:
            print(f"    Found {len(tools)} tool configurations")

        # Clone agent
        cloned = runner.test(
            "Clone agent",
            client.clone_agent,
            test_agent_id,
            "Cloned Test Agent (auto-cleanup)",
        )
        cloned_agent_id = None
        if cloned:
            cloned_agent_id = cloned["id"]
            print(f"    Cloned as: {cloned_agent_id}")

    # ── Chat API Tests ───────────────────────────────────────
    print(f"\n--- Chat API (chat.ai.edgedelta.com) ---")

    channels = runner.test("List channels", client.list_channels)
    if channels:
        print(f"    Found {len(channels)} channels")

        # Get first channel details
        first_ch = channels[0]
        runner.test(
            f"Get channel '{first_ch.get('name', first_ch['id'])}'",
            client.get_channel,
            first_ch["id"],
        )

        # List threads in first DM channel
        dm_channels = [ch for ch in channels if ch.get("type") == "dm" or ch["id"].startswith("dm-")]
        if dm_channels:
            dm_ch = dm_channels[0]
            threads = runner.test(
                f"List threads in '{dm_ch['id']}'",
                client.list_threads,
                dm_ch["id"],
                5,
            )
            if threads and len(threads) > 0:
                first_thread = threads[0]
                runner.test(
                    f"Get thread '{first_thread['id'][:20]}...'",
                    client.get_thread,
                    dm_ch["id"],
                    first_thread["id"],
                )

    # Activity
    activity = runner.test("Get activity", client.get_activity, 5, "7d")
    if activity:
        print(f"    Found {len(activity)} activity items")

    # Search threads
    search_results = runner.test(
        "Search threads",
        client.search_threads,
        "7d",
        None,
        10,
    )
    if search_results is not None:
        print(f"    Found {len(search_results)} threads")

    badge = runner.test("Get badge count", client.get_badge_count)
    if badge:
        print(f"    Badge data: {json.dumps(badge)[:80]}")

    # ── Send a test message ──────────────────────────────────
    print(f"\n--- Message Test ---")

    if test_agent_id:
        # Send message to our test agent
        channel_id = f"dm-{test_agent_id}"
        thread = runner.test(
            "Create thread (send message)",
            client.create_thread,
            channel_id,
            "Test message - please respond with 'Test successful'",
        )
        if thread:
            thread_id = thread["id"]
            print(f"    Thread: {thread_id} (state: {thread.get('state', '?')})")

            # Wait briefly for response
            print("    Waiting 15s for response...", flush=True)
            time.sleep(15)

            thread_data = runner.test(
                "Get thread with messages",
                client.get_thread,
                channel_id,
                thread_id,
            )
            if thread_data:
                state = thread_data.get("state", "unknown")
                msg_count = thread_data.get("messageCount", 0)
                print(f"    State: {state}, Messages: {msg_count}")

            messages = runner.test(
                "Get thread messages",
                client.get_thread_messages,
                channel_id,
                thread_id,
            )
            if messages:
                print(f"    Got {len(messages)} messages")
                for msg in messages:
                    role = msg.get("role", "?")
                    text_parts = []
                    for part in msg.get("parts", []):
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", "")[:100])
                    if text_parts:
                        print(f"    [{role}]: {text_parts[0]}")

    else:
        runner.skip("Create thread", "No test agent created")

    # ── Main API Tests ───────────────────────────────────────
    print(f"\n--- Main API (api.edgedelta.com) ---")

    if api_token:
        models = runner.test("List AI models", client.list_models, api_token)
        if models:
            print(f"    Found {len(models)} models")

        connectors = runner.test("List connectors", client.list_connectors, api_token)
        if connectors:
            count = len(connectors) if isinstance(connectors, list) else "?"
            print(f"    Found {count} connectors")
    else:
        runner.skip("List AI models", "No API token provided")
        runner.skip("List connectors", "No API token provided")

    # ── Cleanup ──────────────────────────────────────────────
    print(f"\n--- Cleanup ---")

    if test_agent_id:
        deleted = runner.test(
            "Delete test agent",
            client.delete_agent,
            test_agent_id,
        )
        if deleted:
            print(f"    Cleaned up agent {test_agent_id}")
    else:
        runner.skip("Delete test agent", "No test agent to clean up")

    if cloned_agent_id:
        deleted = runner.test(
            "Delete cloned agent",
            client.delete_agent,
            cloned_agent_id,
        )
        if deleted:
            print(f"    Cleaned up cloned agent {cloned_agent_id}")
    else:
        runner.skip("Delete cloned agent", "No cloned agent to clean up")

    # ── Report ───────────────────────────────────────────────
    success = runner.report()
    return success


def main():
    parser = argparse.ArgumentParser(description="Test EdgeDelta AI Team API")
    parser.add_argument("--org-id", help="Organization ID")
    parser.add_argument("--jwt", help="JWT token")
    parser.add_argument("--api-token", help="API token for main API")
    parser.add_argument("--env-file", help="Path to .env file")
    parser.add_argument("--email", help="Email for login")
    parser.add_argument("--password", help="Password for login")
    args = parser.parse_args()

    org_id = args.org_id
    jwt = args.jwt
    api_token = args.api_token

    # Load from env file
    if args.env_file:
        env = load_env(args.env_file)
        org_id = org_id or env.get("ED_ORG_ID") or env.get("EDGEDELTA_ORG_ID")
        api_token = api_token or env.get("ED_API_TOKEN") or env.get("ED_ORG_API_TOKEN")
        jwt = jwt or env.get("ED_JWT")

    # Try environment variables
    import os
    org_id = org_id or os.environ.get("ED_ORG_ID")
    api_token = api_token or os.environ.get("ED_API_TOKEN")
    jwt = jwt or os.environ.get("ED_JWT")

    if not org_id:
        print("Error: org_id required. Use --org-id or set ED_ORG_ID")
        sys.exit(1)

    # Login if needed
    if not jwt and args.email and args.password:
        print("Logging in to get JWT...")
        auth = EdgeDeltaAuth(org_id, api_token or "")
        jwt = auth.login(args.email, args.password)
        print(f"JWT obtained: {jwt[:30]}...")

    if not jwt:
        print("Error: JWT required. Use --jwt, set ED_JWT, or provide --email/--password")
        sys.exit(1)

    success = run_tests(org_id, jwt, api_token)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
