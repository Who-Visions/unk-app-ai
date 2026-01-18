
import os

env_path = ".env"
updates = {
    "NOTION_TRADE_LOG_DB_ID": "35940faaf6014d089dff1a01006d02c8",
    "NOTION_HOLDINGS_DB_ID": "4cea6b3f9e304433b6c70a2895db6da3",
    "NOTION_PORTFOLIO_DB_ID": "1a024874a52345fbb6877dfaa2d6c65a"
}

if os.path.exists(env_path):
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    # Remove existing ones if they exist to avoid duplicates
    new_lines = []
    keys_to_update = set(updates.keys())
    for line in lines:
        key = line.split('=')[0] if '=' in line else None
        if key not in keys_to_update:
            new_lines.append(line)
    
    # Add new ones
    for key, val in updates.items():
        if not new_lines[-1].endswith('\n') if new_lines else False:
            new_lines.append('\n')
        new_lines.append(f"{key}={val}\n")
    
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    print("Successfully updated .env with Notion Database IDs.")
else:
    print(".env file not found.")
