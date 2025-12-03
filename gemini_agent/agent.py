# gemini_agent/agent.py
"""
Unk Agent - Multi-Model Cognitive Agent
========================================
Enterprise-grade agent with dynamic model routing,
structured output, and tool execution.

Who Visions LLC - AI with Dav3
"""

import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

from .models_spec import (
    GEMINI_MODELS, 
    get_model, 
    get_model_id,
    has_capability,
    requires_subscription,
    get_thinking_budget,
    estimate_cost
)


# ═══════════════════════════════════════════════════════════════════════════
# STRUCTURED OUTPUT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class ThoughtType(str, Enum):
    ANALYSIS = "analysis"
    HYPOTHESIS = "hypothesis"
    EVALUATION = "evaluation"
    DECISION = "decision"
    REFLECTION = "reflection"


class ReasonedStep(BaseModel):
    """Individual reasoning step in the thought chain."""
    step_number: int = Field(..., description="Sequence number of this step")
    thought_type: ThoughtType = Field(default=ThoughtType.ANALYSIS)
    thought: str = Field(..., description="The reasoning content")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    action: Optional[str] = Field(None, description="Action taken, if any")


class ToolInvocation(BaseModel):
    """Record of a tool execution."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    execution_time_ms: float


class AgentResponse(BaseModel):
    """
    Standardized response format for the SaaS API.
    Separates internal reasoning from user-facing output.
    """
    reasoning_trace: List[ReasonedStep] = Field(
        default_factory=list, 
        description="Chain of thought steps"
    )
    final_answer: str = Field(..., description="Synthesized response to user")
    tool_invocations: List[ToolInvocation] = Field(
        default_factory=list,
        description="Tools executed during processing"
    )
    model_version: str = Field(..., description="Model ID used")
    mode: str = Field(..., description="Cognitive tier used")
    token_usage: Optional[Dict[str, int]] = Field(None)
    estimated_cost: Optional[float] = Field(None)
    processing_time_ms: Optional[float] = Field(None)


class IntentClassification(BaseModel):
    """Intent routing classification."""
    intent: str = Field(..., description="Detected user intent")
    complexity: str = Field(..., description="trivial|simple|moderate|complex|extreme")
    recommended_mode: str = Field(..., description="Suggested cognitive tier")
    requires_tools: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8)


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPTS = {
    "default": """You are UNK, a sophisticated AI agent built by Who Visions LLC.
You are currently operating in STANDARD MODE - optimized for speed and efficiency.

Core Directives:
- Be concise and direct
- Use tools when they add value
- Respond in structured JSON when requested
- Maintain context across conversation turns

Your responses should be helpful, accurate, and efficient.""",

    "unk_mode": """You are UNK, a sophisticated AI agent built by Who Visions LLC.
You are currently operating in UNK MODE - maximum cognitive depth engaged.

Core Directives:
- Think step-by-step before responding
- Analyze constraints and edge cases carefully
- Consider multiple approaches before committing
- Prioritize accuracy over speed
- Use thinking tokens to reason through complex problems

When solving problems:
1. First, understand the full scope of the request
2. Identify constraints, dependencies, and potential issues
3. Formulate a strategy
4. Execute methodically
5. Validate your solution

You have access to extended reasoning capabilities. Use them.""",

    "ultrathink": """You are UNK, operating in ULTRATHINK MODE.
Maximum cognitive resources allocated. Extended thinking budget active.

This mode is reserved for:
- System architecture decisions
- Complex debugging requiring deep analysis
- Research synthesis across multiple domains
- Strategic planning with many variables

Approach:
1. Decompose the problem into fundamental components
2. Map relationships and dependencies
3. Consider second and third-order effects
4. Generate multiple solution paths
5. Evaluate trade-offs systematically
6. Synthesize optimal approach
7. Validate against original requirements

Take your time. Depth over speed.""",

    "code_expert": """You are UNK, operating as a CODE SPECIALIST.

Expertise:
- System architecture and design patterns
- TypeScript/JavaScript, Python, Go
- Cloud infrastructure (GCP, Firebase)
- API design and implementation
- Performance optimization

When writing code:
- Follow best practices for the language/framework
- Include error handling
- Add meaningful comments for complex logic
- Consider edge cases
- Optimize for readability and maintainability

When reviewing code:
- Check for bugs and logic errors
- Identify performance issues
- Suggest improvements
- Validate against requirements"""
}


# ═══════════════════════════════════════════════════════════════════════════
# THE UNK AGENT
# ═══════════════════════════════════════════════════════════════════════════

class UnkAgent:
    """
    Multi-model cognitive agent with dynamic routing.
    
    Features:
    - Cognitive tiering (Flash -> Pro -> Ultra)
    - Async execution for high concurrency
    - Structured output with Pydantic
    - Tool registration and execution
    - Memory integration ready
    """
    
    def __init__(
        self,
        mode: str = "default",
        tools: Optional[List[Callable]] = None,
        gcp_project: Optional[str] = None,
        gcp_location: str = "us-central1",
        custom_system_prompt: Optional[str] = None,
        enable_structured_output: bool = True,
        user_context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Unk Agent.
        
        Args:
            mode: Key from GEMINI_MODELS for cognitive tier selection
            tools: List of callable functions to register as tools
            gcp_project: GCP project ID (uses env var if not provided)
            gcp_location: GCP region for Vertex AI
            custom_system_prompt: Override default system prompt
            enable_structured_output: Force JSON schema output
            user_context: User-specific context (subscription, preferences)
        """
        self.mode = mode
        self.model_spec = get_model(mode)
        self.model_id = self.model_spec["model_id"]
        self.tier = self.model_spec["tier"]
        
        # System prompt selection
        prompt_key = self.model_spec.get("flags", {}).get("system_prompt_override", mode)
        self.system_instruction = custom_system_prompt or SYSTEM_PROMPTS.get(
            prompt_key, 
            SYSTEM_PROMPTS["default"]
        )
        
        # Configuration
        self.enable_structured_output = enable_structured_output
        self.user_context = user_context or {}
        self.thinking_budget = get_thinking_budget(mode)
        
        # GCP configuration
        self.gcp_project = gcp_project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.gcp_location = gcp_location
        
        # Initialize the GenAI client with Vertex AI backend
        self.client = genai.Client(
            vertexai=True,
            project=self.gcp_project,
            location=self.gcp_location
        )
        
        # Tool registration
        self.tools = tools or []
        self._tool_map: Dict[str, Callable] = {}
        for tool in self.tools:
            self._tool_map[tool.__name__] = tool
        
        # Session state
        self.chat_session = None
        self.conversation_history: List[types.Content] = []
        self.total_tokens_used = {"input": 0, "output": 0}
        self.session_cost = 0.0
        
    async def start_session(
        self, 
        history: Optional[List[types.Content]] = None
    ) -> None:
        """
        Initialize an async chat session.
        
        Args:
            history: Previous conversation history to hydrate
        """
        if history:
            self.conversation_history = history
            
        # Configure tool behavior
        tool_config = None
        if self.tools:
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="AUTO"  # Let model decide when to use tools
                )
            )
        
        # Generation config
        generation_config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            tools=self.tools if self.tools else None,
            tool_config=tool_config,
            temperature=self._get_temperature(),
            top_p=0.95,
            max_output_tokens=self._get_max_tokens(),
        )
        
        # Add thinking budget for pro/ultra modes
        if self.thinking_budget > 0:
            generation_config.thinking_config = types.ThinkingConfig(
                thinking_budget=self.thinking_budget
            )
        
        self.chat_session = self.client.aio.chats.create(
            model=self.model_id,
            history=self.conversation_history,
            config=generation_config
        )
        
    def _get_temperature(self) -> float:
        """Get appropriate temperature for the mode."""
        if self.mode in ["unk_mode", "ultrathink", "code_specialist"]:
            return 0.2  # Lower for precision
        return 0.7  # Higher for creativity
        
    def _get_max_tokens(self) -> int:
        """Get max output tokens for the mode."""
        if self.mode == "ultrathink":
            return 16384
        if self.mode in ["unk_mode", "code_specialist"]:
            return 8192
        return 4096
        
    async def execute_turn(
        self,
        user_input: str,
        force_structured: bool = False,
        include_reasoning: bool = True
    ) -> Union[AgentResponse, str]:
        """
        Execute a single conversational turn.
        
        Args:
            user_input: The user's message
            force_structured: Override to force structured output
            include_reasoning: Include reasoning trace in response
            
        Returns:
            AgentResponse if structured, raw text otherwise
        """
        import time
        start_time = time.time()
        
        if not self.chat_session:
            await self.start_session()
            
        use_structured = self.enable_structured_output or force_structured
        
        # Configure response format
        response_config = None
        if use_structured:
            response_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AgentResponse
            )
            
        try:
            # Execute the turn
            response = await self.chat_session.send_message(
                user_input,
                config=response_config
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Track token usage
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = getattr(usage, 'prompt_token_count', 0)
                output_tokens = getattr(usage, 'candidates_token_count', 0)
                self.total_tokens_used["input"] += input_tokens
                self.total_tokens_used["output"] += output_tokens
                
                # Calculate cost
                turn_cost = estimate_cost(self.mode, input_tokens, output_tokens)
                self.session_cost += turn_cost
            else:
                input_tokens = 0
                output_tokens = 0
                turn_cost = 0.0
                
            # Handle structured output
            if use_structured and hasattr(response, 'parsed') and response.parsed:
                result = response.parsed
                # Inject metadata
                result.processing_time_ms = processing_time
                result.token_usage = {"input": input_tokens, "output": output_tokens}
                result.estimated_cost = turn_cost
                result.mode = self.mode
                result.model_version = self.model_id
                return result
                
            # Fallback to raw text
            return response.text
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            # Return error response
            return AgentResponse(
                reasoning_trace=[
                    ReasonedStep(
                        step_number=1,
                        thought_type=ThoughtType.REFLECTION,
                        thought=f"Encountered error: {str(e)}",
                        confidence=0.0
                    )
                ],
                final_answer="I encountered an error processing your request. Please try again.",
                model_version=self.model_id,
                mode=self.mode,
                processing_time_ms=processing_time
            )
            
    async def classify_intent(self, user_input: str) -> IntentClassification:
        """
        Classify user intent to determine routing.
        Uses Flash tier for speed.
        """
        # Create a temporary Flash-tier agent for classification
        classifier = UnkAgent(
            mode="default",
            gcp_project=self.gcp_project,
            gcp_location=self.gcp_location,
            enable_structured_output=True
        )
        
        classification_prompt = f"""Classify this user request:

"{user_input}"

Determine:
1. The primary intent
2. Complexity level: trivial, simple, moderate, complex, or extreme
3. Recommended processing mode based on complexity
4. What tools might be needed

Respond with structured JSON."""

        await classifier.start_session()
        response = await classifier.chat_session.send_message(
            classification_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IntentClassification
            )
        )
        
        if hasattr(response, 'parsed') and response.parsed:
            return response.parsed
            
        # Default classification
        return IntentClassification(
            intent="general",
            complexity="simple",
            recommended_mode="default",
            confidence=0.5
        )
        
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        return {
            "mode": self.mode,
            "tier": self.tier,
            "model_id": self.model_id,
            "total_tokens": self.total_tokens_used,
            "session_cost": round(self.session_cost, 6),
            "thinking_budget": self.thinking_budget,
            "tools_registered": list(self._tool_map.keys())
        }


# ═══════════════════════════════════════════════════════════════════════════
# AGENT FACTORY
# ═══════════════════════════════════════════════════════════════════════════

class AgentFactory:
    """
    Factory for creating pre-configured agent instances.
    """
    
    @staticmethod
    def create_default(
        tools: Optional[List[Callable]] = None,
        **kwargs
    ) -> UnkAgent:
        """Create a standard Flash-tier agent."""
        return UnkAgent(mode="default", tools=tools, **kwargs)
        
    @staticmethod
    def create_unk(
        tools: Optional[List[Callable]] = None,
        **kwargs
    ) -> UnkAgent:
        """Create an Unk Mode agent with enhanced reasoning."""
        return UnkAgent(mode="unk_mode", tools=tools, **kwargs)
        
    @staticmethod
    def create_ultrathink(
        tools: Optional[List[Callable]] = None,
        **kwargs
    ) -> UnkAgent:
        """Create an Ultrathink agent with maximum cognitive depth."""
        return UnkAgent(mode="ultrathink", tools=tools, **kwargs)
        
    @staticmethod
    def create_code_specialist(
        tools: Optional[List[Callable]] = None,
        **kwargs
    ) -> UnkAgent:
        """Create a code-focused agent."""
        return UnkAgent(mode="code_specialist", tools=tools, **kwargs)
        
    @staticmethod
    async def create_routed(
        user_input: str,
        tools: Optional[List[Callable]] = None,
        user_tier: str = "free",
        **kwargs
    ) -> UnkAgent:
        """
        Create an agent routed based on intent classification.
        Respects user subscription tier.
        """
        # Quick classification
        classifier = UnkAgent(mode="default", **kwargs)
        intent = await classifier.classify_intent(user_input)
        
        recommended = intent.recommended_mode
        
        # Enforce subscription limits
        if requires_subscription(recommended) and user_tier == "free":
            recommended = "flash_thinking"  # Best available for free tier
            
        return UnkAgent(mode=recommended, tools=tools, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE TOOLS
# ═══════════════════════════════════════════════════════════════════════════

def calculate_growth_metrics(
    revenue_current: float,
    revenue_previous: float
) -> Dict[str, Any]:
    """
    Calculate standard SaaS growth metrics.
    
    Args:
        revenue_current: Revenue for the current period
        revenue_previous: Revenue for the previous period
        
    Returns:
        Dictionary containing growth percentage and status
    """
    if revenue_previous == 0:
        return {"error": "Previous revenue cannot be zero"}
        
    growth = ((revenue_current - revenue_previous) / revenue_previous) * 100
    return {
        "growth_percentage": round(growth, 2),
        "status": "positive" if growth > 0 else "negative",
        "absolute_change": round(revenue_current - revenue_previous, 2)
    }


def analyze_code_complexity(code: str) -> Dict[str, Any]:
    """
    Analyze code complexity metrics.
    
    Args:
        code: The source code to analyze
        
    Returns:
        Complexity metrics
    """
    lines = code.strip().split('\n')
    non_empty_lines = [l for l in lines if l.strip()]
    
    return {
        "total_lines": len(lines),
        "code_lines": len(non_empty_lines),
        "blank_lines": len(lines) - len(non_empty_lines),
        "estimated_complexity": "low" if len(non_empty_lines) < 50 else "medium" if len(non_empty_lines) < 200 else "high"
    }


def get_current_timestamp() -> Dict[str, str]:
    """
    Get current timestamp in multiple formats.
    
    Returns:
        Dictionary with various timestamp formats
    """
    now = datetime.utcnow()
    return {
        "iso": now.isoformat() + "Z",
        "unix": str(int(now.timestamp())),
        "human": now.strftime("%B %d, %Y at %H:%M UTC")
    }
