# Project Charter: AI Assistant with Persistent Memory

**Version:** 1.0.0  
**Date:** 2026-04-20  
**Status:** Approved — Foundation Document  
**Author:** Sebastian

---

## Question 1 — What exactly am I going to build?

A production-grade, containerized AI assistant system where a LangGraph `StateGraph` agent orchestrates a set of deterministic tools (web search, calculator, RAG retriever) with a three-layer memory architecture that persists conversation context across sessions, container restarts, and time — not just within a single chat window.

The system is exposed via a versioned FastAPI microservice (`/v1/chat`, `/v1/health`), deployed through a hardened multi-stage Docker Compose stack, and validated by a GitHub Actions CI/CD pipeline that enforces static type checking, ≥70% test coverage, and a container vulnerability scan before any merge to `main`.

---

## Question 2 — Who is it intended for?

**Primary audience (portfolio consumers):**
- Senior ML Engineers and AI Architects reviewing portfolio projects at elite companies
- Technical VPs and Engineering Managers assessing system-design maturity
- Hiring panels running take-home reviews or technical screen debriefs

**Secondary audience (technical users):**
- Developers who want to explore a working reference implementation of a LangGraph agentic system with real persistent memory — not a tutorial demo, but a production-structured codebase.

**The implicit audience the project must satisfy:**
The project must be self-evidently more sophisticated than 95% of "AI chatbot" portfolio projects. It does this not through complexity for its own sake, but through *disciplined engineering*, which is the kind a staff-level engineer silently checks against their mental rubric during a code review.

---

## Question 3 — What problem does the product solve?

### Surface Problem
A user wants an AI assistant that actually *remembers* them, their preferences, past questions, and ongoing context across multiple days and sessions, without having to re-introduce themselves every time they open the app.

### Real Engineering Problem
**Stateful agentic systems are architecturally hard to get right.** Most "AI with memory" implementations fail in at least one of three ways:

1. **Memory is fake.** `ConversationBufferMemory` stores messages in RAM. One restart, one container redeploy, one API timeout and every user preference is gone. The "memory" label is a lie.

2. **The agent is not an agent.** Calling an LLM API in a loop and showing the response is not agency. A real agent must reason about *when* to call tools, *which* tool to call, and *how* to synthesize their outputs — then store that synthesis durably.

3. **The LLM does everything, including math.** Asking an LLM to calculate, aggregate, or transform data is asking a probabilistic system to do deterministic work. The result is intermittently wrong in silent, hard-to-catch ways. This is the hallucination problem, and it is an *architectural* failure, not a model quality failure.

This project solves all three by implementing:
- A **three-layer memory system** (in-session state + SQLite sessions + ChromaDB semantic store)
- A **LangGraph StateGraph** agent with native tool-calling, HITL interrupt support, and node-level checkpointing
- A **Brain/Brawn separation**: the LLM reasons and routes; deterministic Python tools calculate and fetch

---

## Question 4 — How is it going to work?

```
User types message
       ↓
Streamlit UI (thin client — no business logic)
       ↓ POST /v1/chat {message, thread_id, use_cloud}
FastAPI Agent Service (/v1/chat)
       ↓ graph.invoke(state, config={thread_id})
LangGraph StateGraph Agent
   ├─ LOAD checkpoint from SQLite (restore prior session)
   ├─ PRELOAD semantic memory (ChromaDB: top-3 user facts)
   ├─ agent_node: LLM reasons over [system_prompt + history + memory + message]
   │    └─ emits tool_calls if needed, or final answer
   ├─ conditional edge: tool_calls? → tool_node : → END
   ├─ tool_node: dispatches to WebSearch / Calculator / RAGRetriever
   ├─ loops back to agent_node with tool results
   └─ SAVE checkpoint to SQLite (persist updated state)
       ↓
FastAPI returns ChatResponse {reply, thread_id, tokens_used, latency_ms}
       ↓
Streamlit renders response
```

Two LLM backends (local Docker Model Runner + OpenRouter cloud API) are available and switchable per request via the `use_cloud` flag in the request body.

---

## Question 5 — What is the expected result (technically)?

| Deliverable | Acceptance Criterion |
|-------------|---------------------|
| LangGraph agent with 3 tools | Agent correctly invokes tools; tool results appear in final response |
| Three-layer memory | Conversation context survives: (a) multi-turn, (b) container restart, (c) brand-new session via semantic recall |
| FastAPI microservice | `POST /v1/chat` and `GET /v1/health` return correct Pydantic-typed responses |
| Streamlit UI | UI sends and receives typed JSON; no business logic in `gui.py` |
| Multi-stage Dockerfile | Image builds without root user; `trivy scan` returns zero HIGH/CRITICAL CVEs |
| GitHub Actions pipeline | CI passes: ruff ✅ · pyright ✅ · pytest ≥70% coverage ✅ · trivy scan ✅ |
| Type safety | `pyright --mode standard` reports zero errors across `src/` |
| Test suite | Unit tests for all tools; integration test for `/v1/chat`; smoke test for `/v1/health` |
| Documentation | ADR-001, system design diagram, this charter, PRD, user story, and roadmap committed |

---

## Question 6 — What steps do I need to take?

### Phase 0 — Planning & Documentation *(current phase)*
- [x] ADR-001: LangGraph vs LangChain decision
- [x] System design architecture diagrams
- [x] Project charter (this document)
- [x] PRD
- [x] User story
- [x] Technical roadmap

### Phase 1 — Foundation Hardening
- Refactor flat `app.py` → project skeleton (`src/agents/`, `src/api/`, `src/tools/`, etc.)
- Wire full `pyproject.toml` (ruff, pyright, pytest, coverage)
- Add `.env.example`, `src/py.typed`, `.pre-commit-config.yaml`
- Harden Dockerfile: multi-stage, non-root user, optimized layer cache
- Implement `ConfigurationManager`, `config/prompts.yaml`, `config/config.yaml`
- Implement `src/utils/logger.py` and `src/utils/exceptions.py`
- Implement Pydantic schemas in `src/entity/schemas.py`

### Phase 2 — Agentic Upgrade
- Build LangGraph `StateGraph` agent (`src/agents/graph.py`)
- Implement three deterministic tools with Pydantic input schemas
- Implement three-layer memory system (AgentState + SqliteSaver + ChromaDB)
- Add versioned system prompt loading from `config/prompts.yaml`

### Phase 3 — Production Engineering
- Build FastAPI service (`src/api/`) with `/v1/chat` and `/v1/health`
- Decouple Streamlit UI to thin HTTP client
- Update `docker-compose.yaml` with db + vector service containers
- Implement structured logging (loguru/structlog) + OpenTelemetry spans
- Write unit tests for all tools + integration tests for API

### Phase 4 — CI/CD & Final Polish
- GitHub Actions: quality-gate → test → docker-build/scan
- `validate_system.bat` multi-point gate script
- README upgrade with architecture diagram, demo GIF, CI badge, quick-start
- Final documentation sync across `reports/docs/`

---

## Question 7 — What could go wrong?

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| LLM API timeouts (OpenRouter) | Medium | Medium | `timeout=30` + retry with exponential backoff in tool layer; local model as fallback |
| LangGraph infinite loop (misconfigured conditional edge) | Medium | High | `recursion_limit=10` in graph config; explicit `max_iterations` guard in agent node |
| ChromaDB embedding drift (model changes between versions) | Low | Medium | Pin embedding model name in `params.yaml`; version-lock in `pyproject.toml` |
| SQLite WAL corruption under concurrent writes | Low | High | Single-writer constraint in `docker-compose.yaml`; migrate to PostgreSQL for multi-user |
| Pyright false positives on LangGraph's `TypedDict` state | Medium | Low | Targeted `# type: ignore` with comments; `typeCheckingMode = "standard"` (not strict) |
| Docker networking failure (app→llm service) | Medium | High | `depends_on: { condition: service_healthy }` + health check retry |
| Prompt injection via user input | Medium | High | Input sanitization in FastAPI request handler; output guardrail in agent node |
| Test coverage target too low to catch real bugs | Low | Medium | Prioritize tool unit tests (deterministic) + API integration tests |
| Scope creep (adding Kubernetes, Celery, fine-tuning, etc.) | High | Medium | Hard freeze: only implement what the ADR and roadmap authorize |

---

## Question 8 — What tools should I use?

### Core Stack

| Category | Tool | Reason |
|----------|------|--------|
| Agent orchestration | `langgraph` | StateGraph, HITL, checkpointing — see ADR-001 |
| LLM client | `langchain-openai` | OpenAI-compatible interface for both local + cloud models |
| API layer | `fastapi` + `uvicorn` | Typed Pydantic endpoints, async, auto OpenAPI docs |
| UI layer | `streamlit` | Thin chat client only; no logic lives here |
| Memory L2 | `langgraph[sqlite]` (SqliteSaver) | Zero-config local persistence |
| Memory L3 | `chromadb` | Embeddable, Docker-friendly, semantic search |
| Embeddings | `langchain-openai` (text-embedding-3-small) | Consistent with LLM client |

### Engineering Toolchain

| Category | Tool | Reason |
|----------|------|--------|
| Dependency management | `uv` | Lightning-fast resolution, lockfile integrity |
| Linting + formatting | `ruff` | Fast, import sorting, f-string enforcement |
| Type checking | `pyright` (standard mode) | Superior Pydantic v2 inference over mypy |
| Testing | `pytest` + `pytest-cov` | Unit + integration tests, coverage gate |
| Logging | `loguru` | Structured, JSON-compatible, zero-config |
| Containerization | `docker` + `docker-compose` | Multi-stage build, service orchestration |
| CI/CD | GitHub Actions | Three-stage pipeline with secrets management |
| Pre-commit | `.pre-commit-config.yaml` | ruff + pyright gates before every commit |
| Environment | `.env` + `python-dotenv` | API keys isolated from source code |

---

## Question 9 — What are the main concepts and how are they related?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CORE CONCEPT MAP                                       │
│                                                                               │
│  Brain/Brawn Separation                                                       │
│  ┌──────────────────────┐         ┌──────────────────────────┐               │
│  │   BRAIN (LLM)        │         │   BRAWN (Tools)          │               │
│  │   - Reason           │ ──────► │   - WebSearchTool        │               │
│  │   - Route            │         │   - CalculatorTool       │               │
│  │   - Synthesize       │ ◄────── │   - RAGRetriever         │               │
│  └──────────────────────┘         └──────────────────────────┘               │
│             │                                   │                             │
│             │ orchestrated by                   │ deterministic               │
│             ▼                                   ▼                             │
│  LangGraph StateGraph              Pydantic BaseModel I/O                    │
│  ┌──────────────────────┐         ┌──────────────────────────┐               │
│  │  AgentState TypedDict│         │  Input schema validation  │               │
│  │  → messages          │         │  Output type enforcement  │               │
│  │  → user_facts        │         │  Google-style docstrings  │               │
│  │  → thread_id         │         │  (agent reads these)      │               │
│  └──────────────────────┘         └──────────────────────────┘               │
│             │                                                                 │
│             │ persisted by                                                    │
│             ▼                                                                 │
│  Three-Layer Memory                                                           │
│  ┌─────────┐ ┌────────────────┐ ┌──────────────────────────┐                │
│  │ Layer 1 │ │   Layer 2      │ │         Layer 3           │                │
│  │ In-     │ │   SQLite       │ │         ChromaDB          │                │
│  │ Session │ │   Checkpointer │ │         Semantic Store    │                │
│  │ RAM     │ │   (thread_id)  │ │         (cosine search)   │                │
│  └─────────┘ └────────────────┘ └──────────────────────────┘                │
│                                                                               │
│             │ exposed by                                                      │
│             ▼                                                                 │
│  FastAPI Microservice              Streamlit (thin client)                   │
│  POST /v1/chat     ◄────────────── HTTP POST with ChatRequest               │
│  GET  /v1/health                   HTTP GET for health probe                │
│                                                                               │
│             │ deployed via                                                    │
│             ▼                                                                 │
│  Docker Compose                    GitHub Actions CI/CD                      │
│  multi-stage Dockerfile  ◄──────── quality → test → build/scan              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**How the concepts chain together:**
The **Brain/Brawn Separation** is the governing principle. It dictates that the **LangGraph agent** (Brain) must only reason and route, never calculate. The **StateGraph** makes the agent's decisions explicit and inspectable via typed state. The **three-layer memory** is what makes the system's "memory" claim actually true — not just within a turn, but across sessions and time. The **FastAPI layer** enforces the contract between UI and agent via Pydantic schemas, ensuring no untyped data crosses service boundaries. The **Docker + CI/CD** layer wraps everything in reproducible, auditable infrastructure that signals production engineering discipline to any reviewer who runs `docker compose up` and sees a healthy, traced, observable system start in under 60 seconds.

---

*Next: [PRD →](prd.md) | [System Design →](../architecture/system_design.md) | [ADR-001 →](../decisions/adr-001-langgraph-vs-langchain.md)*
