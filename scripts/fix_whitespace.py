
import os

MODULES = [
    "gemini_agent/agent.py",
    "gemini_agent/models_spec.py",
    "routers/chat.py",
    "routers/orchestrator.py",
    "routers/core.py",
    "routers/auth.py",
    "routers/models.py",
    "routers/tools.py",
    "routers/dependencies.py",
    "routers/config.py",
    "services/deploy.py",
    "tools/vector_store_bigquery.py"
]

def strip_whitespace(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split lines, strip right whitespace from each line
        lines = [line.rstrip() for line in content.splitlines()]
        
        # Rejoin with newlines
        new_content = '\n'.join(lines)
        
        # Ensure single trailing newline
        if new_content and not new_content.endswith('\n'):
            new_content += '\n'
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed whitespace in {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    for mod in MODULES:
        if os.path.exists(mod):
            strip_whitespace(mod)
        else:
            print(f"File not found: {mod}")
