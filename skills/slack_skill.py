"""
Slack Integration Skill
=======================
Handles messaging and event listening for Slack.
Uses Socket Mode for "intelligent" real-time interaction.
"""

import os
import logging
from typing import Optional, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

logger = logging.getLogger("skills.slack")

class SlackSkill:
    def __init__(self):
        self.bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.app_token = os.environ.get("SLACK_APP_TOKEN")
        self.client = None
        self.socket_client = None

        if self.bot_token:
            self.client = WebClient(token=self.bot_token)
        else:
            logger.warning("⚠️ SlackBot Token not found. Messaging disabled.")

    def post_message(self, channel: str, text: str, blocks: Optional[List] = None) -> str:
        """Posts a message to a Slack channel."""
        if not self.client:
            return "Error: Slack client not initialized."

        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks
            )
            return f"✅ Message sent to {channel} (ts: {response['ts']})"
        except SlackApiError as e:
            return f"❌ Failed to send Slack message: {e.response['error']}"

    def get_history(self, channel: str, limit: int = 10) -> str:
        """Retrieves recent messages from a channel."""
        if not self.client:
            return "Error: Slack client not initialized."

        try:
            result = self.client.conversations_history(channel=channel, limit=limit)
            messages = result["messages"]
            output = []
            for msg in messages:
                user = msg.get("user", "unknown")
                text = msg.get("text", "")
                output.append(f"[{user}]: {text}")
            return "\n".join(output)
        except SlackApiError as e:
            return f"❌ Failed to get history: {e.response['error']}"

    def start_socket_mode(self):
        """Starts the Socket Mode listener (Blocking)."""
        if not self.app_token or not self.bot_token:
            print("❌ Cannot start Socket Mode. Missing SLACK_APP_TOKEN or SLACK_BOT_TOKEN.")
            return

        self.socket_client = SocketModeClient(
            app_token=self.app_token,
            web_client=self.client
        )

        def process(client: SocketModeClient, req: SocketModeRequest):
            if req.type == "events_api":
                event = req.payload["event"]
                # Acknowledge receipt
                response = SocketModeResponse(envelope_id=req.envelope_id)
                client.send_socket_mode_response(response)

                # Handle Mentions
                if event["type"] == "app_mention":
                    channel = event["channel"]
                    user = event["user"]
                    text = event["text"]
                    self.post_message(channel, f"Hello <@{user}>! I heard: {text}")

        self.socket_client.socket_mode_request_listeners.append(process)
        self.socket_client.connect()
        print("⚡ Slack Socket Mode connected!")

        # Keep alive logic would go here in a real service wrapper
