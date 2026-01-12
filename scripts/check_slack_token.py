
import os
import sys
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("SLACK_BOT_TOKEN") or os.environ.get("SLACK_USER_TOKEN")

client = WebClient(token=token)

print(f"Testing token: {token[:15]}...")

try:
    auth_test = client.auth_test()
    print("\n✅ Token is VALID!")
    print(f"Identity: {auth_test['user']} (ID: {auth_test['user_id']})")
    print(f"Team: {auth_test['team']} (ID: {auth_test['team_id']})")
    print(f"Bot User: {auth_test.get('bot_id', 'No (User Token)')}")
    
    # Try to open a socket (will fail if not an app-level token)
    from slack_sdk.socket_mode import SocketModeClient
    print("\nAttempting Socket Mode check...")
    try:
        SocketModeClient(app_token=token, web_client=client).connect()
        print("✅ Socket Mode connected (Unexpected!)")
    except Exception as e:
        print(f"❌ Socket Mode Failed (Expected for User/Enterprise tokens): {e}")

except SlackApiError as e:
    print(f"\n❌ Token Rejected: {e.response['error']}")
