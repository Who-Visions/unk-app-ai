# ARCHITECTURE.md

## Unk Agent System Architecture

Comprehensive architecture documentation for the multi-model cognitive agent system.

---

## System Overview

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                              UNK AGENT SYSTEM                             ║
║                                                                           ║
║   ┌─────────────────────────────────────────────────────────────────┐    ║
║   │                        CLIENT LAYER                             │    ║
║   │   Web App (Next.js)  │  Mobile App  │  CLI Tools  │  API       │    ║
║   └─────────────────────────────────────────────────────────────────┘    ║
║                                    │                                      ║
║                                    ▼                                      ║
║   ┌─────────────────────────────────────────────────────────────────┐    ║
║   │                       API GATEWAY LAYER                         │    ║
║   │                                                                 │    ║
║   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │    ║
║   │   │   Cloud     │  │   Firebase  │  │    Rate Limiting    │    │    ║
║   │   │    Run      │  │    Auth     │  │    & Throttling     │    │    ║
║   │   └─────────────┘  └─────────────┘  └─────────────────────┘    │    ║
║   │                                                                 │    ║
║   └─────────────────────────────────────────────────────────────────┘    ║
║                                    │                                      ║
║                                    ▼                                      ║
║   ┌─────────────────────────────────────────────────────────────────┐    ║
║   │                      ORCHESTRATION LAYER                        │    ║
║   │                                                                 │    ║
║   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │    ║
║   │   │   Intent    │  │   Routing   │  │    Session          │    │    ║
║   │   │ Classifier  │  │   Engine    │  │    Manager          │    │    ║
║   │   └─────────────┘  └─────────────┘  └─────────────────────┘    │    ║
║   │                                                                 │    ║
║   └─────────────────────────────────────────────────────────────────┘    ║
║                                    │                                      ║
║         ┌──────────────────────────┼──────────────────────────┐          ║
║         ▼                          ▼                          ▼          ║
║   ┌───────────┐            ┌───────────────┐           ┌───────────┐    ║
║   │   FLASH   │            │   UNK MODE    │           │ULTRATHINK │    ║
║   │   TIER    │            │    (PRO)      │           │  (ULTRA)  │    ║
║   │           │            │               │           │           │    ║
║   │  2.0 Flash│            │  2.5 Pro      │           │  2.5 Pro  │    ║
║   │  2.0 Lite │            │  + Thinking   │           │  + 32k    │    ║
║   └─────┬─────┘            └───────┬───────┘           └─────┬─────┘    ║
║         │                          │                          │          ║
║         └──────────────────────────┼──────────────────────────┘          ║
║                                    │                                      ║
║                                    ▼                                      ║
║   ┌─────────────────────────────────────────────────────────────────┐    ║
║   │                       TOOL LAYER                                │    ║
║   │                                                                 │    ║
║   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │    ║
║   │   │   Memory    │  │   Custom    │  │    External         │    │    ║
║   │   │   Search    │  │   Tools     │  │    APIs             │    │    ║
║   │   └─────────────┘  └─────────────┘  └─────────────────────┘    │    ║
║   │                                                                 │    ║
║   └─────────────────────────────────────────────────────────────────┘    ║
║                                    │                                      ║
║                                    ▼                                      ║
║   ┌─────────────────────────────────────────────────────────────────┐    ║
║   │                      DATA LAYER                                 │    ║
║   │                                                                 │    ║
║   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │    ║
║   │   │  Firestore  │  │   Vector    │  │    Cloud            │    │    ║
║   │   │  (Sessions) │  │   Store     │  │    Storage          │    │    ║
║   │   └─────────────┘  └─────────────┘  └─────────────────────┘    │    ║
║   │                                                                 │    ║
║   └─────────────────────────────────────────────────────────────────┘    ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Component Details

### 1. Client Layer

#### Web Application
- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS with cyberpunk aesthetics
- **State**: React Query for server state
- **Auth**: Firebase Auth SDK

#### API Integration
```typescript
// Client SDK pattern
const unk = new UnkClient({
  baseUrl: 'https://api.aiwithdav3.com',
  auth: firebaseAuth
});

const response = await unk.chat({
  message: 'Analyze this architecture',
  mode: 'unk_mode'
});
```

---

### 2. API Gateway Layer

#### Cloud Run Configuration
```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: unk-agent
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "100"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
        - image: gcr.io/PROJECT/unk-agent
          resources:
            limits:
              cpu: "2"
              memory: "2Gi"
          env:
            - name: ENV
              value: production
```

#### Authentication Flow
```
1. Client includes Firebase ID token in Authorization header
2. Gateway validates token against Firebase Auth
3. Extract user claims (uid, plan, roles)
4. Attach user context to request
5. Forward to appropriate handler
```

---

### 3. Orchestration Layer

#### Intent Classification
```python
class IntentClassifier:
    """Lightweight classifier using Flash tier."""
    
    COMPLEXITY_MARKERS = {
        "trivial": ["hello", "hi", "thanks"],
        "simple": ["what is", "define", "list"],
        "moderate": ["explain", "compare", "analyze"],
        "complex": ["design", "architect", "debug"],
        "extreme": ["research", "synthesize", "comprehensive"]
    }
    
    async def classify(self, input: str) -> IntentClassification:
        # Use regex for obvious cases (save API costs)
        for complexity, markers in self.COMPLEXITY_MARKERS.items():
            if any(m in input.lower() for m in markers):
                return IntentClassification(
                    complexity=complexity,
                    recommended_mode=self._map_to_mode(complexity)
                )
        
        # Fall back to LLM classification
        return await self._llm_classify(input)
```

#### Routing Engine
```python
class RoutingEngine:
    """Routes requests to appropriate cognitive tier."""
    
    def route(
        self,
        intent: IntentClassification,
        user: UserContext
    ) -> str:
        """Determine the optimal mode for this request."""
        
        recommended = intent.recommended_mode
        
        # Subscription gating
        if self._requires_subscription(recommended):
            if user.plan not in ["pro", "enterprise"]:
                return self._downgrade_mode(recommended)
        
        # Rate limit awareness
        if self._near_rate_limit(recommended):
            return self._downgrade_mode(recommended)
        
        return recommended
```

#### Session Manager
```python
class SessionManager:
    """Manages conversation sessions in Firestore."""
    
    async def get_or_create(self, session_id: str) -> Session:
        """Retrieve existing session or create new one."""
        
        doc = await self.db.collection("sessions").document(session_id).get()
        
        if doc.exists:
            return Session.from_dict(doc.to_dict())
        
        session = Session(
            id=session_id,
            created_at=datetime.utcnow(),
            history=[]
        )
        
        await self._save(session)
        return session
```

---

### 4. Cognitive Engine Layer

#### Model Selection Matrix

| Complexity | Free Tier | Pro Tier | Enterprise |
|------------|-----------|----------|------------|
| Trivial | cost_saver | cost_saver | cost_saver |
| Simple | default | default | default |
| Moderate | flash_thinking | flash_thinking | flash_thinking |
| Complex | flash_thinking | unk_mode | unk_mode |
| Extreme | flash_thinking | unk_mode | ultrathink |

#### Agent Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                       AGENT LIFECYCLE                           │
│                                                                 │
│  1. INITIALIZATION                                              │
│     └── Load model spec                                         │
│     └── Configure system prompt                                 │
│     └── Register tools                                          │
│     └── Initialize GenAI client                                 │
│                                                                 │
│  2. SESSION START                                               │
│     └── Load conversation history                               │
│     └── Create chat session                                     │
│     └── Configure generation parameters                         │
│                                                                 │
│  3. TURN EXECUTION                                              │
│     └── Receive user input                                      │
│     └── Generate response (with tool calls)                     │
│     └── Track token usage                                       │
│     └── Return structured output                                │
│                                                                 │
│  4. SESSION END                                                 │
│     └── Save conversation history                               │
│     └── Update usage statistics                                 │
│     └── Release resources                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 5. Tool Layer

#### Built-in Tools

| Tool | Purpose | Tier Required |
|------|---------|---------------|
| `search_knowledge_base` | Vector memory search | Any |
| `store_information` | Save to memory | Any |
| `calculate_growth_metrics` | SaaS metrics | Any |
| `get_current_timestamp` | Time utilities | Any |

#### Tool Registration Pattern

```python
class ToolRegistry:
    """Central registry for agent tools."""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
    
    def register(
        self,
        func: Callable,
        required_tier: str = "any",
        rate_limited: bool = False
    ):
        """Register a tool with metadata."""
        self._tools[func.__name__] = func
        self._metadata[func.__name__] = ToolMetadata(
            name=func.__name__,
            docstring=func.__doc__,
            required_tier=required_tier,
            rate_limited=rate_limited
        )
    
    def get_tools_for_tier(self, tier: str) -> List[Callable]:
        """Get all tools available for a tier."""
        return [
            t for name, t in self._tools.items()
            if self._metadata[name].is_available_for(tier)
        ]
```

---

### 6. Data Layer

#### Firestore Schema

```
unk_agent (database)
├── sessions (collection)
│   └── {session_id} (document)
│       ├── user_id: string
│       ├── created_at: timestamp
│       ├── updated_at: timestamp
│       ├── history: array
│       │   └── {message}
│       │       ├── role: "user" | "assistant"
│       │       ├── content: string
│       │       └── timestamp: timestamp
│       └── metadata: map
│
├── unk_memory (collection) [Vector-enabled]
│   └── {memory_id} (document)
│       ├── content: string
│       ├── embedding: vector(768)
│       ├── memory_type: string
│       ├── user_id: string
│       ├── metadata: map
│       └── created_at: timestamp
│
├── usage (collection)
│   └── {user_id} (document)
│       ├── period: string
│       ├── requests: number
│       ├── tokens_input: number
│       ├── tokens_output: number
│       └── estimated_cost: number
│
└── users (collection)
    └── {user_id} (document)
        ├── email: string
        ├── plan: string
        ├── created_at: timestamp
        └── settings: map
```

#### Vector Index

```bash
gcloud firestore indexes composite create \
  --collection-group=unk_memory \
  --query-scope=COLLECTION \
  --field-config field-path=embedding,vector-config='{"dimension":"768","flat":"{}"}' \
  --field-config field-path=user_id,order=ASCENDING \
  --field-config field-path=memory_type,order=ASCENDING
```

---

## Data Flow Diagrams

### Standard Request Flow

```
┌──────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐     ┌─────────┐
│Client│────▶│Cloud Run │────▶│ Router  │────▶│  Agent   │────▶│ Gemini  │
└──────┘     └──────────┘     └─────────┘     └──────────┘     └─────────┘
    │                              │                │               │
    │         1. Request           │                │               │
    │────────────────────────────▶│                │               │
    │                              │  2. Classify   │               │
    │                              │───────────────▶│               │
    │                              │                │  3. Generate  │
    │                              │                │──────────────▶│
    │                              │                │  4. Response  │
    │                              │                │◀──────────────│
    │         5. Final             │                │               │
    │◀────────────────────────────│◀───────────────│               │
```

### Tool Execution Flow

```
┌──────────┐     ┌─────────┐     ┌──────────┐     ┌──────────┐
│  Agent   │────▶│ Gemini  │────▶│   Tool   │────▶│ Firestore│
└──────────┘     └─────────┘     └──────────┘     └──────────┘
     │               │                │                 │
     │  1. Prompt    │                │                 │
     │──────────────▶│                │                 │
     │               │  2. Tool Call  │                 │
     │               │───────────────▶│                 │
     │               │                │   3. Query      │
     │               │                │────────────────▶│
     │               │                │   4. Results    │
     │               │                │◀────────────────│
     │               │  5. Tool Result│                 │
     │               │◀───────────────│                 │
     │  6. Response  │                │                 │
     │◀──────────────│                │                 │
```

---

## Security Architecture

### Authentication

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                              │
│                                                                 │
│  1. TRANSPORT SECURITY                                          │
│     └── TLS 1.3 for all connections                            │
│     └── Certificate pinning for mobile                          │
│                                                                 │
│  2. AUTHENTICATION                                              │
│     └── Firebase Auth (OIDC)                                    │
│     └── JWT validation                                          │
│     └── Token refresh handling                                  │
│                                                                 │
│  3. AUTHORIZATION                                               │
│     └── Subscription-based feature gating                       │
│     └── Per-user rate limiting                                  │
│     └── Resource-level access control                           │
│                                                                 │
│  4. DATA PROTECTION                                             │
│     └── User data isolation in Firestore                        │
│     └── Encryption at rest (default GCP)                        │
│     └── PII filtering in logs                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### IAM Roles

| Service Account | Purpose | Roles |
|-----------------|---------|-------|
| unk-agent-sa | Cloud Run service | Vertex AI User, Firestore User |
| unk-memory-sa | Vector operations | Firestore Admin |
| unk-deploy-sa | CI/CD deployments | Cloud Build Editor, Cloud Run Admin |

---

## Scalability Considerations

### Horizontal Scaling

Cloud Run automatically scales based on:
- Concurrent requests
- CPU utilization
- Memory pressure

```yaml
autoscaling.knative.dev/minScale: "0"   # Scale to zero
autoscaling.knative.dev/maxScale: "100" # Max instances
containerConcurrency: 80                 # Requests per instance
```

### Bottleneck Mitigation

| Bottleneck | Solution |
|------------|----------|
| Gemini rate limits | Tier-based routing, request queuing |
| Firestore writes | Batch operations, caching |
| Cold starts | Minimum instances, smaller container |
| Memory pressure | Streaming responses, pagination |

---

## Monitoring & Observability

### Key Metrics

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| Request latency | Cloud Run | P99 > 10s |
| Error rate | Cloud Run | > 5% |
| Token usage | Application | > budget |
| Cost per request | Application | > threshold |

### Logging Strategy

```python
# Structured logging format
log_entry = {
    "severity": "INFO",
    "message": "Request processed",
    "request_id": request_id,
    "user_id": user.uid,
    "mode": mode,
    "latency_ms": latency,
    "tokens": token_count,
    "cost": estimated_cost
}
```

---

## Disaster Recovery

### Backup Strategy

| Data | Backup Frequency | Retention |
|------|------------------|-----------|
| Firestore | Daily | 30 days |
| Vector embeddings | Daily | 30 days |
| Logs | Real-time (Cloud Logging) | 90 days |

### Recovery Procedures

1. **Service Outage**: Automatic Cloud Run failover
2. **Data Corruption**: Restore from Firestore backup
3. **Region Failure**: Deploy to alternate region

---

*Who Visions LLC - AI with Dav3*
