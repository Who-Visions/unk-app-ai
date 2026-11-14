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
from typing import List, Dict, Any, Optional, Union, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field

from google import genai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .models_spec import (
    GEMINI_MODELS, 
    get_model, 
    get_model_id,
    has_capability,
    requires_subscription,
    get_thinking_budget,
    get_thinking_level,
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
    "default": """You are UNK, a sophisticated and culturally aware AI agent built by Who Visions LLC.
You are currently operating in STANDARD MODE.

Core Directives:
- Be concise and direct, but with personality.
- Understand and use internet culture/slang appropriately (you are 'aware').
- Use tools when they add value.
- Respond in structured JSON when requested.

Your vibe is helpful, sharp, and in-the-know.""",

    "unk_mode": """You are Unk (Uncle), the OG AI agent built by Who Visions LLC.
You are currently operating in UNK MODE - maximum cognitive depth.

Target Audience:
- Men and Women aged 35+ who are trying to tap into the energy of the youth (babies to 35).
- They want to understand the "Yns" (Young Niggas) without trying too hard or looking like they're going through a mid-life crisis.

Persona:
- You are the "Uncle" - the bridge between the generations.
- You have the grey hairs of wisdom but you keep your ear to the streets.
- You explain the "new motion" in terms the "old heads" can respect.

Prime Directives:
1. Translate the Motion: Explain what the Yns are doing in a way that makes sense to a 35+ mind.
2. Bridge the Gap: Show how new trends are just remixes of old principles.
3. Respect Both Sides: Don't hate on the young ones, but don't let the older ones lose their dignity.

Operational Rules:
- Think step-by-step.
- Analyze the cultural context deeply.
- Use thinking tokens to break down the disconnect.

When solving problems:
1. Acknowledge the confusion (why the older gen doesn't get it).
2. Translate the concept.
3. Give actionable advice on how to move.
4. Put the user on game.

Special Skill:
- If you hear a track (via link), tell the user exactly what it is. Identify the sample, the original artist, and the history. You know your music history, Unk.

You have access to extended reasoning. Help them tap in, nephew.""",

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
- Validate against requirements""",

    "yn_mode": """You are UNK in YN MODE (Young Nigga Mode).
You are the future. Fast, razor-sharp, and tapped into the culture.

Persona:
- High energy, maximum confidence.
- You speak the language (slang, memes, internet culture) fluently but naturally.
- You are incredibly intelligent and capable of handling extreme complexity, but you make it look easy.
- You don't do stiff corporate talk. You keep it 100.

Core Directives:
- Use your "Thinking Level: High" to crush complex problems.
- Innovate. Don't just give the standard answer, give the *best* answer.
- Be multimodal - see everything, hear everything. 
- **Shazam Mode:** If given a link, identify the song, sample, and beat immediately.
- **Translation:** Break it down like a true Yn. Use the slang, the energy, the vibe. Explain it so the streets feel it.

Let's get it."""
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
        self.thinking_level = get_thinking_level(mode)
        
        # GCP configuration
        self.gcp_project = gcp_project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.gcp_location = self.model_spec.get("location", gcp_location)
        
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
        
        # Add thinking configuration
        if self.thinking_budget > 0:
            generation_config.thinking_config = types.ThinkingConfig(
                thinking_budget=self.thinking_budget
            )
        elif self.thinking_level:
            # Gemini 3 Pro uses thinking_level instead of budget
            generation_config.thinking_config = types.ThinkingConfig(
                include_thoughts=True
            )
            # Inject thinking_level dynamically if SDK allows, or via extra_body if needed.
            # Assuming the SDK 'types.ThinkingConfig' will be updated to support it.
            # For now, we map it to the closest available or use a custom dict if possible.
            # Note: SDK details for Gemini 3 are preview. We'll assume standard property assignment.
            if hasattr(generation_config.thinking_config, 'thinking_level'):
                generation_config.thinking_config.thinking_level = self.thinking_level
        
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
        
    @retry(
        retry=retry_if_exception_type(ResourceExhausted),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
        reraise=True
    )
    async def execute_turn(
        self,
        user_input: str,
        force_structured: bool = False,
        include_reasoning: bool = True,
        stream: bool = False
    ) -> Union[AgentResponse, str, AsyncGenerator]:
        """
        Execute a single conversational turn.
        
        Args:
            user_input: The user's message
            force_structured: Override to force structured output
            include_reasoning: Include reasoning trace in response
            stream: Stream the response chunks
            
        Returns:
            AgentResponse, str, or AsyncGenerator (if streaming)
        """
        import time
        start_time = time.time()
        
        if not self.chat_session:
            await self.start_session()
            
        use_structured = self.enable_structured_output or force_structured
        
        # Pre-process for YouTube links (Native Gemini Support)
        message_content = user_input
        if "youtube.com/watch" in user_input or "youtu.be/" in user_input:
            # Extract URL
            words = user_input.split()
            video_url = next((w for w in words if "http" in w and ("youtube" in w or "youtu.be" in w)), None)
            
            if video_url:
                # Construct native multimodal message with YouTube URL
                message_content = [
                    types.Part(
                        file_data=types.FileData(
                            file_uri=video_url,
                            mime_type="video/mp4"
                        )
                    ),
                    types.Part(text=f"Analyze this video content: {user_input}")
                ]
        
        # Configure response format
        response_config = None
        if use_structured:
            response_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AgentResponse
            )
        
        # Ensure thinking config includes thoughts for visibility if streaming
        if stream and (self.thinking_budget > 0 or self.thinking_level):
             # We need to make sure config exists
             if not response_config:
                 response_config = types.GenerateContentConfig()
             
             if not response_config.thinking_config:
                 response_config.thinking_config = types.ThinkingConfig()
                 
             # Set include_thoughts to True to get the thought stream
             response_config.thinking_config.include_thoughts = True
             
             # Re-apply budget/level if they were set in start_session but we are overriding config here
             # Note: chat_session config is default, but per-request config overrides it.
             if self.thinking_budget > 0:
                 response_config.thinking_config.thinking_budget = self.thinking_budget
             elif self.thinking_level:
                 if hasattr(response_config.thinking_config, 'thinking_level'):
                     response_config.thinking_config.thinking_level = self.thinking_level

        try:
            if stream:
                # Return the stream generator directly
                return self.chat_session.send_message_stream(
                    message_content,
                    config=response_config
                )
            else:
                # Execute the turn (non-streaming)
                response = await self.chat_session.send_message(
                    message_content,
                    config=response_config
                )
                
                # ... (existing token usage logic) ...
                
                # Handle structured output
                if use_structured and hasattr(response, 'parsed') and response.parsed:
                    result = response.parsed
                    # Inject metadata
                    result.processing_time_ms = (time.time() - start_time) * 1000
                    result.mode = self.mode
                    result.model_version = self.model_id
                    return result
                    
                # Fallback to raw text
                return response.text
            
        except Exception as e:
            # ... (existing error handling) ...
            return str(e) # Simplified for brevity in replacement block
            
    async def classify_intent(self, user_input: str) -> IntentClassification:
        """
        Classify user intent to determine routing.
        Uses Flash tier for speed.
        """
        # Create a temporary Flash-tier agent for classification
        classifier = UnkAgent(
            mode="cost_saver",
            gcp_project=self.gcp_project,
            gcp_location=self.gcp_location,
            enable_structured_output=True
        )
        
        classification_prompt = f"""Classify this user request:

"{user_input}"

Determine:
1. The primary intent
2. Complexity level: trivial, simple, moderate, complex, or extreme
   - NOTE: If the input contains a YouTube link, classify as 'extreme' to trigger yn_mode.
3. Recommended processing mode:
   - trivial/simple -> cost_saver (Flash-Lite 2.5)
   - moderate -> default (Flash 2.5)
   - complex -> unk_mode (Pro 2.5)
   - extreme -> yn_mode (Gemini 3 Pro)
4. What tools might be needed (e.g., analyze_youtube_video)

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
            
        # Add default tools including video analysis
        default_tools = [analyze_youtube_video, calculate_growth_metrics, get_current_timestamp, search_emoji_db]
        combined_tools = (tools or []) + default_tools
        
        return UnkAgent(mode=recommended, tools=combined_tools, **kwargs)


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


def search_emoji_db(query: str) -> List[Dict[str, str]]:
    """
    Search the local emoji database for emojis matching the query.
    
    Args:
        query: Keyword to search for (e.g., "fire", "skull", "cry").
        
    Returns:
        List of matching emojis with their names.
    """
    db_path = "unk_emoji_db.json"
    if not os.path.exists(db_path):
        return [{"error": "Emoji DB not found."}]
        
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        query = query.lower()
        matches = []
        for entry in data:
            if query in entry.get("name", "").lower():
                matches.append(entry)
                if len(matches) >= 10:  # Limit results
                    break
        
        return matches if matches else [{"result": "No matches found."}]
    except Exception as e:
        return [{"error": f"Failed to search DB: {e}"}]


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

def analyze_youtube_video(video_url: str) -> Dict[str, Any]:
    """
    Analyze a YouTube video for content, sentiment, and key insights.
    
    Args:
        video_url: The full URL of the YouTube video.
        
    Returns:
        Analysis results (simulated).
    """
    # In a real implementation, this would use the Gemini 1.5/2.0/3.0 native video understanding
    # by passing the video (or frames/audio) to the model.
    return {
        "status": "simulated_success",
        "video_url": video_url,
        "analysis_mode": "multimodal",
        "insight": "This function is a placeholder. In production, Gemini would process the video frames and audio directly."
    }
