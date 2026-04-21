# System Architecture: AI Assistant with Persistent Memory

**Version:** 1.0.0  
**Date:** 2026-04-20  
**Status:** Target State (Post-Upgrade)

---

## 1. High-Level System Overview

The system is comprised of three independently deployable layers, each with a single, well-defined responsibility. The Streamlit UI is a **dumb client**, it knows nothing about the agent or memory. The FastAPI service is the **single integration point**. The LangGraph agent is where all intelligence lives.

```mermaid
graph TB
    subgraph UI["🖥️ Human Interface Layer"]
        ST["Streamlit UI<br/><i>gui.py · port 8501</i>"]
    end

    subgraph API["⚙️ FastAPI Agent Service"]
        R1["POST /v1/chat"]
        R2["GET /v1/health"]
    end

    subgraph AGENT["🧠 LangGraph Agent (StateGraph)"]
        direction TB
        N1["agent_node<br/><i>LLM reasoning + tool selection</i>"]
        N2["tool_node<br/><i>ToolNode dispatcher</i>"]
        N3["HITL interrupt<br/><i>human approval gate</i>"]
        CE{{"should_continue?<br/><i>conditional edge</i>"}}

        N1 --> CE
        CE -->|"tool_calls in state"| N2
        CE -->|"no tool_calls"| END(["__end__"])
        N2 --> N1
        N3 -.->|"approved"| N2
    end

    subgraph TOOLS["🔧 Deterministic Tool Layer"]
        T1["🌐 WebSearchTool<br/><i>Tavily API</i>"]
        T2["🧮 CalculatorTool<br/><i>numexpr evaluator</i>"]
        T3["📄 RAGTool<br/><i>ChromaDB retriever</i>"]
    end

    subgraph MEMORY["💾 Three-Layer Memory System"]
        direction TB
        M1["Layer 1: In-Session State<br/><i>AgentState TypedDict<br/>messages + user_facts</i>"]
        M2["Layer 2: Persistent Sessions<br/><i>SqliteSaver checkpointer<br/>thread_id → full graph state</i>"]
        M3["Layer 3: Long-Term Semantic Memory<br/><i>ChromaDB · pgvector<br/>cross-session fact retrieval</i>"]
    end

    subgraph LLM["🤖 LLM Backend"]
        L1["Local Model<br/><i>ai/devstral-small-2 · llama.cpp</i>"]
        L2["Cloud Model<br/><i>OpenRouter API</i>"]
    end

    subgraph INFRA["🐳 Docker Compose Infrastructure"]
        D1["ai-app container<br/><i>multi-stage · non-root</i>"]
        D2["llm container<br/><i>Docker Model Runner</i>"]
        D3["db container<br/><i>SQLite / pgvector</i>"]
    end

    subgraph CICD["🔄 CI/CD Pipeline (GitHub Actions)"]
        C1["quality-gate<br/><i>ruff · pyright</i>"]
        C2["test<br/><i>pytest --cov ≥70%</i>"]
        C3["docker-build<br/><i>build + trivy scan</i>"]
        C1 --> C2 --> C3
    end

    ST -->|"POST /v1/chat {message, thread_id, use_cloud}"| R1
    ST -->|"GET /v1/health"| R2
    R1 --> N1
    N2 --> T1
    N2 --> T2
    N2 --> T3
    N1 <-->|"reads/writes messages"| M1
    M1 <-->|"checkpoint on every node"| M2
    T3 <-->|"embed + retrieve"| M3
    N1 -->|"use_cloud=false"| L1
    N1 -->|"use_cloud=true"| L2
    D1 -.->|"hosts"| API
    D2 -.->|"hosts"| L1
    D3 -.->|"hosts"| M2
```

---

## 2. Data Flow: Single Chat Turn

This diagram traces the exact execution path for a single user message, from keystroke to response.

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit UI
    participant API as FastAPI /v1/chat
    participant Agent as LangGraph Agent
    participant Tools as Tool Layer
    participant Mem2 as SQLite Checkpointer
    participant Mem3 as ChromaDB
    participant LLM as LLM (local/cloud)

    User->>UI: Types message + presses Enter
    UI->>API: POST /v1/chat<br/>{message, thread_id, use_cloud}
    API->>Agent: graph.invoke(state, config={thread_id})

    Note over Agent,Mem2: Checkpoint LOAD — restore prior state for this thread_id
    Mem2-->>Agent: Restore AgentState (message history, user_facts)

    Agent->>Mem3: preload_memory(user_message)
    Mem3-->>Agent: Top-3 semantic matches (user facts from past sessions)

    Agent->>LLM: invoke([system_prompt + history + memory_facts + user_message])
    LLM-->>Agent: AIMessage with tool_calls=[WebSearchTool(...)]

    Note over Agent: conditional edge: tool_calls present → route to tool_node

    Agent->>Tools: WebSearchTool.run(query="...")
    Tools-->>Agent: SearchResult(snippets=[...])

    Agent->>LLM: invoke([...history + tool_result])
    LLM-->>Agent: Final AIMessage (no tool_calls)

    Note over Agent,Mem2: Checkpoint SAVE — persist updated state
    Agent->>Mem2: save(thread_id, updated_AgentState)

    Agent-->>API: AgentState.messages[-1].content
    API-->>UI: ChatResponse(reply="...", thread_id="...", tokens_used=312, latency_ms=840)
    UI-->>User: Renders assistant response
```

---

## 3. Memory Architecture Detail

The three memory layers serve distinct temporal scopes. They are not alternatives, all three operate simultaneously on every turn.

```mermaid
graph LR
    subgraph L1["Layer 1 — Short-Term (Working Memory)"]
        direction TB
        AS["AgentState TypedDict<br/>messages: list[AnyMessage]<br/>user_facts: str<br/>thread_id: str"]
    end

    subgraph L2["Layer 2 — Persistent (Session Memory)"]
        direction TB
        CP["SqliteSaver Checkpointer<br/>conversations.db<br/>table: checkpoints(thread_id, step, state_blob)"]
    end

    subgraph L3["Layer 3 — Long-Term (Semantic Memory)"]
        direction TB
        VDB["ChromaDB Vector Store<br/>collection: user_facts<br/>embed: text-embedding-3-small"]
        RM["recall_user_memory tool<br/><i>semantic search by meaning</i>"]
        SM["save_user_memory tool<br/><i>extract + upsert facts</i>"]
    end

    L1 -->|"checkpoint every node"| L2
    L2 -->|"restored on session resume"| L1
    L1 -->|"end of session → archive"| L3
    L3 -->|"preload_memory at turn start"| L1

    style L1 fill:#1a1a2e,stroke:#4ecca3,color:#fff
    style L2 fill:#1a1a2e,stroke:#f6b93b,color:#fff
    style L3 fill:#1a1a2e,stroke:#e55039,color:#fff
```

**Scope of each layer:**

| Layer | Survives Restart? | Survives New Session? | Search Mode |
|-------|:-----------------:|:---------------------:|-------------|
| 1 — AgentState | ❌ | ❌ | N/A (direct read) |
| 2 — SQLite | ✅ | ❌ (thread_id-scoped) | Exact thread_id lookup |
| 3 — ChromaDB | ✅ | ✅ | Semantic (cosine similarity) |

---

## 4. Module Structure

```mermaid
graph TD
    subgraph Root["📁 ai-assistant-docker-app/"]
        direction TB
        PC["pyproject.toml<br/><i>ruff · pyright · pytest · uv</i>"]
        DC["docker-compose.yaml<br/><i>ai-app · llm · db services</i>"]
        DF["Dockerfile<br/><i>multi-stage · non-root</i>"]
        CP2["config/"]
        SRC["src/"]
        TST["tests/"]
        RPT["reports/"]
    end

    CP2 --> CY["config.yaml<br/><i>paths</i>"]
    CP2 --> PY["params.yaml<br/><i>model params</i>"]
    CP2 --> PR["prompts.yaml<br/><i>versioned system prompts</i>"]

    SRC --> AG["agents/<br/><i>graph.py — StateGraph definition</i>"]
    SRC --> AP["api/<br/><i>main.py — FastAPI app<br/>routes/chat.py, routes/health.py</i>"]
    SRC --> TL["tools/<br/><i>web_search.py<br/>calculator.py<br/>rag_retriever.py<br/>memory_tools.py</i>"]
    SRC --> CF["config/<br/><i>configuration.py — ConfigurationManager</i>"]
    SRC --> EN["entity/<br/><i>schemas.py — ChatRequest, ChatResponse, AgentState</i>"]
    SRC --> UT["utils/<br/><i>logger.py · exceptions.py</i>"]
    SRC --> UI2["ui/<br/><i>gui.py — Streamlit client</i>"]

    TST --> UT2["tests/tools/<br/><i>test_calculator.py<br/>test_web_search.py</i>"]
    TST --> UA["tests/api/<br/><i>test_health.py<br/>test_chat_endpoint.py</i>"]
    TST --> UM["tests/memory/<br/><i>test_sqlite_saver.py<br/>test_chromadb.py</i>"]

    RPT --> DA["docs/architecture/<br/><i>system_design.md (this file)</i>"]
    RPT --> DD["docs/decisions/<br/><i>adr-001-langgraph-vs-langchain.md</i>"]
```

---

## 5. Docker Compose Service Topology

```mermaid
graph TD
    subgraph COMPOSE["docker-compose.yaml"]
        direction TB

        subgraph APP["ai-app service (port 8501 → 8000)"]
            direction LR
            ST2["Streamlit :8501"]
            FA["FastAPI :8000"]
        end

        subgraph LLM2["llm service (port 8080)"]
            GEM["Docker Model Runner<br/>ai/devstral-small-2"]
        end

        subgraph DB2["db service (port 5432 / volume)"]
            SQ["SQLite / PostgreSQL<br/><i>checkpoints + user profiles</i>"]
        end

        subgraph VEC["vector service (port 8000)"]
            CH["ChromaDB server<br/><i>persistent volume</i>"]
        end
    end

    APP -->|"http://llm:8080/v1"| LLM2
    APP -->|"sqlite:///conversations.db"| DB2
    APP -->|"http://chromadb:8000"| VEC
    LLM2 -.->|"healthcheck"| HC1{{"healthy?"}}
    DB2 -.->|"healthcheck"| HC2{{"healthy?"}}
    APP -.->|"depends_on: healthy"| HC1
    APP -.->|"depends_on: healthy"| HC2
```

---

## 6. CI/CD Pipeline

```mermaid
graph LR
    PR["Pull Request / Push to main"]

    subgraph QG["Job 1: quality-gate"]
        R["ruff check + ruff format --check"]
        P["pyright typecheck (zero errors)"]
        R --> P
    end

    subgraph TEST["Job 2: test"]
        PT["pytest --cov=src --cov-fail-under=70"]
    end

    subgraph BUILD["Job 3: docker-build (main only)"]
        DB["docker build (multi-stage)"]
        TV["trivy scan (HIGH/CRITICAL = fail)"]
        DB --> TV
    end

    PR --> QG
    QG -->|"✅ pass"| TEST
    TEST -->|"✅ pass"| BUILD
    BUILD -->|"✅ pass"| MERGE["Merge allowed"]
    QG -->|"❌ fail"| BLOCK["PR blocked"]
    TEST -->|"❌ fail"| BLOCK
    BUILD -->|"❌ fail"| BLOCK
```

---

## 7. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent orchestration | LangGraph StateGraph | Native HITL, checkpointing, graph-based routing |
| Persistence (L2) | SqliteSaver (dev) / AsyncPostgresSaver (prod) | Zero-config locally; production-grade swap |
| Persistence (L3) | ChromaDB | Embeddable in Docker; semantic search; no cloud dependency |
| API framework | FastAPI | Typed Pydantic schemas, async, OpenAPI docs auto-generated |
| Type checking | pyright (standard) | Superior Pydantic v2 inference vs mypy |
| Container strategy | Multi-stage Dockerfile | Layer cache optimization, non-root user, minimal attack surface |
| UI framework | Streamlit (thin client only) | Rapid prototyping; all logic is in FastAPI — UI is replaceable |
