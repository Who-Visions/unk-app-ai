# ROADMAP.md

## Unk Agent Development Roadmap

Strategic implementation plan from prototype to enterprise SaaS.

---

## Overview

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                          DEVELOPMENT PHASES                               ║
║                                                                           ║
║   PHASE 1          PHASE 2          PHASE 3          PHASE 4             ║
║   Foundation       Production       Scale            Enterprise          ║
║   ━━━━━━━━━        ━━━━━━━━━━       ━━━━━             ━━━━━━━━━━          ║
║   Week 1-2         Week 3-4         Week 5-8         Week 9-12           ║
║                                                                           ║
║   • Core Agent     • Auth/OIDC      • Multi-tenant   • Advanced RAG      ║
║   • Models Spec    • Rate Limits    • Usage Billing  • Custom Tools      ║
║   • Basic Deploy   • Cloud Run      • Monitoring     • White-label       ║
║   • Memory MVP     • Vector Index   • Cost Optimize  • SLA Dashboard     ║
║                                                                           ║
║   $100 credits     $300 credits     $400 credits     $200 credits        ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Phase 1: Foundation (Week 1-2)

### Objectives
- Core agent implementation
- GEMINI_MODELS specification
- Basic deployment infrastructure
- Memory system MVP

### Milestones

#### M1.1: Core Agent (Day 1-3)
- [x] `models_spec.py` - Cognitive tier definitions
- [x] `agent.py` - UnkAgent class implementation
- [x] Async execution with google-genai SDK
- [x] Structured output with Pydantic
- [x] Basic tool registration

**Deliverable**: Working agent that routes between Flash/Pro/Ultra

#### M1.2: Memory System (Day 4-5)
- [x] `memory.py` - VectorMemory class
- [x] Firestore integration
- [x] Embedding generation
- [x] Semantic search (cosine similarity)
- [ ] Memory tool integration

**Deliverable**: RAG-enabled agent with persistent memory

#### M1.3: Basic Deployment (Day 6-7)
- [x] `deploy.py` - FastAPI server
- [x] CORS configuration
- [x] Health endpoints
- [x] Basic request/response models
- [ ] Local Docker testing

**Deliverable**: Locally runnable API server

#### M1.4: Documentation (Day 8-10)
- [x] README.md
- [x] ARCHITECTURE.md
- [x] GEMINI.md
- [x] CLAUDE.md
- [x] ROADMAP.md

**Deliverable**: Comprehensive documentation suite

### Phase 1 Budget: ~$100
- Development testing: $50
- Documentation validation: $25
- Buffer: $25

---

## Phase 2: Production (Week 3-4)

### Objectives
- Full authentication system
- Rate limiting and throttling
- Cloud Run deployment
- Vector index optimization

### Milestones

#### M2.1: Authentication (Day 1-3)
- [ ] Firebase Admin SDK integration
- [ ] JWT validation middleware
- [ ] Subscription tier extraction
- [ ] User context propagation
- [ ] Dev token bypass for testing

**Deliverable**: Secure OIDC authentication

#### M2.2: Rate Limiting (Day 4-5)
- [ ] Per-user rate limits
- [ ] Per-tier rate limits
- [ ] Redis-based counter (optional)
- [ ] Graceful degradation
- [ ] Rate limit headers

**Deliverable**: Fair usage enforcement

#### M2.3: Cloud Run Deployment (Day 6-8)
- [ ] Dockerfile optimization
- [ ] Cloud Build configuration
- [ ] Service account setup
- [ ] Environment configuration
- [ ] Custom domain mapping

**Deliverable**: Production deployment at api.aiwithdav3.com

#### M2.4: Vector Optimization (Day 9-10)
- [ ] Composite index creation
- [ ] Query performance testing
- [ ] Embedding batch operations
- [ ] Memory pruning strategy

**Deliverable**: Optimized vector search (<100ms)

### Phase 2 Budget: ~$300
- Cloud Run hosting: $100
- Vertex AI testing: $150
- Firestore operations: $50

---

## Phase 3: Scale (Week 5-8)

### Objectives
- Multi-tenant architecture
- Usage tracking and billing
- Comprehensive monitoring
- Cost optimization

### Milestones

#### M3.1: Multi-Tenancy (Week 5)
- [ ] Tenant isolation in Firestore
- [ ] Per-tenant configuration
- [ ] Admin API endpoints
- [ ] Tenant onboarding flow

**Deliverable**: Support for multiple organizations

#### M3.2: Usage & Billing (Week 6)
- [ ] Token counting per request
- [ ] Cost attribution
- [ ] Usage aggregation
- [ ] Stripe integration
- [ ] Invoice generation

**Deliverable**: Automated billing system

#### M3.3: Monitoring (Week 7)
- [ ] Cloud Monitoring dashboards
- [ ] Custom metrics
- [ ] Alerting policies
- [ ] Error tracking (Sentry)
- [ ] Cost alerts

**Deliverable**: Full observability

#### M3.4: Cost Optimization (Week 8)
- [ ] Context caching implementation
- [ ] Request batching
- [ ] Prompt compression
- [ ] Tier downgrade policies
- [ ] Budget enforcement

**Deliverable**: 30% cost reduction

### Phase 3 Budget: ~$400
- Production workloads: $200
- Multi-tenant testing: $100
- Monitoring setup: $50
- Optimization testing: $50

---

## Phase 4: Enterprise (Week 9-12)

### Objectives
- Advanced RAG capabilities
- Custom tool framework
- White-label support
- SLA dashboard

### Milestones

#### M4.1: Advanced RAG (Week 9)
- [ ] Hybrid search (vector + keyword)
- [ ] Document chunking strategies
- [ ] Citation generation
- [ ] Source attribution
- [ ] Memory importance ranking

**Deliverable**: Enterprise-grade RAG

#### M4.2: Custom Tool Framework (Week 10)
- [ ] Tool definition DSL
- [ ] Runtime tool registration
- [ ] Tool marketplace
- [ ] Sandboxed execution
- [ ] Tool analytics

**Deliverable**: Extensible tool ecosystem

#### M4.3: White-Label (Week 11)
- [ ] Custom branding support
- [ ] Tenant-specific system prompts
- [ ] Custom domains
- [ ] Embedded widget
- [ ] API key management

**Deliverable**: White-label ready platform

#### M4.4: SLA Dashboard (Week 12)
- [ ] Uptime monitoring
- [ ] Performance metrics
- [ ] SLA compliance tracking
- [ ] Customer-facing status page
- [ ] Incident management

**Deliverable**: Enterprise SLA support

### Phase 4 Budget: ~$200
- Enterprise testing: $100
- Performance optimization: $50
- Buffer: $50

---

## Stacked Diff Strategy

### Branch Structure

```
main
 └── develop
      ├── feature/phase1-core-agent      ✓ Merged
      ├── feature/phase1-memory          ✓ Merged
      ├── feature/phase1-deploy          ✓ Merged
      ├── feature/phase2-auth            → In Progress
      ├── feature/phase2-rate-limits     → Queued
      ├── feature/phase2-cloud-run       → Queued
      └── ...
```

### Commit Convention

```
<type>(<scope>): <description>

Types: feat, fix, docs, refactor, test, chore
Scopes: agent, memory, deploy, auth, tools

Examples:
- feat(agent): implement cognitive tier routing
- fix(memory): handle empty search results
- docs(architecture): add data flow diagrams
- refactor(deploy): extract auth middleware
```

### Pull Request Flow

```
1. Create feature branch from develop
2. Implement feature with atomic commits
3. Open PR with:
   - Description of changes
   - Testing notes
   - Related issues
4. Self-review code
5. Merge to develop
6. Delete feature branch
```

---

## Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Gemini rate limits | High | Medium | Tier-based routing, queuing |
| Vector search latency | Medium | High | Index optimization, caching |
| Cold start times | Medium | Medium | Min instances, container optimization |
| Token cost overrun | Medium | High | Budget alerts, hard limits |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Credit exhaustion | Low | Critical | Daily monitoring, staged rollout |
| Model deprecation | Medium | Medium | Abstraction layer, spec updates |
| Feature scope creep | High | Medium | Strict phase boundaries |

---

## Success Metrics

### Phase 1
- [ ] Agent responds correctly to multi-tier routing
- [ ] Memory search returns relevant results
- [ ] API handles 10 concurrent requests

### Phase 2
- [ ] Authentication blocks invalid tokens
- [ ] Rate limits trigger at thresholds
- [ ] Cloud Run deploys successfully
- [ ] P95 latency < 5 seconds

### Phase 3
- [ ] 10+ tenants onboarded
- [ ] Billing generates accurate invoices
- [ ] Alerts fire within 5 minutes
- [ ] Cost per request reduced 30%

### Phase 4
- [ ] RAG citations are accurate
- [ ] Custom tools execute safely
- [ ] White-label tenant operational
- [ ] 99.9% uptime achieved

---

## Resource Allocation

### $1,000 GCP Credit Distribution

```
┌─────────────────────────────────────────────────────────────────┐
│                    CREDIT ALLOCATION                            │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Phase 1: Foundation          $100  ████░░░░░░░░░░░░░░░░ │   │
│   └─────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Phase 2: Production          $300  ████████████░░░░░░░░ │   │
│   └─────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Phase 3: Scale               $400  ████████████████░░░░ │   │
│   └─────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Phase 4: Enterprise          $200  ████████░░░░░░░░░░░░ │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Total: $1,000                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Time Allocation

- Development: 60%
- Testing: 20%
- Documentation: 10%
- Buffer: 10%

---

## Dependencies

### External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| google-genai | >=0.6.0 | Gemini SDK |
| FastAPI | >=0.115.0 | API framework |
| firebase-admin | >=6.5.0 | Authentication |
| google-cloud-firestore | >=2.19.0 | Data persistence |

### Internal Dependencies

| Module | Depends On |
|--------|------------|
| agent.py | models_spec.py |
| memory.py | models_spec.py (embeddings) |
| deploy.py | agent.py, memory.py |

---

## Next Actions

### Immediate (This Week)
1. Complete Phase 1 documentation
2. Test agent locally
3. Create Firestore indexes
4. Begin Phase 2 auth work

### Short-term (Next 2 Weeks)
1. Complete Phase 2 deployment
2. Validate production API
3. Begin user testing
4. Start Phase 3 planning

### Medium-term (Month 2-3)
1. Complete Phase 3 scale
2. Launch beta
3. Gather feedback
4. Iterate on features

---

*Who Visions LLC - AI with Dav3*
*Last Updated: December 2025*
