
import os

env_path = ".env"
new_secret = os.getenv("NOTION_SECRET_UPDATE_VALUE", "PLACEHOLDER_SECRET")

if os.path.exists(env_path):
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("NOTION_WHO_VISIONS_SECRET="):
                f.write(f"NOTION_WHO_VISIONS_SECRET={new_secret}\n")
            elif line.startswith("NOTION_OBSERVATORY_SECRET="):
                f.write(f"NOTION_OBSERVATORY_SECRET={new_secret}\n")
            else:
                f.write(line)
    print("Successfully updated .env with new Notion secret.")
else:
    print(".env file not found.")
