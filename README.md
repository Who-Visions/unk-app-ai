# Unk Agent

**Multi-Model Cognitive Agent System**

Enterprise-grade AI agent with dynamic cognitive tiering, built for GCP deployment.

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ██╗   ██╗███╗   ██╗██╗  ██╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗ ║
║   ██║   ██║████╗  ██║██║ ██╔╝    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝ ║
║   ██║   ██║██╔██╗ ██║█████╔╝     ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║    ║
║   ██║   ██║██║╚██╗██║██╔═██╗     ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║    ║
║   ╚██████╔╝██║ ╚████║██║  ██╗    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║    ║
║    ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝    ║
║                                                                           ║
║   Who Visions LLC | AI with Dav3                                         ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

## Overview

Unk Agent is a production-ready multi-model AI agent system that dynamically routes requests to the appropriate cognitive tier based on task complexity. Built on Google's Gemini model ecosystem and deployed to GCP Cloud Run.

### Key Features

- **Cognitive Tiering**: Automatic routing between Flash (speed) → Pro (reasoning) → Ultra (deep analysis)
- **Async Architecture**: High-concurrency FastAPI/ASGI deployment
- **Vector Memory**: Firestore-backed RAG with semantic search
- **OIDC Authentication**: Firebase Auth integration for secure access
- **Structured Output**: Pydantic-enforced JSON responses
- **Cost Optimization**: Smart routing to minimize API costs

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI GATEWAY (deploy.py)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │    CORS      │  │    OIDC      │  │   Request Routing    │  │
│  │  Middleware  │  │   Verify     │  │   /chat, /chat/route │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INTENT CLASSIFIER                            │
│         Determines complexity → routes to appropriate tier      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   FLASH     │   │  UNK MODE   │   │ ULTRATHINK  │
│  Gemini 2.0 │   │ Gemini 2.5  │   │ Gemini 2.5  │
│   Flash     │   │    Pro      │   │ Pro (32k)   │
│  ~$0.10/1M  │   │  ~$2.50/1M  │   │  Extended   │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └────────────────┬┴─────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TOOL EXECUTION LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Memory     │  │  Calculator  │  │   Custom Tools       │  │
│  │   Search     │  │   Metrics    │  │   (Extensible)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FIRESTORE VECTOR STORE                       │
│              Semantic memory with cosine similarity             │
└─────────────────────────────────────────────────────────────────┘
```

## Cognitive Tiers

| Mode | Model | Cost/1M Tokens | Use Cases |
|------|-------|----------------|-----------|
| `default` | Gemini 2.0 Flash | $0.10 in / $0.40 out | Greetings, simple Q&A, routing |
| `flash_thinking` | Gemini 2.0 Flash Thinking | $0.10 in / $0.40 out | Moderate reasoning, planning |
| `unk_mode` | Gemini 2.5 Pro | $2.50 in / $10.00 out | Complex analysis, code generation |
| `ultrathink` | Gemini 2.5 Pro (32k thinking) | $2.50 in / $10.00 out | System design, research synthesis |
| `code_specialist` | Gemini 2.5 Pro | $2.50 in / $10.00 out | Code review, debugging |
| `cost_saver` | Gemini 2.0 Flash Lite | $0.02 in / $0.08 out | Classification, extraction |

## Quick Start

### Prerequisites

- Python 3.11+
- GCP Project with Vertex AI enabled
- Firebase project (for authentication)

### Installation

```bash
# Clone the repository
git clone https://github.com/whovisions/unk-agent.git
cd unk-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_CLOUD_PROJECT="your-gcp-project"
export ENV="development"
```

### Running Locally

```bash
# Start the development server
python deploy.py

# Server runs at http://localhost:8080
# API docs at http://localhost:8080/docs
```

### Making Requests

```bash
# Health check
curl http://localhost:8080/health

# Chat (with dev token)
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev_token" \
  -d '{
    "message": "Analyze the architecture for a real-time data pipeline",
    "mode": "unk_mode"
  }'

# Auto-routed chat
curl -X POST http://localhost:8080/chat/route \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev_token" \
  -d '{
    "message": "What is 2 + 2?"
  }'
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "deploy:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/unk-agent
gcloud run deploy unk-agent \
  --image gcr.io/$PROJECT_ID/unk-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "ENV=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
```

## Project Structure

```
unk-agent/
├── deploy.py                 # FastAPI application
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container definition
├── gemini_agent/
│   ├── __init__.py          # Package exports
│   ├── models_spec.py       # GEMINI_MODELS configuration
│   ├── agent.py             # UnkAgent core implementation
│   └── memory.py            # Vector memory system
├── docs/
│   ├── ARCHITECTURE.md      # System architecture
│   ├── ROADMAP.md           # Development roadmap
│   ├── CLAUDE.md            # Claude orchestration guide
│   └── GEMINI.md            # Gemini integration guide
└── scripts/
    └── setup_gcp.sh         # GCP setup automation
```

## API Reference

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/models` | List available modes |
| GET | `/models/{mode}` | Get mode details |
| POST | `/chat` | Chat with specified mode |
| POST | `/chat/route` | Auto-routed chat |
| GET | `/usage` | Get usage statistics |

### Response Format

```json
{
  "success": true,
  "data": {
    "reasoning_trace": [
      {
        "step_number": 1,
        "thought_type": "analysis",
        "thought": "Breaking down the problem...",
        "confidence": 0.9
      }
    ],
    "final_answer": "The analysis shows...",
    "model_version": "gemini-2.5-pro-preview-06-05",
    "mode": "unk_mode",
    "token_usage": {
      "input": 150,
      "output": 450
    },
    "estimated_cost": 0.0048,
    "processing_time_ms": 2340.5
  },
  "request_id": "a1b2c3d4",
  "processing_time_ms": 2345.2
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Required |
| `GCP_LOCATION` | GCP region | `us-central1` |
| `ENV` | Environment (development/production) | `development` |
| `PORT` | Server port | `8080` |

### Firestore Indexes

Create the following composite index for vector search:

```bash
gcloud firestore indexes composite create \
  --collection-group=unk_memory \
  --query-scope=COLLECTION \
  --field-config field-path=embedding,vector-config='{"dimension":"768","flat":"{}"}' \
  --field-config field-path=memory_type,order=ASCENDING
```

## Cost Optimization

The $1,000 GCP credit strategy:

1. **Default to Flash**: 90%+ of requests use the default tier (~$0.10/1M tokens)
2. **Gate Pro Modes**: Require subscription for `unk_mode` and `ultrathink`
3. **Intent Classification**: Use Flash tier for routing decisions
4. **Caching**: Implement context caching for repeated queries

### Estimated Capacity

| Tier | Cost per 1k Turns | Turns per $100 |
|------|-------------------|----------------|
| Flash | ~$0.0005 | ~200,000 |
| Pro | ~$0.0125 | ~8,000 |

## License

Proprietary - Who Visions LLC

## Contact

- Website: [aiwithdav3.com](https://aiwithdav3.com)
- GitHub: [@whovisions](https://github.com/whovisions)
