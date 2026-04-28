# Model Card — AI Assistant with Persistent Memory

> Following the [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993) framework (Mitchell et al., 2019).

---

## 1. Model Details

| Field | Value |
|:---|:---|
| **Name** | AI Assistant with Persistent Memory |
| **Version** | 1.0.0 |
| **Type** | Agentic LLM Wrapper (Tool-Augmented, Memory-Persistent) |
| **Architecture** | LangGraph `StateGraph` with `ToolNode` + `tools_condition` routing |
| **Underlying LLMs** | Local: `ai/devstral-small-2` (Docker Model Runner) · Cloud: configurable via `REMOTE_MODEL_NAME` (default: OpenRouter) |
| **Memory Layers** | Layer 1: In-session `GraphState` · Layer 2: SQLite `SqliteSaver` · Layer 3: ChromaDB HNSW vector store |
| **Framework** | LangChain + LangGraph + FastAPI + Streamlit |
| **Developed By** | Sebastian Garrido |
| **License** | MIT |
| **Repository** | [github.com/SebastianGarrido2790/ai-assistant-docker-app](https://github.com/SebastianGarrido2790/ai-assistant-docker-app) |

---

## 2. Intended Use

### Primary Use Cases
- **Personal productivity assistant**: Answering questions, summarizing documents, performing calculations, and retrieving web search results.
- **Memory-persistent conversations**: Retaining user preferences and facts across multiple disconnected sessions via ChromaDB semantic retrieval.
- **Agentic MLOps portfolio demonstration**: Showcasing production-grade agentic design patterns — Brain/Brawn separation, three-layer memory, structured I/O, HITL gating, and full observability.

### Out-of-Scope Uses
- **Medical, legal, or financial advice**: The system has no domain-specific fine-tuning and should not be used as a substitute for professional judgment.
- **Multi-user production deployment**: The current architecture uses a shared SQLite checkpoint store. Multi-tenant use requires a PostgreSQL checkpointer.
- **Processing personally identifiable information (PII)**: Memory persistence stores facts indefinitely in ChromaDB. Do not use for systems where PII must be purged on request (GDPR compliance gap).
- **Autonomous code execution**: The agent does not have a code execution tool. Adding one requires the hardened sandbox specified in the Agentic Architecture Standards (Rule 1.3).

---

## 3. Factors

### Relevant Factors
- **Language**: Primarily English. Performance in other languages depends on the underlying LLM's multilingual capabilities.
- **Domain**: General-purpose. Performance degrades on highly specialized domains (e.g., molecular biology, tax law) without domain-specific RAG or fine-tuning.
- **Model selection**: Switching between local (`devstral-small-2`) and cloud models (OpenRouter) affects response quality, latency, and cost significantly.

### Evaluation Factors
- Response quality was evaluated informally on general QA, math problems, web search tasks, and document summarization.
- No formal benchmark dataset was used. See §6.

---

## 4. Metrics

| Metric | Value | Notes |
|:---|:---|:---|
| **Test Coverage** | ≥ 70% | Enforced by CI pipeline gate |
| **Pyright Errors** | 0 | Standard mode, 100% clean |
| **Ruff Violations** | 0 | Rules: `E, F, I, UP, N, W, B, SIM, C4, RUF` |
| **Bandit Findings** | 0 (Medium/High) | All findings addressed or annotated |
| **API Latency (P50)** | ~2–5s (local) · ~1–3s (cloud) | Varies by model and query complexity |
| **Memory Retrieval** | Top-3 semantic results per turn | ChromaDB HNSW cosine similarity |

---

## 5. Evaluation Data

No formal evaluation dataset was constructed for this version. The system was validated against:
- Unit tests covering API endpoints, tool logic, memory operations, UI components, and exception handling.
- Manual end-to-end testing of the tool loop (search → calculate → save memory → retrieve memory).
- Integration testing via `validate_system.bat` (4-pillar: lint → typecheck → pytest → Docker build).

**Limitation:** The absence of a benchmark evaluation dataset means quantitative performance claims cannot be made. Future versions should include a curated QA evaluation set.

---

## 6. Training Data

This system does **not** train or fine-tune any model. It wraps pre-trained LLMs via the LangChain/OpenAI API interface. Training data considerations apply to the underlying models:

- **`devstral-small-2`**: Mistral AI coding model. Refer to [Mistral documentation](https://mistral.ai/models/) for training data details.
- **OpenRouter models**: Refer to the respective model provider's documentation.

---

## 7. Ethical Considerations

| Risk | Severity | Mitigation |
|:---|:---|:---|
| **Prompt injection via tool input** | High | Input sanitization patterns documented in `CONTRIBUTING.md` (Rule 1.3). `sanitize_tool_input()` utility available in the codebase. |
| **Hallucination in tool outputs** | Medium | Tools are deterministic (Brawn). LLM (Brain) only selects tools — it does not perform calculations or memory writes directly. |
| **Memory persistence without consent** | Medium | `save_memory_tool` is agent-controlled. HITL gate (`HITL_ENABLED=true`) can be activated to require human approval before memory writes. |
| **Unrestricted API access** | Medium | `X-API-Key` header authentication enforced on all chat endpoints. |
| **LLM API cost abuse** | Medium | Rate limiting: 10 requests/minute via `slowapi`. |
| **Bias in underlying LLM** | Low–High | Inherits biases of the underlying pre-trained model. No mitigation applied at the wrapper level. |

---

## 8. Caveats and Recommendations

1. **Do not store sensitive data in memory**: ChromaDB stores facts as plaintext. Any user-shared PII will persist until manually deleted via the ChromaDB API.
2. **HITL is disabled by default**: Set `HITL_ENABLED=true` in `.env` to activate the Human-in-the-Loop gate for `save_memory_tool` calls. This is strongly recommended for regulated environments.
3. **Local model quality**: `devstral-small-2` is a code-focused model. For general conversation or document summarization, switching to a larger cloud model via `use_cloud=true` in the chat request will produce significantly better results.
4. **Telemetry**: By default, OpenTelemetry spans are exported to console (`OTEL_EXPORTER_TYPE=console`). For production observability, set `OTEL_EXPORTER_TYPE=otlp` and configure a Jaeger or Grafana Tempo backend.
5. **Checkpoint persistence**: SQLite checkpoints grow unbounded. For long-running deployments, implement a checkpoint pruning strategy or migrate to a PostgreSQL `AsyncPostgresSaver`.

---

*Last updated: 2026-04-28 · Version 1.0.0*
