import os
from typing import Any, Dict, Optional
from google.auth import default
import vertexai
from vertexai.preview import reasoning_engines

class ReasoningAgent:
    """
    Agent that interfaces with a deployed Vertex AI Reasoning Engine.
    Resource: projects/574321322006/locations/us-central1/reasoningEngines/5608320741238898688
    """
    def __init__(self):
        self.project = os.getenv("GOOGLE_CLOUD_PROJECT", "unk-app-480102")
        self.location = "us-central1"
        self.resource_id = "5608320741238898688"
        self.resource_path = f"projects/574321322006/locations/{self.location}/reasoningEngines/{self.resource_id}"
        
        # Initialize Vertex AI
        vertexai.init(project=self.project, location=self.location)
        
        # Initialize Remote Engine
        # Note: We use reasoning_engines.ReasoningEngine NOT to create, but to access?
        # The SDK pattern for *calling* an existing engine usually involves valid resource verification
        try:
            self.remote_engine = reasoning_engines.ReasoningEngine(self.resource_path)
            self.connected = True
        except Exception as e:
            print(f"[ReasoningAgent] Connection Error: {e}")
            self.connected = False

    def query(self, input_text: str) -> str:
        """
        Sends a query to the reasoning engine.
        """
        if not self.connected:
            return "Error: Reasoning Engine not connected."
            
        try:
            # The remote UnkAgent expects: query(prompt=str)
            response = self.remote_engine.query(prompt=input_text)
            
            # Extract text from response (dict with 'response' key)
            if isinstance(response, dict):
                return response.get('response', str(response))
            if hasattr(response, 'output'):
                return str(response.output)
            return str(response)
            
        except Exception as e:
            return f"Reasoning Error: {e}"

if __name__ == "__main__":
    # Self-Test
    agent = ReasoningAgent()
    if agent.connected:
        print("Connected! Sending test query...")
        res = agent.query("Analyze this market state: BTC is crashing, I have 100% cash.")
        print(f"Response: {res}")
    else:
        print("Failed to connect.")
