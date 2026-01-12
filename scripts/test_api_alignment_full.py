
import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add project root to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(PROJECT_ROOT)

from services.deploy import app

client = TestClient(app)

def test_routes():
    print("Testing API routes...")
    existing_routes = {route.path for route in app.routes}
    
    expected_endpoints = [
        "/", "/health", "/config", # Core
        "/models", "/embeddings", # Models
        "/chat", "/v1/chat/completions", "/generate", # Chat
        "/.well-known/agent.json", "/a2a/discover", # A2A
        "/tools/search", "/tools/analyze-url", # Tools
        "/lore/sync/status", # Lore
        "/orchestrator/jobs/queue", "/orchestrator/jobs/job_123", # Orchestrator
        "/auth/start/google", "/auth/accounts" # Auth
    ]

    missing = []
    for endpoint in expected_endpoints:
        # Check if endpoint matches any registered route path
        # Note: registered routes might have path params like {job_id}
        # We'll do a simple substring check or exact match
        found = False
        for route in existing_routes:
            if route == endpoint:
                found = True
                break
            # Handle path params simply for this test
            if "{" in route:
                base_route = route.split("{")[0]
                if endpoint.startswith(base_route):
                    found = True
                    break
        
        if not found:
            missing.append(endpoint)
            print(f"❌ Missing: {endpoint}")
        else:
            print(f"✅ Found: {endpoint}")

    if missing:
        print(f"\nFAILED: Missing {len(missing)} endpoints.")
        sys.exit(1)
    else:
        print("\nSUCCESS: All expected endpoints found.")

def test_health():
    print("\nTesting /health endpoint...")
    try:
        response = client.get("/health")
        if response.status_code == 200:
            print(f"✅ /health returned 200: {response.json()}")
        else:
            print(f"❌ /health returned {response.status_code}: {response.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ /health failed with exception: {e}")
        sys.exit(1)

def main():
    test_routes()
    test_health()

if __name__ == "__main__":
    main()
