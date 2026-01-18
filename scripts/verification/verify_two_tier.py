"""
Verification script for Two-Tier Reasoning on Vertex AI (Mocked).
"""

import asyncio
import sys
import os
import json
import types

# Ensure we can import from the root (Robust)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# --- MOCK GOOGLE GENAI SDK ---
# We must mock this BEFORE importing services.reasoning.two_tier
# so that "from google.genai import types" succeeds.

mock_genai = types.ModuleType("google.genai")
mock_types = types.ModuleType("google.genai.types")

# Mock the classes used in two_tier.py
class MockConfig:
    def __init__(self, **kwargs): pass
mock_types.GenerateContentConfig = MockConfig
mock_types.ThinkingConfig = MockConfig
mock_types.UploadFileConfig = MockConfig

mock_genai.types = mock_types
sys.modules["google"] = types.ModuleType("google")
sys.modules["google.genai"] = mock_genai
sys.modules["google.genai.types"] = mock_types

# Now safe to import
from services.reasoning import TwoTierReasoner


class MockResponse:
    def __init__(self, text):
        self.text = text

class MockModels:
    async def generate_content(self, model, contents, config=None):
        print(f"  [Mock] Call to {model}...")
        if "pro" in model or "thinking_level=\"high\"" in str(config): 
            return MockResponse(json.dumps({
                "goal": "Mock Goal - Fix auth",
                "steps": ["Identify bug", "Write test", "Fix code"],
                "constraints": ["No downtime"], 
                "success_criteria": "Tests pass",
                "estimated_complexity": 3
            }))
        else: 
            return MockResponse("Mock execution output.")

class MockAio:
    def __init__(self):
        self.models = MockModels()

class MockClient:
    def __init__(self):
        self.aio = MockAio()

async def test_two_tier_reasoning():
    print("=" * 60)
    print("TWO-TIER REASONING VERIFICATION (MOCKED)")
    print("=" * 60)
    
    # Initialize reasoner
    reasoner = TwoTierReasoner()
    
    # INJECT MOCK CLIENT
    print("Injecting Mock Client...")
    reasoner.client = MockClient()
    
    # Test 1: High-level planning
    print("\n--- TEST 1: High-Level Planning (Gemini Pro) ---")
    
    plan = await reasoner.plan("Fix a bug in the authentication module", context="Python Flask")
    
    print(f"Goal: {plan.goal}")
    print(f"Steps: {len(plan.steps)}")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step}")
    
    # Test 2: Low-level execution
    print("\n--- TEST 2: Low-Level Execution (Gemini Flash) ---")
    
    result = await reasoner.execute(
        instruction="Write a Python function",
        context="Flask application"
    )
    print(f"Result preview: {result[:100]}...")
    
    # Test 3: Full reasoning pipeline
    print("\n--- TEST 3: Full Two-Tier Reasoning ---")
    
    plan, results = await reasoner.reason(
        goal="Add rate limiting",
        auto_execute=True
    )
    
    print(f"Plan steps: {len(plan.steps)}")
    print(f"Execution results: {len(results)}")
    
    # Get stats
    stats = reasoner.get_tier_stats()
    print(f"\n--- Tier Statistics ---")
    print(f"Total steps: {stats['total_steps']}")
    
    if len(plan.steps) > 0 and len(results) > 0:
        print("\n" + "=" * 60)
        print("TWO-TIER REASONING VERIFICATION COMPLETE ✅")
        print("=" * 60)
    else:
        print("❌ Planning or Execution failed.")

if __name__ == "__main__":
    asyncio.run(test_two_tier_reasoning())
