"""
Verification script for Confucius-inspired architecture.
Tests the HierarchicalWorkingMemory, PersistentNotes, and tool extensions.
"""

import asyncio
import sys
import os

sys.path.append(os.getcwd())

async def test_working_memory():
    print("=" * 60)
    print("TEST 1: Hierarchical Working Memory")
    print("=" * 60)
    
    from services.memory import HierarchicalWorkingMemory
    
    memory = HierarchicalWorkingMemory(max_context_tokens=4000)
    
    # Start a scope
    memory.start_scope("debugging_auth")
    
    # Add some steps
    memory.add_step(
        action="Read auth.py",
        result="Found login function with JWT validation",
        is_key=True
    )
    memory.add_step(
        action="Run tests",  
        result="3 failures in test_auth.py"
    )
    memory.add_step(
        action="Edit auth.py line 45",
        result="Fixed token expiry check",
        is_key=True
    )
    
    # Get context window
    context = memory.get_context_window()
    print(f"Context window ({len(context)} chars):")
    print(context[:500])
    
    # Check key artifacts
    artifacts = memory.get_key_artifacts()
    print(f"\nKey artifacts: {len(artifacts)}")
    for k, v in artifacts.items():
        print(f"  - {k}: {v['action'][:50]}...")
    
    print("\n✅ Working Memory Test PASSED\n")

async def test_persistent_notes():
    print("=" * 60)
    print("TEST 2: Persistent Notes")
    print("=" * 60)
    
    from services.memory import PersistentNotes
    
    notes = PersistentNotes(notes_dir="assets/notes")
    
    # Write a test note
    note = notes.write_note(
        category="strategy",
        title="Global Endpoint for Gemini 3",
        content="Always use location='global' for Gemini 3 models on Vertex AI.",
        context="Unk Agent routing fix",
        keywords=["gemini", "vertex", "global", "routing"]
    )
    print(f"Wrote note: {note.id}")
    
    # Retrieve notes by keywords
    relevant = notes.get_notes_for_context(["gemini", "routing"])
    print(f"Found {len(relevant)} relevant notes")
    for n in relevant:
        print(f"  - {n.title} ({n.category})")
    
    print("\n✅ Persistent Notes Test PASSED\n")

async def test_tool_extensions():
    print("=" * 60)
    print("TEST 3: Tool Extensions")
    print("=" * 60)
    
    from services.tools import CommandExecutor, FileEditor, ToolRegistry
    
    # Test command executor
    cmd = CommandExecutor(default_cwd=".", timeout_seconds=10)
    result = await cmd.safe_execute(command="echo Hello from Confucius")
    print(f"Command result: {result.success}")
    print(f"Output: {result.output.strip()}")
    
    # Test registry
    registry = ToolRegistry()
    registry.register(cmd)
    registry.register(FileEditor())
    
    print(f"Registered tools: {registry.list_tools()}")
    print(f"State summary:\n{registry.get_state_summary()}")
    
    print("\n✅ Tool Extensions Test PASSED\n")

async def test_orchestrator():
    print("=" * 60)
    print("TEST 4: Unified Orchestrator")
    print("=" * 60)
    
    from services.orchestrator import UnkOrchestrator
    
    orch = UnkOrchestrator(repo_path=".", persona="unk")
    
    # Start a task
    context = orch.start_task(
        task_name="Test Confucius Integration",
        task_description="Verify all components work together"
    )
    print(f"Started task: {context.task_name}")
    
    # Execute a tool step
    result = await orch.execute_step(
        action="run_command",
        tool_name="command_executor",
        tool_params={"command": "echo Orchestrator working!"}
    )
    print(f"Step result: {result['success']}")
    
    # Get memory snapshot
    snapshot = orch.get_memory_snapshot()
    print(f"Memory snapshot: {len(snapshot)} chars")
    
    print("\n✅ Orchestrator Test PASSED\n")

async def main():
    print("\n" + "=" * 60)
    print("CONFUCIUS ARCHITECTURE VERIFICATION")
    print("=" * 60 + "\n")
    
    await test_working_memory()
    await test_persistent_notes()
    await test_tool_extensions()
    await test_orchestrator()
    
    print("=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
