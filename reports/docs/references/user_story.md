# User Story & Problem Framing
## AI Assistant with Persistent Memory

**Version:** 1.0.0  
**Date:** 2026-04-20  
**References:** [PRD](prd.md) · [Project Charter](project_charter.md)

---

## Epic: An AI Assistant That Actually Remembers

> **As a** user who interacts with AI assistants daily,  
> **I want** the assistant to remember who I am, what we've discussed, and what I prefer across sessions, days, and container restarts —  
> **so that** I never have to re-introduce myself or re-explain context, and can trust that the assistant's answers are grounded in verified tools, not hallucinated guesses.

---

## User Stories

### Story 1 — Persistent Identity Across Sessions
> **As a** returning user,  
> **I want** the assistant to greet me by name and reference facts I shared in a previous session  
> **so that** I feel recognized and don't waste time re-establishing context.

**Acceptance Criteria:**
- [ ] After telling the assistant "I'm a Python developer working on ML systems" in Session A, a new Session B begins and the user asks "What do you know about me?" and the assistant recalls the developer identity and ML context without Session A's message history.
- [ ] The recalled facts come from ChromaDB (Layer 3 semantic search), not from RAM.
- [ ] The recall is triggered automatically by `preload_memory` at the start of every turn.

**Technical mapping:** FR-2.3, FR-2.4, FR-4.3

---

### Story 2 — Memory That Survives a Restart
> **As a** user who has been chatting with the assistant for 20 minutes,  
> **I want** my full conversation history to be restored if the app restarts or the container is redeployed  
> **so that** I never lose context mid-task due to an infrastructure event.

**Acceptance Criteria:**
- [ ] After a conversation establishes 10 messages, `docker compose restart ai-app` is executed, and the same `thread_id` is used — the full message history is restored.
- [ ] The restoration is handled by `SqliteSaver` (Layer 2) transparently to the user.
- [ ] The UI displays a "Resumed session [thread_id]" indicator when a prior session is loaded.

**Technical mapping:** FR-2.2, FR-3.4

---

### Story 3 — Trustworthy Tool-Backed Answers
> **As a** user asking the assistant to calculate something or look something up,  
> **I want** the assistant to use a verified, deterministic tool rather than generating a plausible-sounding answer from pattern matching  
> **so that** I can trust the result without independently verifying every answer.

**Acceptance Criteria:**
- [ ] When asked "What is 15% of $4,847.23?", the agent calls `CalculatorTool`, not the LLM reasoning pathway, and the result is arithmetically correct 100% of the time.
- [ ] When asked "What happened in AI news this week?", the agent calls `WebSearchTool` and cites the specific sources it retrieved.
- [ ] When asked to retrieve a document previously added to the knowledge base, the agent calls `RAGRetriever` and returns the exact passage, not a paraphrase.
- [ ] In all above cases, the LLM synthesizes the tool output into natural language — it does *not* regenerate the underlying facts.

**Technical mapping:** FR-1.2, FR-5.1, FR-5.3

---

### Story 4 — Human Approval Before Consequential Actions
> **As a** user,  
> **I want** the assistant to pause and ask for my explicit approval before it saves any personal information or modifies stored state  
> **so that** I remain in control of what the system remembers about me.

**Acceptance Criteria:**
- [ ] When the agent determines it should call `save_user_memory`, execution pauses and a Streamlit confirmation dialog appears: "Save this fact to your memory profile? [Yes/No]"
- [ ] If the user selects "No", the tool call is aborted and the graph continues without saving.
- [ ] The HITL interrupt is implemented as a LangGraph `interrupt()` before the `tool_node` for write operations.

**Technical mapping:** FR-1.4, FR-4.3

---

### Story 5 — One-Command Local Setup
> **As a** developer cloning this repository for the first time,  
> **I want** to start the entire system with a single command  
> **so that** I spend zero time debugging environment configuration before seeing the app run.

**Acceptance Criteria:**
- [ ] `docker compose up` brings all services (ai-app, llm, db, vector) to a healthy state in under 60 seconds on a machine with Docker installed.
- [ ] `.env.example` clearly documents every required environment variable with placeholder values and comments.
- [ ] The README's Quick Start section requires no steps beyond `git clone`, copying `.env.example` to `.env`, and `docker compose up`.

**Technical mapping:** FR-4 (UI), NFR (Portability)

---

### Story 6 — Confidence That the Code Is Correct
> **As a** developer contributing to or reviewing this codebase,  
> **I want** a CI pipeline that automatically verifies code quality, type safety, and test coverage on every pull request,  
> **so that** no regression can be merged to `main` without passing all quality gates.

**Acceptance Criteria:**
- [ ] Every PR triggers: ruff lint ✅ + pyright zero errors ✅ + pytest ≥70% coverage ✅ + trivy zero CVEs ✅
- [ ] A CI status badge on the README reflects the current state of `main`.
- [ ] Any failing gate blocks the PR merge.

**Technical mapping:** NFR (Testability, Maintainability).

---

## Problem Framing

### The Iceberg Model

```
VISIBLE TO THE USER (above waterline)
─────────────────────────────────────────────────────────
  "The assistant remembered my name!"
  "It looked up today's news instead of guessing."
  "It survived the restart — my chat is still there."
─────────────────────────────────────────────────────────
INVISIBLE TO THE USER (below waterline — the hard part)

  ┌──────────────────────────────────────────────────────┐
  │ LangGraph StateGraph with typed AgentState           │
  │ → conditional edge routing to ToolNode               │
  │ → SqliteSaver checkpointing on every node step       │
  │ → ChromaDB semantic search injected into prompt      │
  │ → Pydantic v2 schemas on every tool boundary         │
  │ → FastAPI lifespan model loading (not per-request)   │
  │ → multi-stage Docker with non-root user              │
  │ → pyright zero-error type safety                     │
  │ → 3-job GitHub Actions gate with trivy scan          │
  └──────────────────────────────────────────────────────┘
```

**The portfolio insight:** Elite employers are not evaluating the visible layer. They are evaluating whether you know how to architect the invisible layer. Every item below the waterline in the iceberg above maps to a concrete file, ADR, or test in this repository.

---

### Jobs-to-be-Done (JTBD) Framework

| Job | Situation | Motivation | Expected Outcome |
|-----|-----------|-----------|-----------------|
| Recall context | Returning after a break | Don't want to re-explain | Assistant greets with known facts |
| Get accurate data | Asking for calculations/research | Don't trust LLM math | Tool-backed answer with source |
| Maintain control | Sharing personal preferences | Privacy conscious | Approval dialog before save |
| Explore the code | Reviewing for hiring | Assess engineering skill | Legible structure, passing CI, clear ADRs |
| Reproduce locally | Evaluating for adoption | Need to trust it runs | One-command setup, clear `.env.example` |

---

### Anti-Story: What Failure Looks Like

> **As a** user who has been using the assistant for a week,  
> **I try** to ask "What's the weather in Madrid right now?"  
> **And the assistant** confidently makes up a weather report, citing no source, getting the temperature wrong by 12 degrees.

> **As a** technical reviewer,  
> **I open** `app.py`  
> **And I find** one 98-line God-class importing deprecated `ConversationChain`, with no type hints, no tests, no CI, and a Dockerfile that runs as root and copies the entire git history into the image.

**Both anti-stories describe the current state of this project.** Every user story above is a direct response to a specific failure mode in the existing codebase.

---

*Next: [Technical Roadmap →](technical_roadmap.md) | [Back to PRD →](prd.md)*
