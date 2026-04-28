# Contributing to AI Assistant Docker App

Thank you for your interest in contributing! This project adheres to high engineering standards for agentic systems and MLOps. Please follow these guidelines to ensure a smooth contribution process.

---

## 🚀 Quick Start (Development)

This project uses `uv` for lightning-fast dependency management and `pre-commit` for local quality gating.

1.  **Install `uv`**:
    ```bash
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
2.  **Clone & Sync**:
    ```bash
    git clone https://github.com/SebastianGarrido2790/ai-assistant-docker-app.git
    cd ai-assistant-docker-app
    uv sync
    ```
3.  **Install Pre-Commit**:
    ```bash
    uv run pre-commit install
    ```
4.  **Validate System**:
    ```bash
    ./validate_system.bat
    ```

---

## 🛠 Engineering Standards

### 1. The "Python-Development" Standard
- **Strong Typing**: 100% type hint coverage. We use `pyright` for static analysis.
- **Isolation**: Use `uv` and Docker. Never install dependencies globally.
- **Documentation**: **Google-style docstrings** are mandatory for all functions and classes.
- **Linting**: `ruff` is used for linting and formatting. Ensure `ruff check` and `ruff format` pass.
- **Security**: `bandit` is used for static security analysis. Avoid `eval()`.

### 2. Agentic Design Principles
- **Brain vs. Brawn**: The LLM (Agent) reasoning must be separated from deterministic execution (Tools).
- **Structured I/O**: All tools must use Pydantic `BaseModel` for input validation.
- **No Naked Prompts**: System prompts must be versioned and stored in `src/agents/prompts.py`.
- **Causal Observability**: All tool calls and agent turns must be wrapped in OpenTelemetry spans.

---

## 🌿 Branching & PR Strategy

- **Branch Naming**:
    - `feature/name` — New features.
    - `fix/issue` — Bug fixes.
    - `docs/topic` — Documentation updates.
- **PR Requirements**:
    - Descriptive title (following Conventional Commits, e.g., `feat: add long-term memory`).
    - Linked issue or design document (ADR).
    - Summary of changes and "Why this approach?".
    - Screenshot/Video if UI changes are involved.
    - All CI checks must pass (Lint, Typecheck, Tests >= 70% coverage, Docker Build, Trivy).

---

## 🧪 Testing Requirements

- **Pytest**: All new logic must be accompanied by unit or integration tests.
- **Coverage**: Total statement coverage must remain **>= 70%**.
- **Fixtures**: Use centralized fixtures in `tests/conftest.py`.
- **Mocking**: Mock external API calls (OpenRouter, ChromaDB) to ensure tests are deterministic and fast.

---

## 📝 Commit Messages

We use Conventional Commits:
- `feat:` — A new feature.
- `fix:` — A bug fix.
- `docs:` — Documentation only changes.
- `refactor:` — Code change that neither fixes a bug nor adds a feature.
- `test:` — Adding missing tests or correcting existing tests.
- `chore:` — Changes to the build process or auxiliary tools and libraries.

---

## 🛡 Security

- Never commit `.env` files or secrets.
- Use `python-dotenv` for local configuration.
- Any tool accepting user input must be sanitized against prompt injection (see `src/utils/sanitization.py` if applicable, or implement standard boundary checks).

---

Thank you for building the future of agentic systems with us!
