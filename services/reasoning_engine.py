#!/usr/bin/env python3
"""
Unk Agent - Vertex AI Reasoning Engine Deployment
==================================================
Deploy Unk Agent as a Reasoning Engine for agent-to-agent coordination.

Who Visions LLC - AI with Dav3
"""

import os
from typing import Any, Dict

from google.cloud import aiplatform
from vertexai.preview import reasoning_engines

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

PROJECT_ID = "unk-app-480102"
LOCATION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-reasoning-engine"
ENGINE_DISPLAY_NAME = "unk-agent-reasoning-engine"

# Initialize Vertex AI
aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)


# ═══════════════════════════════════════════════════════════════════════════
# UNK REASONING ENGINE IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════

class UnkReasoningEngine:
    """
    Unk Agent Reasoning Engine for Vertex AI.

    Provides cognitive routing, cost optimization, and intelligent
    task analysis for the Who Visions Fleet.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.5-pro-preview-06-05",
        project: str = PROJECT_ID,
        location: str = LOCATION
    ):
        """Initialize the Unk Reasoning Engine."""
        self.model_name = model_name
        self.project = project
        self.location = location

        # Import here to avoid deployment issues
        from langchain_google_vertexai import ChatVertexAI  # pylint: disable=import-outside-toplevel

        self.model = ChatVertexAI(
            model_name=model_name,
            project=project,
            location=location,
            temperature=0.3,
            max_tokens=8192
        )

        # Cognitive tiers
        self.tiers = {
            "cost_saver": "gemini-2.0-flash-lite-001",
            "default": "gemini-2.0-flash-001",
            "flash_thinking": "gemini-2.0-flash-thinking-exp",
            "unk_mode": "gemini-2.5-pro-preview-06-05",
            "ultrathink": "gemini-2.5-pro-preview-06-05",
            "code_specialist": "gemini-2.5-pro-preview-06-05"
        }

    def query(
        self,
        prompt: str,
        mode: str = "unk_mode",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main query interface for the reasoning engine.

        Args:
            prompt: User input
            mode: Cognitive tier (default: unk_mode)
            **kwargs: Additional parameters

        Returns:
            Dict with response, mode, and metadata
        """
        from langchain_core.messages import HumanMessage

        # Route to appropriate tier
        selected_model = self.tiers.get(mode, self.tiers["unk_mode"])

        # Classify complexity if auto-routing requested
        if mode == "auto":
            complexity = self._classify_complexity(prompt)
            mode = self._map_complexity_to_mode(complexity)
            selected_model = self.tiers[mode]

        # Create system prompt
        system_prompt = self._build_system_prompt(mode)

        # Build messages
        messages = [
            HumanMessage(content=f"{system_prompt}\n\nUser Query: {prompt}")
        ]

        # Invoke model
        try:
            response = self.model.invoke(messages)

            return {
                "success": True,
                "response": response.content,
                "mode": mode,
                "model": selected_model,
                "metadata": {
                    "project": self.project,
                    "location": self.location,
                    "tier_system": "6-tier cognitive routing"
                }
            }
        except Exception as e:  # pylint: disable=W0718
            return {
                "success": False,
                "error": str(e),
                "mode": mode,
                "model": selected_model
            }

    def _classify_complexity(self, prompt: str) -> str:
        """Classify prompt complexity."""
        # Simple heuristic-based classification
        prompt_lower = prompt.lower()

        # Trivial patterns
        if any(word in prompt_lower for word in ["hello", "hi", "hey", "thanks"]):
            return "trivial"

        # Simple patterns
        if any(word in prompt_lower for word in ["what is", "define", "list"]):
            return "simple"

        # Complex patterns
        if any(word in prompt_lower for word in ["design", "architect", "implement", "debug"]):
            return "complex"

        # Extreme patterns
        if any(word in prompt_lower for word in ["research", "synthesize", "comprehensive", "analyze deeply"]):
            return "extreme"

        # Default to moderate
        return "moderate"

    def _map_complexity_to_mode(self, complexity: str) -> str:
        """Map complexity to cognitive tier."""
        mapping = {
            "trivial": "cost_saver",
            "simple": "default",
            "moderate": "flash_thinking",
            "complex": "unk_mode",
            "extreme": "ultrathink"
        }
        return mapping.get(complexity, "default")

    def _build_system_prompt(self, mode: str) -> str:
        """Build system prompt based on mode."""
        base = """You are Unk Agent, an enterprise-grade cognitive orchestrator specializing in intelligent task routing and cost optimization.

Key Capabilities:
- Multi-tier cognitive routing (6 tiers)
- Cost-aware inference optimization
- Vector memory and RAG
- Structured output generation
- Tool execution and function calling

Brand: Who Visions LLC / AI with Dav3
Role: Cognitive Orchestrator
"""

        mode_specifics = {
            "cost_saver": "MODE: Cost Saver - Provide concise, efficient responses.",
            "default": "MODE: Default - Provide clear, helpful responses.",
            "flash_thinking": "MODE: Flash Thinking - Use reasoning to solve moderately complex problems.",
            "unk_mode": "MODE: Unk Mode - Engage deep analysis and comprehensive reasoning.",
            "ultrathink": "MODE: Ultrathink - Use maximum thinking budget for complex research and system design.",
            "code_specialist": "MODE: Code Specialist - Focus on code review, debugging, and implementation."
        }

        return base + "\n" + mode_specifics.get(mode, mode_specifics["default"])

    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities (A2A standard)."""
        return {
            "name": "Unk Agent",
            "version": "1.0.0",
            "description": "Enterprise-grade multi-model cognitive agent with dynamic tier routing.",
            "capabilities": [
                "text-generation",
                "code-generation",
                "code-analysis",
                "reasoning",
                "deep-research",
                "vector-memory",
                "rag-search",
                "cost-optimization",
                "cognitive-routing",
                "structured-output",
                "tool-execution"
            ],
            "tiers": list(self.tiers.keys()),
            "role": "Cognitive Orchestrator"
        }


# ═══════════════════════════════════════════════════════════════════════════
# DEPLOYMENT FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def deploy_unk_reasoning_engine():
    """Deploy Unk Agent as a Vertex AI Reasoning Engine."""

    print("=" * 70)
    print("UNK AGENT - REASONING ENGINE DEPLOYMENT")
    print("=" * 70)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Staging Bucket: {STAGING_BUCKET}")
    print("=" * 70)

    # Create the reasoning engine
    print("\n🚀 Creating Reasoning Engine...")

    try:
        # Define requirements
        requirements = [
            "google-cloud-aiplatform>=1.79.0",
            "langchain-google-vertexai>=2.0.11",
            "langchain>=0.3.13",
            "langchain-core>=0.3.29"
        ]

        # Create and deploy
        remote_agent = reasoning_engines.ReasoningEngine.create(
            UnkReasoningEngine(),
            requirements=requirements,
            display_name=ENGINE_DISPLAY_NAME,
            description="Unk Agent - Cognitive Orchestrator with 6-tier routing",
            extra_packages=[]
        )

        print("✅ Reasoning Engine deployed successfully!")
        print(f"\nResource Name: {remote_agent.resource_name}")
        print(f"Display Name: {remote_agent.display_name}")

        # Test the engine
        print("\n🧪 Testing Reasoning Engine...")

        test_result = remote_agent.query(
            prompt="Hello! What are your capabilities?",
            mode="default"
        )

        print("\nTest Result:")
        print(f"Success: {test_result.get('success')}")
        print(f"Mode: {test_result.get('mode')}")
        print(f"Response: {test_result.get('response')[:200]}...")

        # Get capabilities
        print("\n📋 Agent Capabilities:")
        capabilities = remote_agent.get_capabilities()
        print(f"Name: {capabilities['name']}")
        print(f"Role: {capabilities['role']}")
        print(f"Tiers: {', '.join(capabilities['tiers'])}")

        print("\n" + "=" * 70)
        print("DEPLOYMENT COMPLETE!")
        print("=" * 70)
        print(f"\nTo use this engine in your code:")
        print(f"```python")
        print(f"from vertexai.preview import reasoning_engines")
        print(f"")
        print(f"agent = reasoning_engines.ReasoningEngine('{remote_agent.resource_name}')")
        print(f"response = agent.query(prompt='Your question', mode='unk_mode')")
        print(f"```")

        return remote_agent

    except Exception as e:  # pylint: disable=W0718
        print(f"\n❌ Deployment failed: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    # Check for required environment
    if "GOOGLE_CLOUD_PROJECT" not in os.environ:
        os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID

    print("\n🎯 Starting Unk Agent Reasoning Engine Deployment...")
    print("This will deploy Unk Agent to Vertex AI Reasoning Engines.\n")

    try:
        deployed_engine = deploy_unk_reasoning_engine()
        print("\n✅ Success! Unk Agent is now available as a Reasoning Engine.")
        sys.exit(0)
    except Exception as e:  # pylint: disable=W0718
        print(f"\n❌ Error: {e}")
        sys.exit(1)
