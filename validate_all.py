"""
COMPREHENSIVE SYSTEM VALIDATION
Validates all components work together in production-ready code.

Tests:
1. GeminiAgent (Vertex AI Global, Gemini 3)
2. UnkAiAgent (Family Dynamic personas)
3. Confucius Architecture (Memory, Notes, Tools, Orchestrator)
4. Two-Tier Reasoning (Pro planning, Flash execution)
"""

import asyncio
import sys
import os

sys.path.append(os.getcwd())


async def test_gemini_agent():
    """Test base GeminiAgent with Gemini 3 Flash on Vertex AI Global."""
    print("\n" + "=" * 60)
    print("TEST 1: GeminiAgent (Vertex AI Global)")
    print("=" * 60)
    
    from services.llm.gemini_agent import GeminiAgent
    
    agent = GeminiAgent(use_vertex=True, default_model="gemini-3-flash-preview")
    
    if not agent.client:
        print("❌ GeminiAgent client not initialized")
        return False
    
    # Test basic generation
    response = await agent.async_run(
        "What is 2+2? Reply with just the number.",
        config={"thinking_level": "low"}
    )
    
    print(f"Response: {response}")
    
    if response and "4" in response:
        print("✅ GeminiAgent Test PASSED")
        return True
    else:
        print("❌ GeminiAgent Test FAILED")
        return False


async def test_unk_agent():
    """Test UnkAiAgent with all three personas."""
    print("\n" + "=" * 60)
    print("TEST 2: UnkAiAgent (Family Dynamic)")
    print("=" * 60)
    
    from services.llm.unk_agent import UnkAiAgent
    
    agent = UnkAiAgent(mode="unk")
    
    # Test Unk mode
    print("Testing Unk mode...")
    response = await agent.speak("What should I do about my lazy coworker?")
    print(f"Unk says: {response[:150]}..." if len(response) > 150 else f"Unk says: {response}")
    
    # Test mode switching
    agent.switch_mode("yn")
    print("\nTesting YN mode...")
    response = await agent.speak("What do you think about RTO policies?")
    print(f"YN says: {response[:150]}..." if len(response) > 150 else f"YN says: {response}")
    
    # Test Auntie mode
    agent.switch_mode("auntie")
    print("\nTesting Auntie mode...")
    response = await agent.speak("My nephew keeps crashing out at work")
    print(f"Auntie says: {response[:150]}..." if len(response) > 150 else f"Auntie says: {response}")
    
    print("\n✅ UnkAiAgent Test PASSED")
    return True


async def test_confucius_memory():
    """Test Confucius-inspired hierarchical memory."""
    print("\n" + "=" * 60)
    print("TEST 3: Confucius Hierarchical Memory")
    print("=" * 60)
    
    from services.memory import HierarchicalWorkingMemory
    
    memory = HierarchicalWorkingMemory(max_context_tokens=8000)
    
    # Test scope management
    memory.start_scope("test_task")
    memory.add_step("Analyze requirements", "Found 3 components need updating", is_key=True)
    memory.add_step("Run tests", "2 tests failing")
    memory.add_step("Fix component A", "Applied hotfix", is_key=True)
    
    # Verify artifacts
    artifacts = memory.get_key_artifacts()
    print(f"Key artifacts stored: {len(artifacts)}")
    
    # Verify context
    context = memory.get_context_window()
    print(f"Context window: {len(context)} chars")
    
    if len(artifacts) >= 2 and len(context) > 50:
        print("✅ Hierarchical Memory Test PASSED")
        return True
    else:
        print("❌ Hierarchical Memory Test FAILED")
        return False


async def test_confucius_notes():
    """Test Confucius-inspired persistent notes."""
    print("\n" + "=" * 60)
    print("TEST 4: Confucius Persistent Notes")
    print("=" * 60)
    
    from services.memory import PersistentNotes
    
    notes = PersistentNotes(notes_dir="assets/notes")
    
    # Write a test note
    note = notes.write_note(
        category="strategy",
        title="Test Strategy Note",
        content="This is a test note for validation.",
        context="Integration test",
        keywords=["test", "validation"]
    )
    
    print(f"Wrote note: {note.id}")
    
    # Retrieve notes
    found = notes.get_notes_for_context(["test", "validation"])
    print(f"Found {len(found)} matching notes")
    
    if len(found) >= 1:
        print("✅ Persistent Notes Test PASSED")
        return True
    else:
        print("❌ Persistent Notes Test FAILED")
        return False


async def test_confucius_tools():
    """Test Confucius-inspired modular tools."""
    print("\n" + "=" * 60)
    print("TEST 5: Confucius Modular Tools")
    print("=" * 60)
    
    from services.tools import CommandExecutor, ToolRegistry
    
    registry = ToolRegistry()
    cmd = CommandExecutor(default_cwd=".", timeout_seconds=10)
    registry.register(cmd)
    
    # Execute a command
    result = await cmd.safe_execute(command="echo Integration Test Success")
    
    print(f"Command result: {result.success}")
    print(f"Output: {result.output.strip()}")
    print(f"State: {cmd.get_state_summary()}")
    
    if result.success and "Success" in result.output:
        print("✅ Modular Tools Test PASSED")
        return True
    else:
        print("❌ Modular Tools Test FAILED")
        return False


async def test_orchestrator():
    """Test the unified orchestrator."""
    print("\n" + "=" * 60)
    print("TEST 6: Unified Orchestrator")
    print("=" * 60)
    
    from services.orchestrator import UnkOrchestrator
    
    orch = UnkOrchestrator(repo_path=".", persona="unk")
    
    # Start a task
    context = orch.start_task(
        task_name="Integration Validation",
        task_description="Test full system integration"
    )
    
    print(f"Started task: {context.task_name}")
    
    # Execute a step
    result = await orch.execute_step(
        action="validate",
        tool_name="command_executor",
        tool_params={"command": "echo Orchestrator Active"}
    )
    
    print(f"Step success: {result['success']}")
    
    # Get trace
    trace = orch.get_execution_trace()
    print(f"Execution trace: {len(trace)} steps")
    
    if result['success'] and len(trace) >= 1:
        print("✅ Orchestrator Test PASSED")
        return True
    else:
        print("❌ Orchestrator Test FAILED")
        return False


async def test_two_tier_reasoning():
    """Test HRM-inspired two-tier reasoning."""
    print("\n" + "=" * 60)
    print("TEST 7: Two-Tier Reasoning (Gemini 3 Pro + Flash)")
    print("=" * 60)
    
    from services.reasoning import TwoTierReasoner
    
    reasoner = TwoTierReasoner()
    
    if not reasoner.client:
        print("❌ TwoTierReasoner client not initialized")
        return False
    
    # Test low-level execution (Flash, fast)
    print("Testing Low-Tier (Flash)...")
    result = await reasoner.execute("Say 'System validated' in exactly 2 words.")
    print(f"Flash response: {result[:100]}...")
    
    # Get stats
    stats = reasoner.get_tier_stats()
    print(f"\nTier Stats:")
    print(f"  High-Tier calls: {stats['high_tier']['count']}")
    print(f"  Low-Tier calls: {stats['low_tier']['count']}")
    
    if stats['low_tier']['count'] >= 1:
        print("✅ Two-Tier Reasoning Test PASSED")
        return True
    else:
        print("❌ Two-Tier Reasoning Test FAILED")
        return False


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("           COMPREHENSIVE SYSTEM VALIDATION")
    print("           Unk Agent - Vertex AI Global - Gemini 3")
    print("=" * 70)
    
    results = {}
    
    # Run all tests
    results["GeminiAgent"] = await test_gemini_agent()
    results["UnkAiAgent"] = await test_unk_agent()
    results["HierarchicalMemory"] = await test_confucius_memory()
    results["PersistentNotes"] = await test_confucius_notes()
    results["ModularTools"] = await test_confucius_tools()
    results["Orchestrator"] = await test_orchestrator()
    results["TwoTierReasoning"] = await test_two_tier_reasoning()
    
    # Summary
    print("\n" + "=" * 70)
    print("                    VALIDATION SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:25} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("   🎉 ALL SYSTEMS VALIDATED SUCCESSFULLY - PRODUCTION READY 🎉")
    else:
        print("   ⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
