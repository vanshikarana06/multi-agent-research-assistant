# System Architecture

**Status:** Living document — updated as the project evolves through phases.
**Last updated:** Phase 0 (project scaffolding)

## Overview

The Multi-Agent Research Assistant takes a research question, plans it into
subquestions, dispatches researcher agents to gather evidence from the web,
validates and synthesizes findings, and returns a citation-checked report.

Architecture style (current): **centralized supervisor + worker pattern**,
sequential subquestion processing. Parallel fan-out/fan-in is a planned
upgrade for a later phase — see Phase log below.

## Diagram

```mermaid
flowchart TB
    User["👤 User"]

    subgraph API["FastAPI Layer"]
        POST["POST /research<br/>returns run_id immediately"]
        GET["GET /research/{run_id}<br/>status + result"]
        TRACE["GET /research/{run_id}/trace<br/>debug trace"]
        HEALTH["GET /health"]
        CANCEL["POST /research/{run_id}/cancel"]
    end

    subgraph ORCH["LangGraph Orchestrator (StateGraph)"]
        direction TB
        PLANNER["Planner Node<br/>1 LLM call → strict Pydantic plan"]
        SUPERVISOR["Supervisor Node<br/>rule-based routing"]

        subgraph WORKERS["Researcher Workers"]
            R1["Researcher: subq 1"]
            R2["Researcher: subq 2"]
            R3["Researcher: subq N"]
        end

        VALIDATE["Evidence Validation<br/>schema + sanity checks"]
        REVIEWER["Reviewer Node<br/>sufficient? contradictions?<br/>loop or proceed"]
        WRITER["Writer Node<br/>synthesize report"]
        CITECHECK["Citation Validator<br/>claim → finding → source<br/>hard fail if broken"]
    end

    subgraph TOOLS["Tools"]
        TAVILY["Tavily Web Search"]
        FETCH["Page Fetch + Extraction"]
    end

    subgraph LLM["Groq API"]
        GROQ["LLM Inference<br/>structured outputs"]
    end

    subgraph STATE["Persistence Layer"]
        EARLY["Phase 1-4: in-memory / SQLite"]
        REDIS["Phase 5+: Redis<br/>checkpointing + crash recovery"]
    end

    subgraph OBS["Observability"]
        TRACER["Step Tracer<br/>run_id, node, latency, tokens, errors"]
    end

    subgraph GUARD["Budget & Guardrails"]
        BUDGET["Search / iteration / token limits"]
        SEC["Prompt-injection defense<br/>treat web content as data"]
    end

    User -->|"research question"| POST
    POST --> ORCH
    User --> GET
    User --> TRACE
    User --> HEALTH
    User --> CANCEL

    PLANNER --> SUPERVISOR
    SUPERVISOR -->|"dispatch subquestions"| WORKERS
    R1 --> TAVILY
    R2 --> TAVILY
    R3 --> TAVILY
    TAVILY --> FETCH
    FETCH --> VALIDATE
    WORKERS --> VALIDATE
    VALIDATE --> REVIEWER
    REVIEWER -->|"insufficient → another pass"| SUPERVISOR
    REVIEWER -->|"sufficient"| WRITER
    WRITER --> CITECHECK
    CITECHECK -->|"invalid → fail loudly"| WRITER
    CITECHECK -->|"valid"| REPORT["Final ResearchReport"]

    PLANNER -.->|"structured call"| GROQ
    R1 -.-> GROQ
    R2 -.-> GROQ
    R3 -.-> GROQ
    REVIEWER -.-> GROQ
    WRITER -.-> GROQ

    ORCH -.->|"read/write state"| STATE
    ORCH -.->|"record every step"| TRACER
    ORCH -.->|"enforce limits"| BUDGET
    WORKERS -.->|"sanitize untrusted content"| SEC

    REPORT --> GET
    TRACER --> TRACE

    style User fill:#4a90d9,color:#fff
    style REPORT fill:#2ecc71,color:#000
    style REDIS fill:#e67e22,color:#000
    style GROQ fill:#9b59b6,color:#fff
    style TAVILY fill:#9b59b6,color:#fff
```

## Component responsibilities

| Component | Responsibility |
|---|---|
| FastAPI layer | Accepts requests, returns `run_id` immediately, exposes status/trace polling |
| Planner node | One structured LLM call → research plan + subquestions (Pydantic-validated) |
| Supervisor node | Rule-based routing: dispatch work, decide on re-research passes |
| Researcher workers | Search + fetch + extract evidence per subquestion, with provenance |
| Evidence validation | Schema and sanity checks before findings enter shared state |
| Reviewer node | Decides sufficiency, detects contradictions, loops back or proceeds |
| Writer node | Synthesizes structured report from validated findings only |
| Citation validator | Hard-fails the report if any claim can't be traced to a real source |
| Persistence layer | Run state storage; SQLite/in-memory early, Redis from Phase 5 for checkpointing |
| Observability | Step-level trace: node, input/output, latency, tokens, errors |
| Budget & guardrails | Enforces hard limits on searches/iterations/tokens; treats web content as untrusted |

## External service constraints (verified 2026-09-20, against live account dashboards)

These are hard operational limits, verified directly against our own account
dashboards — not secondary sources, which were found to reference outdated
model names during initial research. Re-check periodically, as providers
change these without notice.

### Groq API (LLM inference)
- Free tier, no credit card required.
- Limits apply **per model, per organization** (not per API key) across
  RPM / RPD / TPM / TPD.
- Available chat models (verified via account dashboard, 2026-09-20):
  `allam-2-7b`, `groq/compound`, `groq/compound-mini`, `openai/gpt-oss-120b`,
  `openai/gpt-oss-20b`, `openai/gpt-oss-safeguard-20b`, `qwen/qwen3.8-27b`.
- **Chosen model: `openai/gpt-oss-120b`** — largest available model at the
  same free-tier ceiling as the smaller `20b` variant, so no capability
  tradeoff exists at this tier.
  Limits: 30 RPM / 1,000 RPD / 8,000 TPM / 200,000 TPD.
- Exceeding any dimension → HTTP 429 with a `retry-after` header, plus
  `x-ratelimit-remaining-*` headers on every response.
- **Design implication:** 1,000 requests/day is a hard daily ceiling. At an
  estimated 5-6 LLM calls per research run (planner, researchers, reviewer,
  writer), this supports roughly 150-200 full research runs/day — sufficient
  for a learning/portfolio project, but a real number that belongs in
  budget-enforcement logic (Phase 5), not just a note.

### Tavily (web search)
- Free "Researcher" plan, no credit card required.
- **1,000 API credits/month**, resets on the 1st of each calendar month.
- 1 basic search = 1 credit. Covers search + extract endpoints.
- Rate limit: 100 requests/minute on a dev key.
- No overage billing on free tier — blocked/429 once credits exhausted.
- **Design implication:** at ~6 searches/run (budget cap, see Budget &
  Guardrails), supports 150+ full research runs/month before exhausting
  the monthly quota. This number directly justifies the "max searches
  per subquestion" and "max total searches per run" budget limits.

## Known simplifications (current phase)

- No Redis yet — introduced deliberately in Phase 5 alongside checkpointing/crash-recovery teaching.
- No parallel worker execution yet — sequential subquestion processing until the sequential path is proven correct.
- No contradiction detection yet — planned as LLM-based pairwise claim comparison, not embedding/NLI-based (cost and complexity tradeoff, documented limitation).
- No long-term/episodic memory — deliberately excluded; each run is self-contained.

## Phase log

- **Phase 0 (current):** Project scaffolding, `uv`, `ruff`, package skeleton, Git/GitHub setup.