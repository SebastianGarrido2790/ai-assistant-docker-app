# ADR-001: LangGraph over LangChain Chains for Agent Orchestration

| Field       | Value                             |
|-------------|-----------------------------------|
| **Status**  | ✅ Accepted                        |
| **Date**    | 2026-04-20                        |
| **Deciders**| Sebastian                         |
| **Scope**   | `src/agents/` orchestration layer |

---

## Context

The original `app.py` uses `ConversationChain` with `ConversationBufferMemory` from LangChain v0.1. This implementation has critical limitations that prevent this project from qualifying as a production-grade system or demonstrating genuine agentic design competency:

1. **`ConversationChain` is deprecated.** As of LangChain v0.2, the `Chain` abstraction was superseded by the LCEL (LangChain Expression Language) runnable interface and, for multi-step workflows, by LangGraph. Shipping deprecated code signals to reviewers that the design is stale.

2. **No tool-calling capability.** `ConversationChain` is a pure chat wrapper. It cannot invoke deterministic tools (e.g., a web search function, a calculator, or a RAG retriever). The "Brain vs. Brawn" principle is entirely unimplemented.

3. **Ephemeral memory only.** `ConversationBufferMemory` is in-process RAM. A container restart erases all conversation history. The app's own headline — "AI Assistant with Memory" — is a false claim against this implementation.

4. **No state graph.** Sequential logic is hardcoded. There is no mechanism for resumption after failure, HITL interrupts, or time-travel debugging.

5. **No checkpointing.** Without a checkpointer, crash recovery is impossible and the agent cannot be paused mid-workflow for human approval on high-stakes actions.

---

## Decision

**Use LangGraph (`StateGraph`) as the sole orchestration layer for the agent.**

LangChain's `ConversationChain` and `ConversationBufferMemory` will be fully removed. The agent will be implemented as a LangGraph `StateGraph` with a `ToolNode`, a conditional routing edge, and a `SqliteSaver` checkpointer as the first persistence layer.

---

## Options Considered

### Option A — LangChain LCEL + `RunnableWithMessageHistory`

**Description:** Upgrade from `ConversationChain` to the modern LCEL `pipe` (`prompt | llm | parser`) with `RunnableWithMessageHistory` wrapping a custom `BaseChatMessageHistory` backed by SQLite.

**Pros:**
- Lower learning curve than LangGraph for basic chat-with-history use cases.
- Smaller dependency footprint.
- Direct migration path from the current codebase — less refactoring.

**Cons:**
- `RunnableWithMessageHistory` is still a *linear* execution model. It cannot express branching logic, loops, or conditional tool invocation without custom callback hacks.
- Does not support HITL interrupts natively — these require re-implementing the graph traversal manually.
- No native checkpointing at the node level. Crash recovery is manual.
- Does not demonstrate multi-agent orchestration patterns (Coordinator, Agent-as-a-Tool) that elite employers evaluate.
- Portfolio signal: "Can use modern LangChain" — not "can design agentic systems."

### Option B — LangGraph `StateGraph` ✅ *Selected*

**Description:** Model the entire agent workflow as a directed graph where nodes are Python functions (or sub-agents), edges are conditional routing rules, state is a typed `TypedDict` schema, and a `SqliteSaver`/`AsyncPostgresSaver` checkpointer persists state between invocations.

**Pros:**
- **Explicit, inspectable state.** The `AgentState` TypedDict is the single source of truth for what the agent "knows" at any step. No hidden magic.
- **Native HITL support.** `graph.interrupt()` before tool execution is a first-class primitive — critical for any high-stakes tool call.
- **Native checkpointing.** `SqliteSaver` gives real persistence for free. Every node execution is a checkpoint — the agent can be resumed after a crash from the exact step where it failed.
- **Time-travel debugging.** Any past state snapshot can be re-entered for debugging — impossible with LCEL chains.
- **Multi-agent extensibility.** Adding a second specialized sub-agent (e.g., a "Document Analyst" sub-graph) is a `add_node` + `add_edge` call — not a rewrite.
- **Tool-calling is native.** `ToolNode` + `bind_tools` is the canonical pattern. No adapter layers.
- **Portfolio signal:** Demonstrates ability to design stateful, fault-tolerant, multi-step agentic systems — a staff-level engineering competency.

**Cons:**
- Higher initial complexity. LangGraph requires understanding of state schemas, node functions, and conditional edge routing before the first working agent runs.
- Slightly heavier dependency (`langgraph` adds ~15MB over bare `langchain`).
- Graph topology must be reasoned about upfront — a poorly designed graph is hard to refactor.

### Option C — `pydantic-ai` Agent

**Description:** Use the `pydantic-ai` library to define a typed agent with tool decorators and structured output enforcement.

**Pros:**
- First-class Pydantic v2 integration — the strongest type safety of any option.
- Clean, decorator-based tool definition with zero boilerplate.
- Deterministic schema validation on every output without custom parsers.

**Cons:**
- No native graph-based state management. Multi-step workflows require manual orchestration.
- No native HITL primitives or checkpointing.
- Smaller community and ecosystem compared to LangGraph.
- Less directly employable for candidates targeting LangChain/LangGraph-heavy teams (the majority of the 2025–2026 ML engineering market).

**Verdict:** Strong contender for tool-layer validation schemas. We will use `pydantic-ai`-style Pydantic v2 models for tool input/output contracts, but delegate orchestration to LangGraph.

---

## Consequences

### Positive
- The agent becomes a **real agentic system**: it can reason over tools, loop, and resume.
- Memory is genuinely persistent: `SqliteSaver` survives container restarts (Phase 2 baseline); ChromaDB semantic search provides long-term cross-session recall (Phase 2 delivery).
- The system is **interview-demonstrable**: showing the LangGraph Studio trace of a tool-calling loop with a SQLite checkpoint is a concrete artifact that justifies every architectural claim.
- **HITL is unlocked**: before any state-modifying tool (e.g., saving user profile data), the graph can pause and surface an approval prompt in the Streamlit UI.

### Negative / Risks
- **Vendor coupling.** LangGraph is a LangChain Inc. product. If the project migrates away from LangChain's ecosystem, the graph abstraction would need to be rewrapped. Mitigated by keeping all tool *logic* in `src/tools/` as pure Python functions — the graph only *calls* the tools.
- **Debugging complexity.** A misconfigured conditional edge can cause silent infinite loops. Mitigated by setting `recursion_limit` in the graph config and adding the `max_iterations` guard described in GEMINI.md Rule 1.8.3 (Review and Critique Loop Pattern).

---

## Implementation Contract

The following constraints are binding for all PRs touching the agent layer:

| Rule | Constraint |
|------|-----------|
| 1.2 | Agent nodes MUST NOT perform calculations. Math lives in `src/tools/`. |
| 1.3 | Each tool function MUST accept a Pydantic `BaseModel` and return a typed result. |
| 1.4 | Agent output MUST be a typed `AgentState` schema — no untyped `dict` returns. |
| 1.5 | System prompt MUST be loaded from `config/prompts.yaml`, version-pinned. |
| 1.6 | Any tool that writes data MUST be preceded by a `graph.interrupt()` HITL node. |
| 1.7 | Every graph invocation MUST emit an OpenTelemetry span with `thread_id` and `step`. |

---

## References

- [LangGraph Docs — StateGraph](https://langchain-ai.github.io/langgraph/)
- [LangChain Migration Guide v0.1 → v0.2](https://python.langchain.com/docs/versions/migrating_chains/)
- [Portfolio Upgrade Analysis](reports/docs/evaluations/portfolio_upgrade_analysis.md)
