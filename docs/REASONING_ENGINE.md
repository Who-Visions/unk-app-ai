# Unk Agent - Reasoning Engine Deployment Guide

## 🧠 Vertex AI Reasoning Engine

Deploy Unk Agent as a Vertex AI Reasoning Engine for agent-to-agent coordination in the Who Visions Fleet.

---

## Prerequisites

1. **GCP Project**: `unk-app-480102`
2. **Location**: `us-central1`
3. **APIs Enabled**:
   - Vertex AI API
   - Cloud Storage API
4. **Permissions**: Vertex AI User, Storage Admin

---

## Quick Deploy

### From Cloud Shell:

```bash
# 1. Clone repository
git clone https://github.com/Who-Visions/unk-app-ai.git
cd unk-app-ai

# 2. Set project
gcloud config set project unk-app-480102

# 3. Enable APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com

# 4. Create staging bucket
gsutil mb -l us-central1 gs://unk-app-480102-reasoning-engine

# 5. Install dependencies
pip install -r reasoning_engine_requirements.txt

# 6. Deploy reasoning engine
python reasoning_engine_deploy.py
```

---

## Deployment Output

Expected output:
```
======================================================================
UNK AGENT - REASONING ENGINE DEPLOYMENT
======================================================================
Project: unk-app-480102
Location: us-central1
Staging Bucket: gs://unk-app-480102-reasoning-engine
======================================================================

🚀 Creating Reasoning Engine...
✅ Reasoning Engine deployed successfully!

Resource Name: projects/574321322006/locations/us-central1/reasoningEngines/1234567890
Display Name: unk-agent-reasoning-engine

🧪 Testing Reasoning Engine...

Test Result:
Success: True
Mode: default
Response: Hello! I'm Unk Agent, a cognitive orchestrator...

📋 Agent Capabilities:
Name: Unk Agent
Role: Cognitive Orchestrator
Tiers: cost_saver, default, flash_thinking, unk_mode, ultrathink, code_specialist

======================================================================
DEPLOYMENT COMPLETE!
======================================================================
```

---

## Using the Reasoning Engine

### Python SDK:

```python
from vertexai.preview import reasoning_engines
from google.cloud import aiplatform

# Initialize
aiplatform.init(
    project="unk-app-480102",
    location="us-central1"
)

# Load the engine
agent = reasoning_engines.ReasoningEngine(
    "projects/574321322006/locations/us-central1/reasoningEngines/<ID>"
)

# Query with auto-routing
response = agent.query(
    prompt="Design a microservices architecture",
    mode="auto"
)

print(response["response"])
print(f"Mode used: {response['mode']}")
```

### Specific Tier:

```python
# Use ultrathink for deep research
response = agent.query(
    prompt="Comprehensive analysis of distributed systems",
    mode="ultrathink"
)

# Use cost_saver for simple tasks
response = agent.query(
    prompt="What is 2 + 2?",
    mode="cost_saver"
)
```

### Get Capabilities:

```python
capabilities = agent.get_capabilities()
print(f"Tiers: {capabilities['tiers']}")
print(f"Role: {capabilities['role']}")
```

---

## Cognitive Tiers

The reasoning engine supports 6 cognitive tiers:

| Tier | Model | Use Case |
|------|-------|----------|
| `cost_saver` | Gemini 2.0 Flash Lite | Classification, extraction |
| `default` | Gemini 2.0 Flash | Simple Q&A |
| `flash_thinking` | Gemini 2.0 Flash Thinking | Moderate reasoning |
| `unk_mode` | Gemini 2.5 Pro | Complex analysis |
| `ultrathink` | Gemini 2.5 Pro (32k thinking) | Research, design |
| `code_specialist` | Gemini 2.5 Pro | Code review |

---

## Auto-Routing

Set `mode="auto"` to automatically route based on complexity:

```python
# Automatically selects appropriate tier
response = agent.query(
    prompt="Your question here",
    mode="auto"
)
```

**Complexity Classification:**
- **Trivial** → `cost_saver`
- **Simple** → `default`
- **Moderate** → `flash_thinking`
- **Complex** → `unk_mode`
- **Extreme** → `ultrathink`

---

## Fleet Integration

### A2A Discovery

Update the deployed Cloud Run service's A2A card:

```json
{
  "name": "Unk Agent",
  "version": "1.0.0",
  "reasoning_engine": {
    "enabled": true,
    "resource_name": "projects/574321322006/locations/us-central1/reasoningEngines/<ID>",
    "location": "us-central1"
  }
}
```

### Agent-to-Agent Calls

Other agents (Who-Tester, Dav1d, Rhea) can now:

```python
# From another agent
from vertexai.preview import reasoning_engines

unk_agent = reasoning_engines.ReasoningEngine(
    "projects/574321322006/locations/us-central1/reasoningEngines/<ID>"
)

# Delegate complex task to Unk
result = unk_agent.query(
    prompt="Optimize this cost analysis",
    mode="unk_mode"
)
```

---

## Monitoring

### List All Engines:

```bash
gcloud ai reasoning-engines list \
  --project=unk-app-480102 \
  --location=us-central1
```

### Get Engine Details:

```bash
gcloud ai reasoning-engines describe <ENGINE_ID> \
  --project=unk-app-480102 \
  --location=us-central1
```

---

## Updating the Engine

To update the engine after code changes:

```bash
# Re-run deployment
python reasoning_engine_deploy.py
```

This creates a new version. Update references to the new resource name.

---

## Troubleshooting

### Issue: Staging bucket doesn't exist

```bash
gsutil mb -l us-central1 gs://unk-app-480102-reasoning-engine
```

### Issue: API not enabled

```bash
gcloud services enable aiplatform.googleapis.com
```

### Issue: Permissions error

Ensure your service account has:
- `Vertex AI User`
- `Storage Object Admin`

---

## Cost Optimization

The reasoning engine uses cognitive routing to minimize costs:

- **Simple queries** → Flash models (~$0.10/1M tokens)
- **Complex queries** → Pro models (~$2.50/1M tokens)
- **Auto-routing** → Optimal tier selection

Expected cost: **~$50-100/month** for moderate usage

---

## Next Steps

1. ✅ Deploy reasoning engine
2. ✅ Test with sample queries
3. ✅ Update A2A card with engine resource name
4. ✅ Integrate with Who-Tester fleet
5. ⏭️ Set up monitoring dashboards
6. ⏭️ Configure auto-scaling policies

---

*Who Visions LLC - AI with Dav3*  
*Reasoning Engine: Unk Agent v1.0.0*  
*Last Updated: December 14, 2025*
