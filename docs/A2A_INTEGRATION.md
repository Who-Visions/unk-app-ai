# A2A Integration - Who Visions Fleet

## Overview

Unk Agent implements the **Agent-to-Agent (A2A) Identity Card** standard to participate in the **Who Visions Fleet**. This allows other agents (Who-Tester, Dav1d, Rhea, Kaedra, etc.) to dynamically discover Unk Agent's capabilities and endpoints.

---

## Standard Endpoint

**URL:** `GET /.well-known/agent.json`  
**Content-Type:** `application/json`  
**Access:** Public (Unauthenticated)

---

## Identity Card Response

```json
{
  "name": "Unk Agent",
  "version": "1.0.0",
  "description": "Enterprise-grade multi-model cognitive agent with dynamic tier routing. Specialist in intelligent task complexity analysis, cost optimization, and scalable AI orchestration across Gemini 2.0/2.5 models.",
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
  "endpoints": {
    "chat": "/chat",
    "chat_routed": "/chat/route",
    "health": "/health",
    "models": "/models",
    "usage": "/usage",
    "pricing_spikes": "/pricing/spikes",
    "pricing_history": "/pricing/history",
    "pricing_trends": "/pricing/trends"
  },
  "models": {
    "tiers": [
      "cost_saver",
      "default",
      "flash_thinking",
      "unk_mode",
      "ultrathink",
      "code_specialist"
    ],
    "primary": "gemini-2.5-pro",
    "routing": "automatic"
  },
  "extensions": {
    "color": "bold magenta",
    "role": "Cognitive Orchestrator",
    "tier_system": "6-tier cognitive routing",
    "memory_type": "Firestore Vector Store",
    "auth_method": "Firebase OIDC",
    "deployment": "Cloud Run",
    "project": "Who Visions LLC",
    "brand": "AI with Dav3",
    "social": {
      "instagram": "@aiwithdav3",
      "youtube": "youtube.com/aiwithdav3"
    }
  }
}
```

---

## Capabilities Explained

| Capability | Description |
|------------|-------------|
| `text-generation` | Natural language generation across all tiers |
| `code-generation` | Code creation with specialized `code_specialist` mode |
| `code-analysis` | Code review, debugging, complexity analysis |
| `reasoning` | Deep reasoning with thinking tokens (Gemini 2.5 Pro) |
| `deep-research` | Comprehensive research with `ultrathink` mode |
| `vector-memory` | Firestore Vector Store with 768-dim embeddings |
| `rag-search` | Semantic memory search with cosine similarity |
| `cost-optimization` | Intelligent cognitive tier routing to minimize costs |
| `cognitive-routing` | Auto-route requests based on complexity analysis |
| `structured-output` | Pydantic-enforced JSON responses |
| `tool-execution` | Function calling with SDK auto-execution |

---

## Cognitive Tier System

Unk Agent's unique **6-tier cognitive routing** system:

| Tier | Model | Cost | Use Case |
|------|-------|------|----------|
| `cost_saver` | Gemini 2.0 Flash Lite | $0.02/$0.08 per 1M tokens | Classification, extraction |
| `default` | Gemini 2.0 Flash | $0.10/$0.40 per 1M tokens | Simple Q&A, greetings |
| `flash_thinking` | Gemini 2.0 Flash Thinking | $0.10/$0.40 per 1M tokens | Moderate reasoning |
| `unk_mode` | Gemini 2.5 Pro | $2.50/$10.00 per 1M tokens | Complex analysis, code gen |
| `ultrathink` | Gemini 2.5 Pro (32k thinking) | $2.50/$10.00 per 1M tokens | Research, system design |
| `code_specialist` | Gemini 2.5 Pro | $2.50/$10.00 per 1M tokens | Code review, debugging |

---

## Fleet Integration

### Discovery by Leader (Who-Tester)

Who-Tester can discover Unk Agent by fetching the identity card:

```bash
curl https://unk-agent-url/.well-known/agent.json
```

### Agent-to-Agent Communication

Other agents in the fleet can:
1. **Discover capabilities** via the A2A card
2. **Route complex tasks** to Unk Agent's `ultrathink` tier
3. **Leverage cost optimization** for high-volume inference
4. **Access vector memory** for shared knowledge retrieval

---

## Testing

### Local Testing
```bash
# Start Unk Agent locally
python deploy.py

# In another terminal, fetch the A2A card
curl http://localhost:8080/.well-known/agent.json
```

### Production Testing
```bash
# Cloud Run deployment
curl https://unk-agent-xyz.run.app/.well-known/agent.json
```

### Expected Response
Status: `200 OK`  
Content-Type: `application/json`

---

## Fleet Member Profile

**Agent Name:** Unk Agent  
**Role:** Cognitive Orchestrator  
**Color:** Bold Magenta  
**Specialty:** Multi-tier cognitive routing, cost optimization, scalable AI orchestration

**Fleet Position:**
- **Collaborates with Dav1d** for specialized Python implementation
- **Works with Kaedra** for security/compliance auditing
- **Supports Rhea** with advanced reasoning capabilities
- **Reports to Who-Tester** as fleet coordinator

---

## Implementation Details

### Code Location
- **File:** `deploy.py`
- **Line:** ~323
- **Function:** `agent_identity_card()`

### Dependencies
- FastAPI JSONResponse
- No authentication required (public endpoint)
- No database queries (static configuration)

### Performance
- **Response Time:** <10ms
- **Caching:** Not required (static data)
- **Rate Limiting:** Not applied

---

## Future Enhancements

### V1.1 (Planned)
- [ ] Dynamic capability detection based on enabled features
- [ ] Real-time model availability status
- [ ] Current tier usage statistics
- [ ] Fleet coordination metadata

### V2.0 (Proposed)
- [ ] Agent-to-Agent authentication
- [ ] Capability negotiation protocol
- [ ] Distributed task routing
- [ ] Fleet-wide knowledge sharing

---

## Related Documentation

- [A2A Implementation Guide](c:\Users\super\HQ_Blade\Chrome Dls\a2a_implementation_guide.md (2).resolved)
- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)
- [Gemini Integration](GEMINI.md)

---

*Who Visions LLC - AI with Dav3*  
*A2A Standard: v1.0.0*  
*Last Updated: December 14, 2025*
