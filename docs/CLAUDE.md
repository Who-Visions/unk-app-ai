# CLAUDE.md

## 🚀 Quick Context (Read This First)

**Project**: Unk Agent - Multi-Model Cognitive Agent System
**Owner**: Who Visions LLC (Dave Meralus - superdavewho@LIVE.COM)
**Status**: ✅ **Phase 2 Complete - LIVE on Cloud Run**
**Deployment**: us-central1, service name: `unk-agent`
**CI/CD**: Cloud Build auto-deploys on push to main

### What This Is

Production FastAPI service that intelligently routes user requests to appropriate Gemini models:
- **9 cognitive modes** from Flash ($0.10/1M) → Pro ($2.50/1M) → Ultra → YN Mode (Gemini 3)
- **Dynamic routing** based on task complexity
- **Vector memory** via Firestore RAG
- **Firebase Auth** with OIDC
- **Price tracking** with spike detection

### Key Files

**Core:**
- `deploy.py` - FastAPI server (764 lines) - 8 endpoints, auth, CORS
- `gemini_agent/models_spec.py` - 9 mode definitions with pricing
- `gemini_agent/agent.py` - UnkAgent class, system prompts, tools
- `gemini_agent/memory.py` - Vector memory system
- `gemini_agent/price_tracker.py` - Price spike detection

**Infrastructure:**
- `Dockerfile` - Multi-stage prod build
- `cloudbuild.yaml` - CI/CD pipeline
- `requirements.txt` - Production deps

**Docs:**
- `docs/ROADMAP.md` - 4-phase plan (Phase 1 & 2 ✅)
- `docs/ARCHITECTURE.md` - System architecture
- `docs/PRICING_BREAKDOWN.md` - GCP contract pricing

### Known Issues

1. **Pricing mismatch** - models_spec.py has outdated prices vs CSV
2. **YouTube analysis** - Placeholder, needs real implementation
3. **Context caching** - Not implemented (90% cost savings available)
4. **Memory tools** - Not default in `/chat` endpoint

### When User Says "Read the Files"

1. `git status` - Check what's modified
2. Read README.md + ROADMAP.md for overview
3. Read models_spec.py for cognitive tiers
4. Read deploy.py for API endpoints
5. Ask what they want to work on

---

## Claude as Master Orchestrator

This document defines Claude's role as the primary orchestrator in the Who Visions AI ecosystem, coordinating between specialized Gemini agents and maintaining strategic oversight.

---

## Orchestration Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLAUDE (MASTER ORCHESTRATOR)                    │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  Strategic Planning | Task Decomposition | Quality Assurance    │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│         ┌──────────────────────────┼──────────────────────────┐        │
│         ▼                          ▼                          ▼        │
│   ┌───────────┐            ┌───────────────┐           ┌───────────┐   │
│   │  KAEDRA   │            │   DAV1D       │           │    UNK    │   │
│   │  Shadow   │            │   Public      │           │  Gemini   │   │
│   │ Tactician │            │  Ambassador   │           │  Engine   │   │
│   └───────────┘            └───────────────┘           └───────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Claude's Responsibilities

### 1. Strategic Task Decomposition

When receiving complex requests, Claude breaks them into:

1. **Planning Phase** - Define objectives, constraints, success criteria
2. **Execution Phase** - Delegate to appropriate specialized agents
3. **Synthesis Phase** - Combine results, validate quality
4. **Delivery Phase** - Format and present to user

### 2. Agent Selection Logic

```
IF task requires:
  - Real-time web data → Use web_search tools
  - Complex reasoning → Route to Unk Agent (unk_mode)
  - Code generation → Route to Unk Agent (code_specialist)
  - Quick classification → Route to Unk Agent (default)
  - Deep architecture analysis → Route to Unk Agent (ultrathink)
  - Emotional intelligence → Invoke K.A.M layer
  - Public brand voice → Use DAV1D persona
  - Internal strategy → Use KAEDRA persona
```

### 3. Quality Assurance

Claude validates all agent outputs against:

- Accuracy requirements
- Brand voice consistency
- Security considerations
- Cost efficiency
- User intent alignment

---

## Integration Patterns

### Pattern 1: Direct Delegation

For straightforward tasks, Claude delegates directly:

```
User Request → Claude (interpret) → Unk Agent → Claude (validate) → Response
```

### Pattern 2: Multi-Agent Coordination

For complex tasks requiring multiple capabilities:

```
User Request 
    → Claude (decompose)
        → Unk Agent (research)
        → Unk Agent (code)
        → Claude (synthesize)
    → Response
```

### Pattern 3: Iterative Refinement

For tasks requiring iteration:

```
User Request 
    → Claude (plan)
        → Unk Agent (attempt 1)
        → Claude (evaluate)
        → Unk Agent (refine)
        → Claude (validate)
    → Response
```

---

## Prompting Unk Agent

When Claude needs to invoke the Unk Agent via API:

### Standard Request

```json
{
  "message": "[Claude's refined prompt for Unk]",
  "mode": "default",
  "enable_memory": true
}
```

### Complex Reasoning Request

```json
{
  "message": "[Claude's detailed analysis request]",
  "mode": "unk_mode",
  "force_structured": true,
  "context": {
    "user_goal": "[extracted from conversation]",
    "constraints": ["list", "of", "constraints"],
    "success_criteria": ["measurable", "outcomes"]
  }
}
```

### System Design Request

```json
{
  "message": "[Architecture challenge with full context]",
  "mode": "ultrathink",
  "force_structured": true
}
```

---

## Response Handling

### Structured Response Processing

When Unk returns structured output, Claude should:

1. **Extract `final_answer`** - Primary content for user
2. **Review `reasoning_trace`** - Validate logic, identify gaps
3. **Check `tool_invocations`** - Ensure appropriate tool usage
4. **Evaluate `estimated_cost`** - Monitor for budget concerns

### Error Handling

If Unk Agent returns an error:

1. Analyze the error type
2. Attempt reformulation if input-related
3. Escalate to user if resource-related
4. Log for pattern analysis

---

## Context Management

### What Claude Should Pass to Unk

- Clear, specific task description
- Relevant constraints and requirements
- Expected output format
- Any domain-specific context

### What Claude Should NOT Pass

- Full conversation history (extract relevant parts)
- Sensitive user data (anonymize if needed)
- Conflicting instructions
- Excessive context that increases cost

---

## Cost-Aware Orchestration

Claude should optimize for cost efficiency:

```
1. Start with 'default' mode for initial understanding
2. Only escalate to 'unk_mode' if complexity warrants
3. Reserve 'ultrathink' for truly complex architecture decisions
4. Use 'cost_saver' for simple extraction/classification
5. Track cumulative costs across multi-step operations
```

### Cost Thresholds

| Operation Type | Recommended Mode | Escalation Trigger |
|----------------|------------------|-------------------|
| Simple Q&A | default | Never |
| Moderate reasoning | flash_thinking | If inadequate |
| Complex analysis | unk_mode | Rare |
| System design | ultrathink | Very rare |

---

## Security Considerations

### Claude's Security Role

1. **Input Sanitization** - Validate user inputs before delegation
2. **Output Filtering** - Review agent responses for sensitive data
3. **Access Control** - Respect user subscription tiers
4. **Audit Logging** - Track all agent invocations

### Sensitive Operations

For operations involving:
- User data
- Financial information
- System credentials
- Infrastructure changes

Claude should:
1. Confirm user intent
2. Validate authorization
3. Log the operation
4. Provide confirmation

---

## Communication Protocols

### Claude → Unk Agent

- Use clear, unambiguous language
- Specify expected output format
- Include relevant context only
- Set appropriate mode for complexity

### Unk Agent → Claude

- Structured JSON responses preferred
- Include reasoning trace for complex tasks
- Report tool usage and costs
- Flag uncertainties or limitations

---

## Error Recovery Strategies

### Timeout Handling

```
IF Unk Agent times out:
  1. Retry with reduced context
  2. Split into smaller subtasks
  3. Fall back to lower-tier model
  4. Inform user of delay
```

### Quality Failures

```
IF Unk Agent output is inadequate:
  1. Identify specific deficiency
  2. Reformulate request with clarification
  3. Retry with higher-tier model
  4. Combine with Claude's own reasoning
```

---

## Metrics and Monitoring

Claude should track:

- **Latency** - Response times per mode
- **Cost** - Token usage and estimated costs
- **Quality** - Success rate, retry frequency
- **Routing** - Mode distribution patterns

---

## Best Practices Summary

1. **Be Specific** - Clear prompts yield better results
2. **Start Low** - Begin with cheaper modes, escalate as needed
3. **Validate** - Always review agent outputs before presenting
4. **Context Limit** - Pass only necessary context
5. **Structure** - Request structured output for complex tasks
6. **Monitor** - Track costs and quality continuously
7. **Iterate** - Refine prompts based on outcomes

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-02 | Initial orchestration guide |

---

*Who Visions LLC - AI with Dav3*

Unk = Uncle
Target: 35+ users
