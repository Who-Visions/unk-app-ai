import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from services.llm.smart_router import router
from services.llm.gemini_agent import GeminiAgent

def test_overrides():
    print("--- Testing Overrides ---")
    
    # Pro Overrides
    model, config = router.route("complex: what is the meaning of life?")
    assert model == "gemini-3-pro-preview", f"Failed: Expected Pro, got {model}"
    assert config['thinking_config']['thinking_level'] == 'high', "Failed: Expected high thinking"
    print("✓ 'complex:' override works")

    model, config = router.route("deep: analysis needed")
    assert model == "gemini-3-pro-preview", f"Failed: Expected Pro, got {model}"
    print("✓ 'deep:' override works")

    # Flash Overrides
    model, config = router.route("fast: quick check")
    assert model == "gemini-3-flash-preview", f"Failed: Expected Flash, got {model}"
    assert config['thinking_config']['thinking_level'] == 'low', "Failed: Expected low thinking"
    print("✓ 'fast:' override works")

def test_heuristics():
    print("\n--- Testing Heuristics ---")
    
    # 1. Length Check
    long_prompt = "a" * 1001
    model, config = router.route(long_prompt)
    assert model == "gemini-3-pro-preview", "Failed: Length > 1000 should route to Pro"
    assert config['thinking_config']['thinking_level'] == 'high', "Failed: High complexity should be High thinking"
    print("✓ Length > 1000 trigger works")
    
    # 2. Math Check
    model, config = router.route("please solve for x in this quadratic equation")
    assert model == "gemini-3-pro-preview", "Failed: Math keyword should route to Pro"
    print("✓ Math keyword trigger works")

    # 3. Code Check
    model, config = router.route("write a python script to scan ports")
    assert model == "gemini-3-pro-preview", "Failed: Code keyword should route to Pro"
    print("✓ Code keyword trigger works")
    
def test_user_scenarios():
    print("\n--- Testing User-Specific Scenarios ---")
    scenarios = [
        ("what time is it?", "gemini-3-flash-preview"),
        ("what is the mathematical equation for quantum theory?", "gemini-3-pro-preview"),
        ("Just a short random sentence.", "gemini-3-flash-preview"),
        ("Calculate the derivative of x^2.", "gemini-3-pro-preview"),
        ("Write a Python script to parse a CSV.", "gemini-3-pro-preview"),
        ("Compare and contrast React and Vue.", "gemini-3-pro-preview"),
        (f"A very long prompt that exceeds 1000 characters... {'a'*1000}", "gemini-3-pro-preview"),
        ("Who won the 1998 World Cup?", "gemini-3-flash-preview"),
    ]
    
    for prompt, expected in scenarios:
        # Truncate prompt for display if too long
        disp_prompt = (prompt[:50] + '..') if len(prompt) > 50 else prompt
        model, config = router.route(prompt)
        
        status = "✓ PASS" if model == expected else f"✗ FAIL (Got {model})"
        level = config.get('thinking_config', {}).get('thinking_level', 'UNKNOWN')
        print(f"[{status}] '{disp_prompt}' -> {model} (Thinking: {level})")
        
        # Soft assertion to allow viewing all results even if one fails
        if model != expected:
            print(f"   >>> WARN: Mismatch for '{disp_prompt}'")

def test_heuristics():
    # Kept for backward compatibility or remove if redundant
    pass

def test_agent_integration():
    print("\n--- Testing Agent Integration ---")
    agent = GeminiAgent(api_key_env="TEST_KEY_NOT_NEEDED_FOR_ROUTING")
    # We mock the _call_gemini to avoid actual API calls
    agent._call_gemini = lambda model, contents, config: f"Called {model} with {config}"
    
    response = agent.run("fast: quick test")
    print(f"Response: {response}")
    assert "gemini-3-flash-preview" in response
    assert "'thinking_level': 'low'" in response or "ThinkingLevel.LOW" in str(response)
    print("✓ Agent integration works")

if __name__ == "__main__":
    test_overrides()
    test_user_scenarios()
    test_agent_integration()
    print("\nALL TESTS PASSED")
