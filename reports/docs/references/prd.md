# Product Requirements Document (PRD)
## AI Assistant with Persistent Memory — Production-Grade Agentic System

**Version:** 1.0.0  
**Date:** 2026-04-20  
**Status:** Approved  
**Author:** Sebastian  
**References:** [Project Charter](project_charter.md) · [ADR-001](../decisions/adr-001-langgraph-vs-langchain.md) · [System Design](../architecture/system_design.md)

---

## Project Analogy

> Think of this system as a **veteran personal assistant who works at a law firm**.
>
> A *junior* assistant (the current implementation) takes excellent notes during a meeting but destroys them when they go home. Bring them back tomorrow and they remember nothing, and you must brief them from scratch every single time. They also insist on doing arithmetic in their head, occasionally getting it wrong, and you never quite know why.
>
> A *veteran* assistant (this system's target state) keeps a structured case file for each client (SQLite session), a personal memory journal they consult at the start of every meeting (ChromaDB semantic search), and delegates all calculations and research to trusted specialists (deterministic tools). When they hand you a conclusion, you know *exactly* which source they cited and which specialist they consulted. And when they're about to do something consequential, like filing a court document, they pause and ask for your approval first (HITL interrupt).

---

## 1. Executive Summary

This project upgrades a deprecated LangChain v0.1 chat wrapper into a production-grade AI assistant demonstrating the full **Agentic MLOps** engineering stack:

- A stateful **LangGraph agent** that reasons over tools and maintains typed graph state
- A **three-layer memory system** that makes "persistent memory" technically true, not a marketing claim
- A **FastAPI microservice** that decouples agent logic from the UI and exposes typed contracts
- A **hardened Docker Compose stack** and **GitHub Actions CI/CD pipeline** that enforce engineering discipline end-to-end

The project is simultaneously a working product and a portfolio artifact designed to demonstrate staff-level ML engineering competency to elite technical reviewers.

---

## 2. Problem Statement

### 2.1 What Users Experience
- AI assistants forget everything between sessions, forcing users to constantly re-explain context.
- There is no reliable way for an assistant to do research, calculate, or retrieve documents without the answer being potentially hallucinated.
- Switching the AI "off and on" (container restart) resets all memory.

### 2.2 What Engineers Experience (The Real Problem)
- Most "AI with memory" implementations ship `ConversationBufferMemory` and call it done. This is architecturally indefensible and actively misleading.
- LLMs performing calculations and data transformations violate the determinism contract that production systems require.
- Monolithic "God-class" AI apps cannot be tested, scaled, or debugged in isolation.

---

## 3. Goals and Non-Goals

### Goals ✅
| # | Goal | Measurable Outcome |
|---|------|--------------------|
| G1 | True persistent memory | Memory survives container restart; passes `test_memory_persistence.py` |
| G2 | Real tool-calling agent | Agent correctly routes to ≥1 tool in ≥80% of relevant test prompts |
| G3 | Type-safe codebase | `pyright` reports zero errors in `src/` |
| G4 | Production-grade API | FastAPI `/v1/chat` returns Pydantic-typed `ChatResponse` |
| G5 | CI/CD quality gate | All 3 jobs pass on every PR to `main` |
| G6 | Hardened container | Trivy scan: zero HIGH/CRITICAL CVEs in final image |
| G7 | Test coverage | `pytest --cov=src` ≥ 70% |
| G8 | Live memory demo | "What do you remember about me?" returns facts from a prior session |

### Non-Goals ❌
| # | Non-Goal | Rationale |
|---|----------|-----------|
| NG1 | Kubernetes / Helm charts | Single-service app; overkill signals cargo-culting |
| NG2 | Fine-tuning | Out of scope; adds breadth without depth to this project |
| NG3 | Multi-user authentication | Increases scope; `thread_id` scoping is sufficient for demo |
| NG4 | Real-time audio/video input | Separate capability; not part of the core system narrative |
| NG5 | Celery / Redis task queue | No async background work to justify the dependency |
| NG6 | Second LLM provider (Anthropic, Gemini) | More providers ≠ more depth; OpenRouter already covers routing |

---

## 4. User Personas

### Persona A — "The Technical Evaluator" (Primary)
**Profile:** Senior ML Engineer or Technical VP reviewing portfolio projects.  
**Context:** Spending 8–12 minutes reading the README, skimming the `src/` directory, and running `docker compose up`.  
**Their silent rubric:**
- Does the code separate concerns or is it a monolith?
- Is there a real agent or just an LLM API call?
- Does "memory" mean RAM or actual persistence?
- Is there a CI badge? Does it pass?
- Would I trust this person to design a production system?

**What they need to see:**  
An architecture diagram that makes the system legible in 60 seconds, a module structure that passes a 30-second code review, and a README that answers "why is this hard" without prompting.

### Persona B — "The Technical User" (Secondary)
**Profile:** A developer who uses the assistant as a reference implementation for their own work.  
**Context:** Clones the repo, runs it locally, reads the ADRs to understand design decisions.  
**Their need:** The system must run with `docker compose up` in under 2 minutes and include a
`.env.example` with clear instructions.

---

## 5. Functional Requirements

### FR-1: Agent Orchestration
- **FR-1.1** The agent MUST be implemented as a LangGraph `StateGraph` with typed `AgentState`.
- **FR-1.2** The agent MUST support at least 3 tools: web search, calculator, and RAG retrieval.
- **FR-1.3** The agent MUST loop (max 10 iterations) until no tool calls remain in the state.
- **FR-1.4** State-modifying tools (e.g., `save_user_memory`) MUST trigger a HITL interrupt before execution.

### FR-2: Memory System
- **FR-2.1** Layer 1 (in-session) MUST use `AgentState` TypedDict, survives within a single turn sequence.
- **FR-2.2** Layer 2 (persistent) MUST use `SqliteSaver` checkpointer, survives container restart.
- **FR-2.3** Layer 3 (semantic) MUST use ChromaDB, enables cross-session fact retrieval by meaning.
- **FR-2.4** At the start of every turn, a `preload_memory` tool MUST query Layer 3 and inject top-3 facts into the system prompt context.
- **FR-2.5** At session end, conversation facts MUST be extractable and archivable to Layer 3.

### FR-3: API Layer
- **FR-3.1** MUST expose `POST /v1/chat` accepting `ChatRequest` and returning `ChatResponse`.
- **FR-3.2** MUST expose `GET /v1/health` returning `{"status": "healthy", "model": str, "memory_backend": str}`.
- **FR-3.3** The agent MUST be initialized once via lifespan context manager — never inside a request handler.
- **FR-3.4** Every request MUST be traceable by `thread_id` for session continuity.

### FR-4: UI Layer
- **FR-4.1** Streamlit MUST act as a thin HTTP client — zero business logic in `gui.py`.
- **FR-4.2** UI MUST display `thread_id` and allow session switching.
- **FR-4.3** UI MUST include a "What do you remember about me?" demo button.
- **FR-4.4** UI MUST display model selection toggle (local vs. cloud).

### FR-5: Tool Contracts
- **FR-5.1** Every tool function MUST accept a Pydantic `BaseModel` as its sole argument.
- **FR-5.2** Every tool function MUST have a complete Google-style docstring (the agent reads these).
- **FR-5.3** Tools MUST be pure, deterministic Python functions with no LLM calls inside them.

---

## 6. Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| **Performance** | End-to-end latency (local model, no tools) | < 5 seconds per turn |
| **Performance** | End-to-end latency (cloud model, 1 tool call) | < 15 seconds per turn |
| **Reliability** | Agent must not crash on tool failure | Tool exceptions return structured error string to agent |
| **Security** | No secrets in source code | All API keys in `.env`, excluded by `.gitignore` |
| **Security** | Container user | Non-root; `trivy scan` zero HIGH/CRITICAL CVEs |
| **Maintainability** | Type coverage | `pyright` zero errors; ≥80% of functions have type hints |
| **Testability** | Test coverage | ≥70% via `pytest-cov` |
| **Observability** | Per-request metrics | `tokens_used`, `latency_ms`, `model`, `tool_calls` logged per request |
| **Portability** | One-command startup | `docker compose up` starts all services in correct order |
| **Documentation** | Self-describing | New engineer can understand system in <15 minutes via docs |

---

## 7. System Architecture Summary

*See full diagram in [System Design](../architecture/system_design.md).*

```
Streamlit UI  →  POST /v1/chat  →  FastAPI  →  LangGraph Agent
                                               ├── WebSearchTool     → Tavily API
                                               ├── CalculatorTool    → numexpr
                                               └── RAGRetriever      → ChromaDB
                                               ↕
                                    Memory Layer 2: SQLite (SqliteSaver)
                                    Memory Layer 3: ChromaDB (semantic)
```

---

## 8. Dependencies and Constraints

### External Dependencies
| Dependency | Purpose | Risk if Unavailable |
|------------|---------|---------------------|
| OpenRouter API | Cloud LLM backend | Fallback to local model; warn in UI |
| Tavily API | Web search tool | Tool returns error string; agent continues without |
| Docker Model Runner | Local LLM (ai/devstral-small-2) | System degrades to cloud-only mode |

### Technical Constraints
- Python `>=3.12, <3.13` (pinned for determinism)
- All packages pinned via `uv.lock`
- `pyproject.toml` is the single source of all project metadata and tooling config
- No Jupyter notebooks in `src/`; notebooks are EDA-only in `notebooks/`

---

## 9. Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Memory persistence demo | "Remember about me" returns facts from prior session | Manual test + `test_memory_persistence.py` |
| CI pipeline green | All 3 jobs pass on every PR | GitHub Actions status badge |
| Tool invocation accuracy | Agent calls correct tool for structured test prompts | `tests/evals/test_tool_routing.py` |
| Container startup time | All services healthy in < 60 seconds | Measured in CI `docker compose up` step |
| Reviewer first impression | README legible in < 90 seconds | Hallway test with a non-project developer |

---

## 10. Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-04-20 | Initial PRD created from Project Charter |

---

*Next: [User Story →](user_story.md) | [Technical Roadmap →](technical_roadmap.md)*
