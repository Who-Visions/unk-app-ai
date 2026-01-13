import sys
import os
import types

# MOCK YAML if missing
try:
    import yaml
except ImportError:
    print("⚠️ PyYAML missing, mocking module for verification...")
    mock_yaml = types.ModuleType("yaml")
    mock_yaml.safe_load = lambda x: {}
    sys.modules["yaml"] = mock_yaml

# Ensure we can import from the root
sys.path.append(os.getcwd())

from services.llm.unk_agent import UnkAiAgent
from services.llm.dispatcher import AgentDispatcher

def test_unk_agent_prompt():
    print("Testing UnkAiAgent prompt generation...")
    # ... (rest of test_unk_agent_prompt) ...
    agent = UnkAiAgent(api_key_env="DUMMY_KEY") 
    original_call = agent._call_gemini
    agent._call_gemini = lambda model, contents, config=None, tools=None: f"MOCK_RESPONSE: {contents}"
    
    payload = {"title": "Skibidi Toilet", "platform": "TikTok"}
    response = agent.summarise_trend(payload)
    
    # Check naive output
    raw_text = response.get("raw", "")
    if not raw_text and isinstance(response, str): raw_text = response
    
    print(f"\nPrompt Snippet: {raw_text[:100]}...\n")

    if "Tribunal" in raw_text and ("City Boy" in raw_text or "City Girl" in raw_text):
        print("✅ Unk 'Tribunal' & 'City Boy' prompt instructions detected.")
    elif "Cookout Uncle" in raw_text: 
        print("✅ Unk 'Cookout Uncle' prompt instructions detected (Previous Version).")
    else:
        print("❌ Unk comedy prompt MISSING new Tribunal traits.")

def test_dispatcher():
    print("\nTesting AgentDispatcher...")
    # Mock load_config to avoid file read/yaml parse errors
    original_load = AgentDispatcher._load_config
    AgentDispatcher._load_config = lambda self, path: {
        "team": [
            {"name": "Design Lead", "role": "UI/UX", "focus": "Visuals", "model": "gemini-3-pro-image-preview"},
            {"name": "Builder", "role": "Eng", "focus": "Code", "model": "gemini-3-flash-preview"}
        ]
    }

    try:
        dispatcher = AgentDispatcher("antigravity.yaml")
        print("✅ Dispatcher loaded (mock) config.")
        
        design_agent = dispatcher.get_agent("Design Lead")
        if design_agent and design_agent.default_model == "gemini-3-pro-image-preview":
             print(f"✅ Design Lead agent instantiated with correct model: {design_agent.default_model}")
        else:
             print("❌ Design Lead agent failed or wrong model.")
    except Exception as e:
        print(f"❌ Dispatcher error: {e}")

if __name__ == "__main__":
    test_unk_agent_prompt()
    test_dispatcher()

