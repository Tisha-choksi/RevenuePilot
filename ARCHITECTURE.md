# RevenuePilot — Architecture

This document expands on [`readme.md`](./readme.md) into a detailed system architecture for RevenuePilot, an enterprise-grade, multi-agent AI Sales Automation Platform.

## 1. System Overview

RevenuePilot is organized into five layers:

1. **Interface Layer** — channels through which prospects/customers and human reps interact with the system (web app, email, chat widget, CRM webhook).
2. **Orchestration Layer** — a LangGraph state machine that routes work between specialized agents and manages the sales workflow lifecycle.
3. **Agent Layer** — specialized AI agents, each owning one part of the sales process.
4. **Knowledge & Memory Layer** — RAG retrieval, customer memory, and long-term context storage.
5. **Integration & Data Layer** — tool-calling adapters to CRM, inventory, pricing, email/calendar systems, plus the underlying datastores.

```
                          ┌─────────────────────────────────────────┐
                          │              Interface Layer             │
                          │  Web App (React/Next.js) | Chat | Email  │
                          │  CRM Webhooks | Inbound Lead Forms       │
                          └───────────────────┬───────────────────-─┘
                                              │ REST / WebSocket (FastAPI)
                          ┌───────────────────▼───────────────────--┐
                          │           Orchestration Layer            │
                          │     LangGraph Workflow State Machine     │
                          │  (routing, retries, human-in-the-loop)   │
                          └───────────────────┬───────────────────-─┘
                                              │
        ┌───────────────┬──────────────┬─────┴──────┬───────────────┬───────────────┐
        ▼                ▼              ▼            ▼               ▼               ▼
 ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌─────────────┐ ┌──────────────┐ ┌────────────┐
 │   Lead Qual. │ │   Product    │ │ Pricing/ │ │ Negotiation │ │  Engagement  │ │  Analytics │
 │    Agent     │ │ Recommender  │ │ Discount │ │   /Objection│ │ & Follow-up  │ │   Agent    │
 │              │ │    Agent     │ │  Agent   │ │    Agent    │ │    Agent     │ │            │
 └──────┬──────-┘ └──────┬──────-┘ └────┬─────┘ └──────┬──────┘ └──────┬───────┘ └─────┬──────┘
        │                │              │              │               │               │
        └────────────────┴──────────────┴──────┬───────┴───────────────┴───────────────┘
                                                 ▼
                          ┌────────────────────────────────────────--─┐
                          │         Knowledge & Memory Layer          │
                          │  RAG (Qdrant/pgvector) | Customer Memory  │
                          │  Conversation History | Session State     │
                          └───────────────────┬─────────────────────-─┘
                                              │
                          ┌───────────────────▼─────────────────────-─┐
                          │         Integration & Data Layer          │
                          │ CRM API | Inventory API | Pricing Engine  │
                          │ Email/Calendar | PostgreSQL | Redis       │
                          └─────────────────────────────────────────-─┘
```

## 2. Orchestration Layer (LangGraph)

The orchestration layer is a directed graph of nodes (agents/tools) and conditional edges that encodes the sales lifecycle as a state machine rather than a fixed pipeline, so the workflow can branch, loop, or escalate based on agent output.

**Workflow state** (shared across nodes) includes:
- `lead_profile` — firmographic/demographic data, source, score
- `conversation_history` — turn-by-turn dialogue with the prospect
- `qualification_status` — `NEW | QUALIFYING | QUALIFIED | DISQUALIFIED`
- `recommended_products`, `active_quote`, `pricing_constraints`
- `objections_raised`, `negotiation_state`
- `next_action` — decided by the router node after each agent step
- `escalation_flag` — set when human-in-the-loop is required

**Routing logic** (simplified):

```
START → Lead Qualification Agent
  ├─ disqualified → Analytics Agent (log) → END
  └─ qualified → Product Recommendation Agent
        → Pricing Agent
        → Engagement Agent (presents quote/proposal)
              ├─ objection raised → Negotiation Agent → Engagement Agent (loop)
              ├─ needs human approval → Human-in-the-Loop Escalation → resume
              ├─ accepted → CRM Update (Deal Won) → Analytics Agent → END
              └─ no response (timeout) → Follow-up Scheduler → Engagement Agent (loop, bounded retries)
```

Each node is implemented as a LangGraph node wrapping an LLM-driven agent with tool access; conditional edges are implemented as router functions that inspect workflow state.

## 3. Agent Layer

| Agent | Responsibility | Primary Tools |
|---|---|---|
| **Lead Qualification Agent** | Scores and qualifies inbound/outbound leads using firmographic data + conversational signals (BANT/MEDDIC-style scoring) | CRM read, lead enrichment APIs |
| **Product Recommendation Agent** | Matches customer requirements to product/service catalog via RAG over product docs | Vector search (RAG), product catalog API |
| **Pricing & Discount Agent** | Computes quotes, applies discount policy, enforces margin/approval thresholds | Pricing engine API, policy rules |
| **Negotiation / Objection-Handling Agent** | Detects and responds to objections (price, timing, competitor, fit) using persuasion strategies and fallback offers | Knowledge base RAG, pricing agent (re-quote) |
| **Engagement & Follow-up Agent** | Drives outreach cadence, schedules calls/demos, sends proposals, manages timeouts/reminders | Email API, calendar API, scheduler |
| **Sales Analytics Agent** | Aggregates funnel metrics, win/loss reasons, agent performance, and feeds dashboards | PostgreSQL analytics views, CRM write |

All agents share a common **Agent Runtime** abstraction: LLM client (OpenAI-compatible or local via Ollama) + tool-calling interface + access to the Knowledge & Memory layer + structured output parsing into the shared workflow state.

## 4. Knowledge & Memory Layer

- **RAG (Retrieval-Augmented Generation)**: Product specs, pricing policy documents, sales playbooks, and objection-handling scripts are chunked, embedded, and indexed in **Qdrant** (or **pgvector** for a simpler single-database deployment). Agents retrieve top-k relevant chunks before generating responses to ground outputs in factual product/policy data.
- **Customer Memory**: Per-lead/account long-term memory (past interactions, preferences, prior objections, deal history) persisted in PostgreSQL and surfaced to agents at the start of each session, enabling context continuity across multi-session sales cycles.
- **Session/Working Memory**: Short-lived conversational state held in Redis for low-latency access during an active session, including in-flight workflow state and rate-limited follow-up counters.

## 5. Integration & Data Layer

- **CRM Integration**: Bi-directional sync (e.g., Salesforce/HubSpot-style API) — reads existing deal/contact records, writes qualification status, quotes, and deal stage transitions in real time.
- **Inventory/Product API**: Source of truth for product availability and specs, queried by the Recommendation Agent.
- **Pricing Engine**: External or internal service enforcing pricing rules, discount tiers, and approval thresholds.
- **Email/Calendar Tools**: Used by the Engagement Agent for outreach and scheduling (e.g., SMTP/Graph API/Calendar API adapters).
- **PostgreSQL**: System of record for leads, accounts, quotes, deals, and analytics aggregates.
- **Redis**: Caching, session state, task queues (e.g., scheduled follow-ups), and rate limiting.
- **Qdrant/pgvector**: Vector store for RAG embeddings.

## 6. API & Backend (FastAPI)

FastAPI exposes:
- `POST /leads` — ingest new leads (forms, webhooks)
- `POST /workflows/{lead_id}/advance` — trigger/resume a LangGraph workflow run
- `GET /workflows/{lead_id}/state` — inspect current workflow state (for dashboards/HITL UI)
- `POST /workflows/{lead_id}/escalations/{id}/resolve` — human approval/override endpoint
- `GET /analytics/*` — dashboard data endpoints
- WebSocket channel for real-time conversation streaming to the frontend chat UI

Background workers (e.g., Celery/RQ on Redis, or async tasks) handle scheduled follow-ups and long-running workflow steps so HTTP requests stay non-blocking.

## 7. Human-in-the-Loop Escalation

Certain conditions force a pause and route to a human rep via the dashboard:
- Discount/pricing exceeds policy threshold
- High-value deal or VIP account
- Repeated unresolved objections
- Agent confidence below threshold on a critical decision

Escalations are persisted as records with full workflow context; once a human resolves them (approve/edit/reject) via the dashboard, the workflow resumes from the paused node.

## 8. Frontend (React/Next.js)

- **Sales Dashboard**: Pipeline view, lead scores, deal stages, analytics charts.
- **Conversation Console**: Live view of agent-customer conversations with intervention controls.
- **Escalation Queue**: Human-in-the-loop approval UI.
- **Configuration UI**: Pricing policy, product catalog, and playbook management.

## 9. Observability

- **LangSmith** — traces every agent/LLM call, tool invocation, and LangGraph state transition for debugging and quality evaluation.
- **OpenTelemetry** — distributed tracing/metrics/logs across FastAPI, background workers, and datastore calls, exported to a standard backend (e.g., Prometheus/Grafana, Jaeger).
- Key metrics: lead-to-qualified conversion rate, agent response latency, escalation rate, quote-to-close rate, RAG retrieval relevance.

## 10. Deployment Architecture

- **Docker Compose** (dev) / container orchestration (prod) with services: `api` (FastAPI), `worker` (background tasks), `postgres`, `redis`, `qdrant`, `frontend`.
- LLM inference via **Ollama** (self-hosted/local models) or any **OpenAI-compatible** endpoint, selected via config — allowing on-prem/data-residency-sensitive deployments to swap providers without code changes.
- Stateless API/worker containers scale horizontally; PostgreSQL/Redis/Qdrant scale independently behind the data layer.

## 11. Tech Stack Mapping

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph / LangChain |
| Backend API | FastAPI |
| Relational data | PostgreSQL |
| Cache / queue / session state | Redis |
| Vector store | Qdrant or pgvector |
| LLM inference | Ollama / OpenAI-compatible models |
| Frontend | React / Next.js |
| Observability | LangSmith / OpenTelemetry |
| Containerization | Docker |
