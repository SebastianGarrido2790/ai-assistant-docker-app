# AI Assistant with Persistent Memory

[![CI Pipeline](https://github.com/SebastianGarrido2790/ai-assistant-docker-app/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/SebastianGarrido2790/ai-assistant-docker-app/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-6C63FF?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-microservice-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-multi--stage-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e)](LICENSE.txt)

A production-grade agentic AI assistant built on **LangGraph**, **FastAPI**, and a **three-layer memory architecture**. The agent uses real tools (web search, calculator, document summarization, long-term memory), persists full conversation state to SQLite, and retrieves cross-session facts from a ChromaDB vector store all observable via OpenTelemetry tracing.

![AI Assistant with Persistent Memory](reports/figures/ai_assistant_with_memory.png)

---

## Architecture

```mermaid
graph TB
    subgraph UI["🖥️ Streamlit UI (thin HTTP client)"]
        ST["src/ui/app.py · :8501"]
    end

    subgraph API["⚙️ FastAPI Agent Service"]
        R1["POST /v1/chat"]
        R2["GET /v1/health"]
        OT["OTel span: agent_invocation\nlatency_ms · prompt_tokens · completion_tokens"]
    end

    subgraph AGENT["🧠 LangGraph StateGraph"]
        N1["chat_node\nLLM reasoning + tool selection\nPreload Memory Pattern"]
        N2["tool_node\nToolNode dispatcher"]
        CE{{"tools_condition"}}
        N1 --> CE
        CE -->|"tool_calls"| N2
        CE -->|"done"| END(["__end__"])
        N2 --> N1
    end

    subgraph TOOLS["🔧 Deterministic Tool Layer"]
        T1["🌐 search_web_tool"]
        T2["🧮 calculate_tool"]
        T3["📄 summarize_document_tool"]
        T4["💾 save_memory_tool"]
        T5["🔍 search_memory_tool"]
    end

    subgraph MEMORY["💾 Three-Layer Memory"]
        M1["Layer 1 · In-session GraphState\nadd_messages reducer"]
        M2["Layer 2 · SQLite checkpoints\nSqliteSaver · survives restart"]
        M3["Layer 3 · ChromaDB vector store\nsentence-transformers · HNSW · cross-session"]
    end

    subgraph LLM["🤖 LLM Backend"]
        L1["Local · Docker Model Runner"]
        L2["Cloud · OpenRouter API"]
    end

    ST -->|"POST /v1/chat"| R1
    R1 --> OT --> N1
    N2 --> T1 & T2 & T3 & T4 & T5
    N1 <-->|"read/write"| M1
    M1 <-->|"checkpoint"| M2
    T4 & T5 <-->|"embed/query"| M3
    N1 -->|"Preload Memory"| T5
    N1 --> L1 & L2
```

---

## Why This Is Hard

Most LLM demos are wrappers around a single API call. This system is not. Each of the following design problems has a non-obvious solution:

### 1. Memory that actually persists

Three distinct memory scopes require three distinct implementations. Short-term context is held in `GraphState` using `add_messages` reducers. Session persistence across container restarts uses `SqliteSaver` keyed by `thread_id`. Cross-session semantic recall uses ChromaDB's HNSW index with `sentence-transformers` embeddings. These are not interchangeable — they serve different temporal scopes and failure modes.

The hard part: ChromaDB's default embedding engine silently fails if `onnxruntime` is not pinned in `pyproject.toml`. Facts appear to save but are never written to the vector store. The fix requires both pinning the dependency *and* wiring a structured logger so the failure is observable.

### 2. Service boundary isolation

The agent graph cannot live in the Streamlit process. Streamlit re-runs the entire script on every interaction, which would instantiate new LLM clients, new SQLite connections, and new ChromaDB handles on every user keystroke. The solution is a FastAPI `lifespan()` context manager that builds the compiled graph exactly once at process startup and stores it on `app.state` as a singleton.

### 3. Environment variable inheritance on Windows

When `start` spawns a child `cmd.exe` process, it breaks the parent shell's environment inheritance chain. The host's `OPENROUTER_API_KEY` is visible in the parent session but `None` in the uvicorn worker. The fix is `uv run --env-file .env`, which injects `.env` contents directly into the child process environment, bypassing Windows inheritance entirely.

### 4. Causal observability across tool calls

A single chat turn may invoke two or three tools before returning a final response. Without distributed tracing, a failure in `save_memory_tool` on turn 3 of a 10-turn conversation is indistinguishable from an LLM error. The solution is a two-layer OpenTelemetry span hierarchy: a root `agent_invocation` span per request with child spans per tool call, each capturing `tool.input` and `tool.output`.

### 5. Reproducible Docker builds at development speed

Docker invalidates the layer cache when any file in the `COPY` context changes. Copying the entire source directory before `uv sync` means every code edit forces a full dependency reinstall (~2 minutes). The multi-stage build copies only `pyproject.toml` + `uv.lock` first, then runs `uv sync --frozen`. Source code is copied in a later layer that does not invalidate the dependency cache — rebuilds with no dependency changes complete in seconds.

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) with **Docker Model Runner** enabled
- An [OpenRouter API key](https://openrouter.ai/) (for cloud model mode)

### 1. Clone and configure

```bash
git clone https://github.com/SebastianGarrido2790/ai-assistant-docker-app.git
cd ai-assistant-docker-app
cp .env.example .env
# Edit .env — add your OPENROUTER_API_KEY
```

### 2. Launch

```bash
docker compose up --build
```

**Expected output:**

```
[+] Running 3/3
 ✔ Container ai-assistant-docker-app-llm-1       Healthy
 ✔ Container ai-assistant-docker-app-backend-1   Started
 ✔ Container ai-assistant-docker-app-frontend-1  Started

backend-1   | INFO | Initializing Agent Graph...
backend-1   | INFO | Agent Graph initialized.
backend-1   | INFO | Application startup complete.
```

### 3. Open the UI

Navigate to **[http://localhost:8501](http://localhost:8501)**.

- Toggle **Use Cloud Model** in the sidebar to switch between the local Docker Model Runner and OpenRouter.
- Click **"What do you remember about me?"** to demonstrate cross-session long-term memory recall.

![What do you remember about me?](reports/figures/what_do_you_remember_about_me_button.png)

- The session ID persists conversation history across browser refreshes.

### 4. Verify the API directly

```bash
# Health check
curl http://localhost:8000/v1/health

# Expected:
# {"status":"healthy","model":"google/gemma-4-31b-it","memory_backend":"SQLite + ChromaDB"}

# Send a chat message
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My name is Sebastian and I prefer concise answers.", "session_id": "demo-001", "use_cloud": true}'
```

### Local development (without Docker)

For developers working directly on the host machine, the system includes two automation scripts to ensure environment parity:

1. **[launch_system.bat](launch_system.bat)**: One-click launcher that starts the FastAPI backend and Streamlit frontend in parallel, correctly injecting `.env` and `PYTHONPATH`.
2. **[validate_system.bat](validate_system.bat)**: Local CI mirror that runs the "4 pillars of quality" (Ruff, Pyright, Pytest, and Port validation) before you push.

```bash
uv sync
.\launch_system.bat       # Windows: starts FastAPI + Streamlit in separate processes
.\validate_system.bat     # Run full local CI suite (pyright + ruff + pytest + port checks)
```

---

## Production Engineering Signals

| Signal | Implementation |
|--------|---------------|
| Agent orchestration | LangGraph `StateGraph` with `ToolNode` + `tools_condition` conditional routing |
| Three-layer memory | In-session `GraphState` → `SqliteSaver` (SQLite) → ChromaDB (HNSW vector store) |
| API boundary | FastAPI `lifespan()` singleton + Pydantic v2 request/response contracts |
| Tool contracts | Pydantic `BaseModel` input schemas in `src/entity/agent_tools.py` (contract layer) |
| Observability | Loguru JSON logs + OpenTelemetry two-layer span hierarchy per request |
| Type safety | `pyright` standard mode — 0 errors; `ruff` — 0 violations |
| Container security | Multi-stage Dockerfile, non-root `appuser`, `uv sync --frozen`, Trivy CVE scanning |
| CI/CD | 3-stage GitHub Actions: quality-gate → pytest ≥ 70% → docker build + Trivy |
| Prompt governance | Versioned `SYSTEM_PROMPT_V1` registry in `src/agents/prompts.py` — no naked prompts |
| Config isolation | 3-tier priority chain prevents host env var leakage into Docker containers |

---

## Project Structure

```
ai-assistant-docker-app/
├── src/
│   ├── agents/
│   │   ├── graph.py        # LangGraph StateGraph + ToolNode + Preload Memory Pattern
│   │   ├── memory.py       # ChromaDB PersistentClient (Layer 3)
│   │   └── prompts.py      # Versioned system prompt registry
│   ├── api/
│   │   └── app.py          # FastAPI lifespan + OTel spans + token metrics
│   ├── tools/
│   │   └── tools.py        # 5 deterministic @tool functions with OTel child spans
│   ├── entity/
│   │   ├── schema.py       # API request/response models (Pydantic v2)
│   │   └── agent_tools.py  # Tool input contracts (Pydantic v2)
│   ├── config/
│   │   └── configuration.py # 3-tier priority ConfigurationManager
│   ├── utils/
│   │   ├── logger.py       # Loguru JSON + enqueued sinks
│   │   └── telemetry.py    # OpenTelemetry TracerProvider + BatchSpanProcessor
│   └── ui/
│       ├── app.py          # Thin Streamlit entry point
│       ├── client.py       # HTTP interaction layer (isolated)
│       ├── components.py   # Reusable render functions
│       └── styles.py       # Glassmorphism CSS design system
├── tests/                  # 7 test modules — pytest ≥ 70% coverage gate
├── reports/docs/
│   ├── architecture/system_design.md     # As-built architecture (Mermaid)
│   ├── decisions/adr-001-langgraph-vs-langchain.md
│   ├── workflows/phase_1/2/3_*.md       # Implementation records
│   └── evaluations/portfolio_upgrade_analysis.md
├── .github/workflows/ci.yml  # 3-stage GitHub Actions pipeline
├── Dockerfile                # Multi-stage build
├── docker-compose.yaml
├── validate_system.bat       # Local CI mirror (4 pillars)
└── launch_system.bat         # One-click hybrid launcher
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Project Charter](reports/docs/references/project_charter.md) | Original project charter defining goals, scope, and deliverables |
| [System Design](reports/docs/architecture/system_design.md) | As-built architecture with 11 Mermaid diagrams |
| [ADR-001: LangGraph vs LangChain](reports/docs/decisions/adr-001-langgraph-vs-langchain.md) | Why LangGraph over bare chains |
| [Phase 1 — Foundation Hardening](reports/docs/workflows/phase_1_foundation_hardening.md) | Modular src/, toolchain, multi-stage Docker |
| [Phase 2 — Agentic Upgrade](reports/docs/workflows/phase_2_agentic_upgrade.md) | Tools, three-layer memory, prompt registry |
| [Phase 3 — Production Engineering](reports/docs/workflows/phase_3_production_engineering.md) | FastAPI decoupling, CI/CD, observability, UI modularization |
| [Portfolio Upgrade Analysis](reports/docs/evaluations/portfolio_upgrade_analysis.md) | Clinical diagnosis of the original prototype and upgrade rationale |

---

## Contact

**Sebastian Garrido** · [sebastiangarrido2790@gmail.com](mailto:sebastiangarrido2790@gmail.com) · [GitHub](https://github.com/SebastianGarrido2790)