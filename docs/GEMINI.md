# GEMINI.md

## Gemini Model Integration Guide

Comprehensive guide for working with the Gemini model ecosystem in the Unk Agent system.

---

## Model Ecosystem Overview

### Generation Timeline

```
2024 Q1-Q2: Gemini 1.0 (Legacy)
2024 Q2-Q4: Gemini 1.5 Pro/Flash (1M context)
2025 Q1:    Gemini 2.0 Flash (Agentic focus)
2025 Q2:    Gemini 2.5 Pro (Thinking tokens)
2025 H2:    Gemini 2.5 Flash variants
2026+:      Gemini 3.0 (Expected)
```

### Current Production Models

| Model ID | Release | Context | Specialty |
|----------|---------|---------|-----------|
| `gemini-2.0-flash-001` | 2025-02 | 1M | Speed, tools |
| `gemini-2.0-flash-thinking-exp` | 2025-01 | 1M | Reasoning + speed |
| `gemini-2.5-pro-preview-06-05` | 2025-06 | 2M | Deep reasoning |
| `gemini-2.0-flash-lite-001` | 2025-02 | 1M | Cost efficiency |
| `text-embedding-004` | 2024-05 | N/A | Vector embeddings |

---

## The google-genai SDK

### Installation

```bash
pip install google-genai>=0.6.0
```

### Client Initialization

```python
from google import genai

# Vertex AI backend (production)
client = genai.Client(
    vertexai=True,
    project="your-gcp-project",
    location="us-central1"
)

# Developer API (development)
client = genai.Client(
    api_key="your-api-key"
)
```

### Async Operations

```python
# Async chat session
chat = client.aio.chats.create(
    model="gemini-2.0-flash-001",
    history=[],
    config=generation_config
)

# Async message
response = await chat.send_message("Hello")
```

---

## Cognitive Tiering Implementation

### Tier Definitions

```python
COGNITIVE_TIERS = {
    "lite": {
        "models": ["gemini-2.0-flash-lite-001"],
        "use_cases": ["classification", "extraction"],
        "max_complexity": 1
    },
    "flash": {
        "models": ["gemini-2.0-flash-001"],
        "use_cases": ["conversation", "simple_reasoning"],
        "max_complexity": 3
    },
    "pro": {
        "models": ["gemini-2.5-pro-preview-06-05"],
        "use_cases": ["complex_reasoning", "code_generation"],
        "max_complexity": 8
    },
    "ultra": {
        "models": ["gemini-2.5-pro-preview-06-05"],
        "use_cases": ["system_design", "research"],
        "max_complexity": 10,
        "thinking_budget": 32768
    }
}
```

### Routing Algorithm

```python
def route_to_tier(task_complexity: int, user_tier: str) -> str:
    """Route task to appropriate cognitive tier."""
    
    if task_complexity <= 1:
        return "lite"
    elif task_complexity <= 3:
        return "flash"
    elif task_complexity <= 6:
        if user_tier in ["pro", "enterprise"]:
            return "pro"
        return "flash"  # Fallback for free users
    else:
        if user_tier == "enterprise":
            return "ultra"
        elif user_tier == "pro":
            return "pro"
        return "flash"  # Maximum fallback
```

---

## Thinking Tokens (Gemini 2.5+)

### What Are Thinking Tokens?

Gemini 2.5 Pro introduces "thinking tokens" - internal reasoning steps the model takes before producing output. These enable chain-of-thought reasoning without explicit prompting.

### Configuration

```python
from google.genai import types

# Enable thinking with budget
config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(
        thinking_budget=8192  # Up to 65536
    )
)
```

### Budget Guidelines

| Budget | Use Case | Cost Impact |
|--------|----------|-------------|
| 2048 | Simple reasoning | +10% tokens |
| 8192 | Standard complex tasks | +50% tokens |
| 16384 | Deep analysis | +100% tokens |
| 32768 | System design | +200% tokens |
| 65536 | Maximum depth | +400% tokens |

### Accessing Thinking Content

```python
response = await chat.send_message(prompt, config=config)

# Thinking content (if available)
if hasattr(response, 'thinking_content'):
    for thought in response.thinking_content:
        print(f"Thought: {thought}")

# Final answer
print(response.text)
```

---

## Tool/Function Calling

### Defining Tools

```python
def calculate_metric(value: float, baseline: float) -> dict:
    """
    Calculate percentage change from baseline.
    
    Args:
        value: Current value
        baseline: Baseline value for comparison
        
    Returns:
        Dictionary with change percentage and status
    """
    change = ((value - baseline) / baseline) * 100
    return {
        "change_percentage": round(change, 2),
        "status": "increase" if change > 0 else "decrease"
    }
```

### Registering Tools

```python
tools = [calculate_metric, other_function]

config = types.GenerateContentConfig(
    tools=tools,
    tool_config=types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(
            mode="AUTO"  # AUTO, ANY, or NONE
        )
    )
)
```

### Tool Execution Flow

```
1. User sends message
2. Model analyzes and decides to call tool
3. Model returns FunctionCall object
4. Your code executes the function
5. Result is sent back to model
6. Model synthesizes final response
```

### Automatic Execution

The SDK handles the loop automatically when tools are registered in a chat session:

```python
chat = client.aio.chats.create(
    model="gemini-2.0-flash-001",
    config=types.GenerateContentConfig(
        tools=[my_tool]
    )
)

# SDK handles: call → execute → return → synthesize
response = await chat.send_message("Calculate the change from 100 to 150")
```

---

## Structured Output

### With Pydantic Models

```python
from pydantic import BaseModel, Field

class AnalysisResult(BaseModel):
    summary: str = Field(..., description="Brief summary")
    confidence: float = Field(..., ge=0, le=1)
    recommendations: list[str] = Field(default_factory=list)

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=AnalysisResult
)

response = await chat.send_message(prompt, config=config)

# Access parsed object
result: AnalysisResult = response.parsed
```

### JSON Schema Direct

```python
schema = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number"}
    },
    "required": ["answer"]
}

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=schema
)
```

---

## Multimodal Capabilities

### Image Input

```python
import base64

with open("image.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = await client.aio.models.generate_content(
    model="gemini-2.0-flash-001",
    contents=[
        types.Part.from_image(
            image=types.Image(
                mime_type="image/png",
                data=image_data
            )
        ),
        types.Part.from_text("Describe this image")
    ]
)
```

### Video Input

```python
# Upload to Google Cloud Storage first
video_uri = "gs://bucket/video.mp4"

response = await client.aio.models.generate_content(
    model="gemini-2.0-flash-001",
    contents=[
        types.Part.from_uri(
            file_uri=video_uri,
            mime_type="video/mp4"
        ),
        types.Part.from_text("Summarize this video")
    ]
)
```

---

## Embeddings

### Generate Embeddings

```python
result = client.models.embed_content(
    model="text-embedding-004",
    contents="Text to embed"
)

embedding = result.embeddings[0].values  # List[float]
```

### Batch Embeddings

```python
texts = ["First text", "Second text", "Third text"]

result = client.models.embed_content(
    model="text-embedding-004",
    contents=texts
)

embeddings = [e.values for e in result.embeddings]
```

### Dimensionality

- `text-embedding-004`: 768 dimensions
- Firestore limit: 2048 dimensions
- Compatible with cosine similarity

---

## Context Caching

### What Is Context Caching?

For repeated queries with the same large context (system prompts, documents), you can cache the context to reduce costs.

### Implementation

```python
# Create a cached context
cache = await client.caches.create(
    model="gemini-2.0-flash-001",
    contents=[
        types.Content(
            role="user",
            parts=[types.Part.from_text(large_system_prompt)]
        )
    ],
    ttl="3600s"  # 1 hour
)

# Use cached context
response = await client.aio.models.generate_content(
    model="gemini-2.0-flash-001",
    cached_content=cache.name,
    contents=[types.Part.from_text("User query")]
)
```

### Cost Savings

- Cached input tokens: 75% discount
- Cache storage: ~$4.50/1M tokens/hour
- Break-even: ~4 requests with same context

---

## Rate Limits and Quotas

### Default Limits (Vertex AI)

| Model Tier | RPM | TPM |
|------------|-----|-----|
| Flash | 1000 | 4,000,000 |
| Pro | 150 | 1,000,000 |
| Ultra | 60 | 500,000 |

### Handling Rate Limits

```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5)
)
async def make_request(prompt: str):
    return await chat.send_message(prompt)
```

---

## Error Handling

### Common Errors

```python
from google.api_core import exceptions

try:
    response = await chat.send_message(prompt)
except exceptions.ResourceExhausted:
    # Rate limit hit - back off and retry
    pass
except exceptions.InvalidArgument:
    # Bad input - check prompt/config
    pass
except exceptions.DeadlineExceeded:
    # Timeout - reduce complexity or retry
    pass
except exceptions.InternalServerError:
    # Server error - retry with backoff
    pass
```

### Graceful Degradation

```python
async def resilient_generate(prompt: str, preferred_mode: str):
    """Try preferred mode, fall back to lower tiers."""
    
    fallback_chain = {
        "ultrathink": ["unk_mode", "flash_thinking", "default"],
        "unk_mode": ["flash_thinking", "default"],
        "flash_thinking": ["default"],
        "default": ["cost_saver"]
    }
    
    modes_to_try = [preferred_mode] + fallback_chain.get(preferred_mode, [])
    
    for mode in modes_to_try:
        try:
            agent = UnkAgent(mode=mode)
            return await agent.execute_turn(prompt)
        except exceptions.ResourceExhausted:
            continue
        except Exception as e:
            logger.error(f"Error with {mode}: {e}")
            continue
    
    raise RuntimeError("All models exhausted")
```

---

## Best Practices

### 1. Temperature Settings

| Task Type | Temperature |
|-----------|-------------|
| Factual/Code | 0.0 - 0.2 |
| Analysis | 0.2 - 0.5 |
| Creative | 0.7 - 1.0 |
| Brainstorming | 0.9 - 1.2 |

### 2. Prompt Engineering

```python
# Good: Specific, structured
prompt = """
Analyze the following code for security vulnerabilities.

Code:
```python
{code}
```

Provide:
1. List of vulnerabilities found
2. Severity rating (low/medium/high/critical)
3. Recommended fixes
"""

# Bad: Vague, unstructured
prompt = "Check this code: {code}"
```

### 3. Token Optimization

- Use concise prompts
- Strip unnecessary whitespace
- Compress large contexts with summarization
- Use structured output to avoid verbose responses

### 4. Cost Monitoring

```python
def estimate_cost(mode: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost before making request."""
    spec = GEMINI_MODELS[mode]
    pricing = spec["pricing"]
    
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    
    return input_cost + output_cost
```

---

## Migration Notes

### From 1.5 to 2.0/2.5

1. Update model strings in GEMINI_MODELS
2. Test tool calling compatibility
3. Verify structured output schemas
4. Adjust rate limit handling
5. Enable thinking tokens where appropriate

### Deprecation Timeline

| Model | Deprecation | End of Life |
|-------|-------------|-------------|
| gemini-1.0-* | 2024-02 | 2024-08 |
| gemini-1.5-flash-001 | 2025-09 | 2026-03 |
| gemini-1.5-pro-001 | 2025-09 | 2026-03 |

---

## Resources

- [Google GenAI SDK Docs](https://ai.google.dev/gemini-api/docs)
- [Vertex AI Generative AI](https://cloud.google.com/vertex-ai/generative-ai/docs)
- [Gemini API Pricing](https://ai.google.dev/pricing)
- [Model Versions & Lifecycle](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions)

---

*Who Visions LLC - AI with Dav3*
