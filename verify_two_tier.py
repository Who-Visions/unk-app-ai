"""
Verification script for Two-Tier Reasoning on Vertex AI.
"""

import asyncio
import sys
import os

sys.path.append(os.getcwd())

async def test_two_tier_reasoning():
    print("=" * 60)
    print("TWO-TIER REASONING VERIFICATION")
    print("=" * 60)
    
    from services.reasoning import TwoTierReasoner
    
    # Initialize reasoner
    reasoner = TwoTierReasoner()
    
    if not reasoner.client:
        print("❌ Vertex AI client not initialized")
        return
    
    # Test 1: High-level planning
    print("\n--- TEST 1: High-Level Planning (Gemini Pro) ---")
    goal = "Fix a bug in the authentication module that causes token expiry errors"
    
    plan = await reasoner.plan(goal, context="Python Flask application with JWT authentication")
    
    print(f"Goal: {plan.goal}")
    print(f"Steps: {len(plan.steps)}")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step}")
    print(f"Complexity: {plan.estimated_complexity}/10")
    print(f"Success Criteria: {plan.success_criteria}")
    
    # Test 2: Low-level execution
    print("\n--- TEST 2: Low-Level Execution (Gemini Flash) ---")
    
    result = await reasoner.execute(
        instruction="Write a Python function to validate JWT token expiry",
        context="Flask application using PyJWT library"
    )
    print(f"Result preview: {result[:300]}...")
    
    # Test 3: Full reasoning pipeline
    print("\n--- TEST 3: Full Two-Tier Reasoning ---")
    
    plan, results = await reasoner.reason(
        goal="Add rate limiting to an API endpoint",
        context="FastAPI application",
        auto_execute=False  # Just plan, don't execute all steps
    )
    
    print(f"Plan steps: {len(plan.steps)}")
    
    # Get stats
    stats = reasoner.get_tier_stats()
    print(f"\n--- Tier Statistics ---")
    print(f"High-Tier calls: {stats['high_tier']['count']} (avg {stats['high_tier']['avg_latency_ms']:.0f}ms)")
    print(f"Low-Tier calls: {stats['low_tier']['count']} (avg {stats['low_tier']['avg_latency_ms']:.0f}ms)")
    print(f"Total steps: {stats['total_steps']}")
    
    print("\n" + "=" * 60)
    print("TWO-TIER REASONING VERIFICATION COMPLETE ✅")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_two_tier_reasoning())
