
import os

env_path = ".env"
updates = {
    "NOTION_TRADE_LOG_DB_ID": "35940faa-f601-4d08-9dff-1a01006d02c8",
    "NOTION_HOLDINGS_DB_ID": "4cea6b3f-9e30-4433-b6c7-0a2895db6da3",
    "NOTION_PORTFOLIO_DB_ID": "1a024874-a523-45fb-b687-7dfaa2d6c65a"
}

if os.path.exists(env_path):
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    new_lines = []
    keys_to_update = set(updates.keys())
    for line in lines:
        key = line.split('=')[0] if '=' in line else None
        if key not in keys_to_update:
            new_lines.append(line)
    
    for key, val in updates.items():
        new_lines.append(f"{key}={val}\n")
    
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    print("Successfully updated .env with Notion Database IDs (with dashes).")
else:
    print(".env file not found.")
