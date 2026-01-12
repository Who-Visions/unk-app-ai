
import os
import sys
import logging
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
load_dotenv()

APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

if not APP_TOKEN or not BOT_TOKEN:
    print("❌ Missing tokens in .env")
    sys.exit(1)

print(f"App Token: {APP_TOKEN[:10]}...")
print(f"Bot Token: {BOT_TOKEN[:10]}...")

# Init Clients
client = WebClient(token=BOT_TOKEN)
socket_client = SocketModeClient(app_token=APP_TOKEN, web_client=client)

print("\n📡 Connecting to Slack Socket Mode...")
try:
    socket_client.connect()
    print("✅ Socket Mode CONNECTED!")
    
    # Check Auth
    auth = client.auth_test()
    print(f"✅ Auth Success: Connected as {auth['user']} ({auth['user_id']})")
    
    # Clean disconnect
    socket_client.close()
    print("✅ Disconnected cleanly.")
    
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    sys.exit(1)
