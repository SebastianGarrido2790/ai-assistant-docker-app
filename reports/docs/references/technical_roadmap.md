# Technical Roadmap
## AI Assistant with Persistent Memory — Phase-by-Phase Specification

**Version:** 1.0.0  
**Date:** 2026-04-20  
**Status:** Active  
**References:** [PRD](prd.md) · [Project Charter](project_charter.md) · [User Stories](user_story.md) · [ADR-001](../decisions/adr-001-langgraph-vs-langchain.md)

> [!IMPORTANT]
> This roadmap is a living document. Return to this document and update statuses, add discovered tasks, or revise phase boundaries when new requirements or shortcomings emerge. It is a reference, not a contract carved in stone.

---

## Roadmap Overview

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4
Planning   Foundation  Agentic     Production   CI/CD &
& Docs     Hardening   Upgrade     Engineering  Polish
[DONE]     [NEXT]      [PLANNED]   [PLANNED]    [PLANNED]
```

| Phase | Name | Primary Deliverable | Signals To Employers |
|-------|------|---------------------|---------------------|
| 0 | Planning & Documentation | Charter, ADR, PRD, Roadmap, Architecture | Documentation discipline |
| 1 | Foundation Hardening | Modular repo structure, toolchain, hardened Docker | Code structure, type safety |
| 2 | Agentic Upgrade | LangGraph agent, 3 tools, 3-layer memory | Agent design, memory architecture |
| 3 | Production Engineering | FastAPI service, observability, tests | Production engineering maturity |
| 4 | CI/CD & Polish | GitHub Actions, README, demo GIF | DevOps discipline, self-promotion |

---

## Phase 0 — Planning & Documentation
**Status: ✅ Complete**  
**Duration:** 1 session

Planning-first foundation. No code written until the system is understood on paper.

| Task | File(s) | Status |
|------|---------|--------|
| 0.1 Write Architecture Decision Record (LangGraph vs LangChain) | `reports/docs/decisions/adr-001-langgraph-vs-langchain.md` | ✅ Done |
| 0.2 Create system design architecture with Mermaid diagrams | `reports/docs/architecture/system_design.md` | ✅ Done |
| 0.3 Write Project Charter (9 strategic questions) | `reports/docs/references/project_charter.md` | ✅ Done |
| 0.4 Write Product Requirements Document (PRD) | `reports/docs/references/prd.md` | ✅ Done |
| 0.5 Write User Story & Problem Framing | `reports/docs/references/user_story.md` | ✅ Done |
| 0.6 Write Technical Roadmap (this document) | `reports/docs/references/technical_roadmap.md` | ✅ Done |

---

## Phase 1 — Foundation Hardening
**Status: 🔲 Not Started**  
**Rationale:** The codebase must be defensible before the agent is built on top of it.
Structural debt compounds, making a God-class `app.py` makes every subsequent task harder.

### 1.1 — Project Skeleton Refactor

**Goal:** Replace the flat 2-file structure with a standard module layout.

**Tasks:**

| # | Task | File(s) to Create/Modify | Acceptance Criteria |
|---|------|--------------------------|---------------------|
| 1.1.1 | Create `src/` package structure | `src/__init__.py`, `src/agents/`, `src/api/`, `src/tools/`, `src/config/`, `src/entity/`, `src/utils/`, `src/ui/` | All `__init__.py` files present; `uv run python -c "import src"` succeeds |
| 1.1.2 | Create `src/py.typed` marker | `src/py.typed` | File exists; PEP 561 compliance |
| 1.1.3 | Create `src/utils/logger.py` | `src/utils/logger.py` | `from src.utils.logger import get_logger` returns a working logger; JSON output in production mode |
| 1.1.4 | Create `src/utils/exceptions.py` | `src/utils/exceptions.py` | `ChatException`, `ModelTimeoutError`, `ToolExecutionError` defined with traceback capture |
| 1.1.5 | Create `src/constants/__init__.py` | `src/constants/__init__.py` | `CONFIG_FILE_PATH`, `PARAMS_FILE_PATH`, `PROMPTS_FILE_PATH` defined as `pathlib.Path` constants |
| 1.1.6 | Move `gui.py` → `src/ui/gui.py` | `src/ui/gui.py`, `src/ui/__init__.py` | Streamlit still runs via `uv run streamlit run src/ui/gui.py` |
| 1.1.7 | Delete old `app.py` | — | No import of deprecated `ConversationChain` or `ConversationBufferMemory` anywhere in `src/` |

### 1.2 — Configuration System

**Goal:** Eliminate scattered `os.environ.get()` calls. Centralize all config into typed, validated dataclasses.

**Tasks:**

| # | Task | File(s) | Acceptance Criteria |
|---|------|---------|---------------------|
| 1.2.1 | Create `config/config.yaml` | `config/config.yaml` | Defines service URLs, DB paths, vector store paths |
| 1.2.2 | Create `config/params.yaml` | `config/params.yaml` | Defines model names, timeout values, max iterations, embedding model |
| 1.2.3 | Create `config/prompts.yaml` | `config/prompts.yaml` | System prompt versioned as `version: "1.0.0"` with `template:` key |
| 1.2.4 | Create `src/entity/config_entity.py` | `src/entity/config_entity.py` | Frozen Pydantic `BaseModel` for each config section; `model_config = ConfigDict(extra="forbid")` |
| 1.2.5 | Create `src/config/configuration.py` | `src/config/configuration.py` | `ConfigurationManager` class with methods returning typed config entities |
| 1.2.6 | Create `.env.example` | `.env.example` | All required env vars documented with placeholder values and comments |
| 1.2.7 | Create `src/entity/schemas.py` | `src/entity/schemas.py` | `ChatRequest`, `ChatResponse`, `HealthResponse` Pydantic models defined |

### 1.3 — Toolchain Configuration

**Goal:** Make `pyproject.toml` the single source of all project metadata and engineering standards.

**Tasks:**

| # | Task | File(s) | Acceptance Criteria |
|---|------|---------|---------------------|
| 1.3.1 | Add `[tool.pyright]` config to `pyproject.toml` | `pyproject.toml` | `pythonVersion = "3.12"`, `typeCheckingMode = "standard"` |
| 1.3.2 | Add `[tool.ruff]` and `[tool.ruff.lint]` config | `pyproject.toml` | `select` includes `E, F, I, UP, N, W, B, SIM, C4, RUF`; `line-length = 100` |
| 1.3.3 | Add `[tool.pytest.ini_options]` and `[tool.coverage.run]` | `pyproject.toml` | `testpaths = ["tests"]`; `source = ["src"]` |
| 1.3.4 | Create `.pre-commit-config.yaml` | `.pre-commit-config.yaml` | Hooks: `ruff`, `ruff-format`, `pyright`; runs on `pre-commit run --all-files` |
| 1.3.5 | Update `pyproject.toml` dependencies | `pyproject.toml` | Remove deprecated `langchain==0.1.13`; add `langgraph`, `fastapi`, `uvicorn`, `chromadb`, `loguru` |
| 1.3.6 | Run `uv lock` and commit `uv.lock` | `uv.lock` | `uv sync --frozen` succeeds |

### 1.4 — Dockerfile Hardening

**Goal:** Comply with multi-stage, non-root, optimized cache.

**Tasks:**

| # | Task | File(s) | Acceptance Criteria |
|---|------|---------|---------------------|
| 1.4.1 | Rewrite Dockerfile with multi-stage build | `Dockerfile` | Stage 1 (builder): installs deps; Stage 2 (runtime): copies only `.venv` and `src/` |
| 1.4.2 | Add non-root user to Dockerfile | `Dockerfile` | `RUN adduser --disabled-password appuser` + `USER appuser` before `CMD` |
| 1.4.3 | Optimize layer cache order | `Dockerfile` | `COPY pyproject.toml uv.lock` before `COPY src/` |
| 1.4.4 | Update `.dockerignore` | `.dockerignore` | Excludes `.git/`, `notebooks/`, `reports/`, `*.log`, `.env`, `artifacts/` |
| 1.4.5 | Add `LABEL` for metadata | `Dockerfile` | `LABEL version`, `maintainer`, `description` |

**Phase 1 Exit Criteria:**
- [ ] `uv run pyright src/` → zero errors
- [ ] `uv run ruff check src/` → zero errors
- [ ] `uv run ruff format --check src/` → zero errors
- [ ] `docker build -t ai-assistant .` succeeds
- [ ] `docker run --rm ai-assistant` starts without errors
- [ ] `uv run python -c "from src.config.configuration import ConfigurationManager; ConfigurationManager()"` executes

---

## Phase 2 — Agentic Upgrade
**Status: 🔲 Not Started**  
**Rationale:** This is the core portfolio signal. Everything in Phase 1 was infrastructure;
everything in Phase 2 is the actual system.

### 2.1 — LangGraph Agent

**Goal:** Replace `ConversationChain` with a real `StateGraph` agent. See ADR-001.

**Tasks:**

| # | Task | File(s) | Acceptance Criterion |
|---|------|---------|----------------------|
| 2.1.1 | Define `AgentState` TypedDict | `src/agents/state.py` | Contains `messages: Annotated[list, add_messages]`, `user_facts: str`, `thread_id: str` |
| 2.1.2 | Build `agent_node` function | `src/agents/nodes.py` | Calls LLM with bound tools; returns updated state |
| 2.1.3 | Build `should_continue` conditional edge | `src/agents/graph.py` | Returns `"tools"` if tool_calls present; `"__end__"` otherwise |
| 2.1.4 | Build `StateGraph` and compile with checkpointer | `src/agents/graph.py` | `graph.compile(checkpointer=SqliteSaver(...))` runs without error |
| 2.1.5 | Load system prompt from `config/prompts.yaml` | `src/agents/nodes.py` | Prompt includes `{tool_names}`, `{current_date}`, `{user_facts}` placeholders |
| 2.1.6 | Support dual LLM backend (local/cloud) | `src/agents/llm.py` | Factory function `get_llm(use_cloud: bool) -> BaseChatModel` |
| 2.1.7 | Set `recursion_limit=10` guard | `src/agents/graph.py` | Raises `GraphRecursionError` (not infinite loop) after 10 iterations |

### 2.2 — Deterministic Tool Layer

**Goal:** Implement 3 tools that give the agent factual grounding. Each must be pure, deterministic, and Pydantic-typed.

| Tool | Input Schema | Output | External Dependency |
|------|-------------|--------|---------------------|
| `WebSearchTool` | `WebSearchInput(query: str, max_results: int = 3)` | `str` (formatted snippets + URLs) | Tavily API (key in `.env`) |
| `CalculatorTool` | `CalculatorInput(expression: str)` | `str` (result or error message) | `numexpr` (no API) |
| `RAGRetriever` | `RAGInput(query: str, collection: str = "default")` | `str` (top-3 passages with source) | ChromaDB (local) |

**Tasks:**

| # | Task | File(s) | Acceptance Criterion |
|---|------|---------|----------------------|
| 2.2.1 | Implement `WebSearchTool` | `src/tools/web_search.py` | Returns real snippet for "OpenAI GPT-4" query (not hallucinated) |
| 2.2.2 | Implement `CalculatorTool` | `src/tools/calculator.py` | `15% of $4,847.23` returns `727.08` exactly, 100% of the time |
| 2.2.3 | Implement `RAGRetriever` | `src/tools/rag_retriever.py` | Returns passage from an indexed document on semantic query |
| 2.2.4 | Register all tools with LLM via `bind_tools` | `src/agents/llm.py` | Agent selects calculator for math, web for current events, RAG for docs |
| 2.2.5 | Write unit tests for all 3 tools | `tests/tools/` | Each tool has ≥3 parametrized test cases; mocked external API |

### 2.3 — Three-Layer Memory System

**Goal:** Make every user story related to memory provably true with a test.

**Tasks:**

| # | Task | File(s) | Acceptance Criterion |
|---|------|---------|----------------------|
| 2.3.1 | Wire `SqliteSaver` as Layer 2 checkpointer | `src/agents/graph.py` | State restored after `docker compose restart ai-app` with same `thread_id` |
| 2.3.2 | Set up ChromaDB client and collection | `src/memory/vector_store.py` | `get_vector_store()` returns a working `chromadb.Collection` |
| 2.3.3 | Implement `recall_user_memory` tool | `src/tools/memory_tools.py` | Returns top-3 semantically matched facts for a given query |
| 2.3.4 | Implement `save_user_memory` tool | `src/tools/memory_tools.py` | Upserts a fact into ChromaDB; triggers HITL before execution |
| 2.3.5 | Implement `preload_memory` helper | `src/agents/nodes.py` | Runs at start of every `agent_node` call; injects facts into system prompt |
| 2.3.6 | Write memory persistence tests | `tests/memory/` | `test_layer2_survives_restart.py` and `test_layer3_cross_session_recall.py` |

**Phase 2 Exit Criteria:**
- [ ] Agent calls `CalculatorTool` for math (not LLM reasoning) — verified in test
- [ ] Agent calls `WebSearchTool` for current events — verified in test
- [ ] Conversation history survives `docker compose restart ai-app` — verified in test
- [ ] "What do you remember about me?" returns Layer 3 facts from a prior session — verified manually
- [ ] `uv run pyright src/` → still zero errors

---

## Phase 3 — Production Engineering
**Status: 🔲 Not Started**  
**Rationale:** The agent is now real. Wrap it in production-grade infrastructure that makes the system observable, testable, and deployable.

### 3.1 — FastAPI Microservice

**Goal:** Decouple the agent from the UI. The agent becomes a typed HTTP service.

**Tasks:**

| # | Task | File(s) | Acceptance Criterion |
|---|------|---------|----------------------|
| 3.1.1 | Create FastAPI app with lifespan | `src/api/main.py` | Agent compiled once at startup; not per-request |
| 3.1.2 | Implement `POST /v1/chat` endpoint | `src/api/routes/chat.py` | Accepts `ChatRequest`; returns `ChatResponse` with `tokens_used`, `latency_ms` |
| 3.1.3 | Implement `GET /v1/health` endpoint | `src/api/routes/health.py` | Returns `HealthResponse(status="healthy", model=..., memory_backend=...)` |
| 3.1.4 | Mount routes under `/v1` prefix | `src/api/main.py` | `APIRouter(prefix="/v1")` |
| 3.1.5 | Add `src/api/__init__.py` | `src/api/__init__.py` | Proper Python package; `from src.api.main import app` works |
| 3.1.6 | Refactor `src/ui/gui.py` to thin client | `src/ui/gui.py` | Zero LangGraph / LLM imports; HTTP-only via `requests` or `httpx` |
| 3.1.7 | Update `docker-compose.yaml` | `docker-compose.yaml` | Add db and vector services; `ai-app` `depends_on` both as `healthy` |
| 3.1.8 | Write API integration tests | `tests/api/` | `test_health.py` (GET /v1/health → 200) and `test_chat.py` (POST /v1/chat → 200 with valid body) |

### 3.2 — Structured Observability

**Goal:** Replace `logging.basicConfig` with production-grade structured logging and tracing.

**Tasks:**

| # | Task | File(s) | Acceptance Criterion |
|---|------|---------|----------------------|
| 3.2.1 | Configure `loguru` structured logger | `src/utils/logger.py` | JSON output in non-TTY environments; human-readable in TTY |
| 3.2.2 | Log per-request metrics | `src/api/routes/chat.py` | Every `/v1/chat` request logs `{thread_id, tokens_used, latency_ms, model, tool_calls}` |
| 3.2.3 | Add OpenTelemetry spans to agent nodes | `src/agents/nodes.py` | Every `agent_node` and `tool_node` execution emits a span with `thread_id` |
| 3.2.4 | Add request middleware for timing | `src/api/main.py` | `X-Process-Time` header on every response |

**Phase 3 Exit Criteria:**
- [ ] `curl http://localhost:8000/v1/health` returns HTTP 200 with `{"status": "healthy", ...}`
- [ ] `curl -X POST http://localhost:8000/v1/chat -d '{"message": "hello", "thread_id": "test-1"}'` returns a valid `ChatResponse`
- [ ] Streamlit UI makes zero direct LangGraph calls
- [ ] `uv run pytest tests/ --cov=src --cov-fail-under=70` passes
- [ ] Every `POST /v1/chat` logs structured JSON with all required fields

---

## Phase 4 — CI/CD & Final Polish
**Status: 🔲 Not Started**  
**Rationale:** The technical system is complete. Now package it so a recruiter spending 5 minutes with the repo gets the same signal as a developer spending an hour with the code.

### 4.1 — GitHub Actions Pipeline

**Goal:** Enforce quality gates on every PR.

**Tasks:**

| # | Task | File(s) | Acceptance Criterion |
|---|------|---------|----------------------|
| 4.1.1 | Create `ci.yml` with 3 jobs | `.github/workflows/ci.yml` | `quality-gate → test → docker-build` executes on every PR |
| 4.1.2 | Quality gate job: ruff + pyright | `.github/workflows/ci.yml` | Fails on any lint error or type error |
| 4.1.3 | Test job: pytest with coverage | `.github/workflows/ci.yml` | `--cov-fail-under=70` gate |
| 4.1.4 | Docker build + Trivy scan job | `.github/workflows/ci.yml` | Zero HIGH/CRITICAL CVEs; only runs on push to `main` |
| 4.1.5 | Cache `uv` dependencies | `.github/workflows/ci.yml` | `actions/cache` on `~/.cache/uv`; subsequent runs 60% faster |
| 4.1.6 | Store CI badge in README | `README.md` | `[![CI](badge_url)](actions_url)` renders green on `main` |

### 4.2 — System Validation Script

**Goal:** Multi-point local health check before any deployment.

**Tasks:**

| # | Task | File(s) | Acceptance Criterion |
|---|------|---------|----------------------|
| 4.2.1 | Create `validate_system.bat` (Windows) | `validate_system.bat` | Runs all 4 pillars: pyright + ruff → pytest → dvc status → curl /v1/health |
| 4.2.2 | Create `launch_system.bat` (Windows) | `launch_system.bat` | Runs `uv sync` → `docker compose up -d` → opens browser to localhost:8501 |

### 4.3 — README Upgrade

**Goal:** The README is a portfolio landing page, not an afterthought.

**Required sections:**

| Section | Content |
|---------|---------|
| Header | Project name, tagline, CI badge, Docker image size badge |
| Architecture Diagram | Mermaid or exported PNG from `system_design.md` |
| "Why This Is Hard" | 3 bullets: real persistence, real tool-calling, Brain/Brawn separation |
| Quick Start | `git clone` + copy `.env.example` + `docker compose up` — 3 steps max |
| Live Demo | Animated GIF showing memory recall from a prior session |
| Project Structure | File tree of `src/` with one-line descriptions |
| Tech Stack Table | Tool · Purpose · Why This One (not another) |
| Documentation Links | Links to ADR-001, system design, PRD |

### 4.4 — Final Documentation Sync

| # | Task | File(s) |
|---|------|---------|
| 4.4.1 | Update all `Status:` fields in roadmap to reflect final state | `technical_roadmap.md` |
| 4.4.2 | Add `reports/docs/evaluations/` with tool accuracy results | `reports/docs/evaluations/tool_routing_eval.md` |
| 4.4.3 | Record demo GIF | `reports/figures/demo.gif` |
| 4.4.4 | Verify all Mermaid diagrams render in GitHub | Manual check on GitHub.com |

**Phase 4 Exit Criteria (= Project Complete):**
- [ ] CI pipeline status: all 3 jobs green on `main`
- [ ] `docker compose up` → all services healthy in < 60 seconds
- [ ] README renders correctly on GitHub.com, including all diagrams
- [ ] `validate_system.bat` runs to completion with all 4 pillars passing
- [ ] No `TODO` or `FIXME` comments remain in `src/`
- [ ] `uv run pyright src/` → zero errors
- [ ] `uv run pytest tests/ --cov=src --cov-fail-under=70` → passes

---

## Revision Log

| Version | Date | Change | Trigger |
|---------|------|--------|---------|
| 1.0.0 | 2026-04-20 | Initial roadmap | Phase 0 planning session |

> [!NOTE]
> When a new requirement emerges or a task is found to be mis-scoped, add a row here with the date, what changed, and what triggered the change. This log is the project's memory of its own evolution.

---

*← [User Story](user_story.md) · [PRD](prd.md) · [ADR-001](../decisions/adr-001-langchain-vs-langchain.md) · [System Design](../architecture/system_design.md)*
