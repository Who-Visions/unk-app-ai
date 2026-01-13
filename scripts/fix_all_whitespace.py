import os
TARGET_DIRS = ["services", "skills", "routers", "gemini_agent", "tools"]

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # rstrip() removes newline too, so verify logic
        # line.rstrip() removes all trailing whitespace including \n
        # So we add \n back. 
        # But if line was empty string? rstrip is empty. + \n is \n. Correct.
        new_lines = [line.rstrip() + "\n" for line in lines]
        
        # Determine if file ends with newline properly
        # The above logic enforces \n on every line including last.
        
        # Check diff
        if lines != new_lines:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"Fixed: {filepath}")
    except Exception as e:
        print(f"Skipping {filepath}: {e}")

if __name__ == "__main__":
    for d in TARGET_DIRS:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for file in files:
                if file.endswith(".py"):
                    fix_file(os.path.join(root, file))
