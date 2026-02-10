# mnemofy Feature Spec: Meeting Type Detection & Pluggable LLM Engines (v0.2 Draft)

Generated: 2026-02-10T07:59:38

This document defines two production-grade features:

1) **Meeting Type Detection + Template-Based Notes** (built on top of transcripts)  
2) **Pluggable LLM Engine** (OpenAI-like APIs, Ollama, etc.) for notes/classification

The design follows the project constitution:
- **User Control Over Automation**
- **Safe-by-Default Execution**
- **Transparency Over Magic**
- **Deterministic First, Intelligent Second**
- **Local-First by Default**

---

## Feature 1: Meeting Type Detection + Template-Based Notes

### 1.1 Problem
Meeting recordings vary widely (status sync, planning, demo, incident review, tech talk, discovery, 1:1, brainstorming). A single “generic” notes structure yields poor recall and low signal.

We need:
- a **detected meeting type** (or user-chosen),
- a **type-specific notes template**, and
- a notes generator that remains **grounded in transcript evidence**.

### 1.2 Goals
- Detect a meeting “genre” with explainable evidence.
- Select the most appropriate notes template automatically (default), while allowing overrides.
- Preserve raw transcripts always.
- Work without LLM (heuristics only) and improve with LLM if enabled.
- Support non-interactive runs (CI/pipes) without hanging.

### 1.3 Non-Goals (v0.2)
- Perfect diarization (speaker labels). (Planned)
- Fully automatic multi-type segmentation across the whole meeting. (Planned)
- Real-time meeting type updates during live transcription.

### 1.4 Meeting Types (Common Cases)

#### Supported types (v0.2)
1. `status` — progress sync / blockers / next steps
2. `planning` — scope, priorities, estimates, milestones
3. `design` — deep-dive, architecture, trade-offs, review
4. `demo` — show & tell, walkthrough, feedback
5. `talk` — presentation / lecture / technology explanation
6. `incident` — incident review, RCA, postmortem timeline
7. `discovery` — customer discovery, requirements, constraints
8. `oneonone` — 1:1 coaching, feedback, growth, agreements
9. `brainstorm` — idea generation, clustering, experiments

> Rationale: This set covers >90% of real meetings while keeping UX simple.

### 1.5 CLI/UX Contract

#### Flags
- `--meeting-type auto|status|planning|design|demo|talk|incident|discovery|oneonone|brainstorm`
  - Default: `auto`
  - If user sets explicit type, detection is skipped.
- `--template <name>`
  - Optional alias; overrides meeting type mapping.
- `--classify heuristic|llm|off`
  - Default: `heuristic` (local-first)
  - `llm` available only if LLM engine configured
- `--no-interactive`
  - Force non-interactive behavior even in TTY.
  - Useful for scripts.

#### Output behavior (required)
- Always print:
  - detected type (or explicit type),
  - confidence (if auto),
  - evidence terms (top signals),
  - template chosen.

Example (TTY, auto):
```text
Meeting type detection:
- Recommended: planning (0.62)
- Other candidates: status (0.21), design (0.12)
- Evidence: "scope", "estimate", "deadline", "priority"

Template: planning.md
```

### 1.6 Detection: Two-Layer Design

#### Layer A: Heuristic Classifier (default)
Runs fully offline, deterministic.
Inputs:
- transcript segments (timestamped text)
- optionally: first N minutes + high-signal segments (see sampling below)

Outputs:
- top-K meeting types with scores
- evidence tokens/phrases used for scoring

Mechanisms:
- weighted keyword/phrase dictionaries per type
- bigrams/trigrams (e.g., “next steps”, “root cause”)
- structural markers:
  - question density (Q/A heavy suggests talk/discovery)
  - “demo” verbs (“show”, “click”, “screen”, “walk through”)
  - timeline vocabulary (“at 10:42”, “then”, “incident”)
  - estimate vocabulary (“points”, “hours”, “ETA”)

Sampling strategy (recommended):
- Use first 10–15 minutes of transcript
- Add up to 30 “signal segments” where keywords appear
- Cap total text length (prevents latency spikes)

#### Layer B: LLM Classifier (optional)
Enabled when:
- `--classify llm` AND LLM engine configured.

Inputs:
- condensed transcript window (first 10–15 minutes + signal segments)
- heuristic top-3 candidates as hints (optional)

Outputs (strict JSON):
```json
{
  "type": "planning",
  "confidence": 0.62,
  "evidence": ["scope", "estimate", "deadline"],
  "notes_focus": ["risks", "action_items", "decisions"]
}
```

Rules:
- Must rely only on transcript text
- Must return “unclear” if ambiguous
- Must not hallucinate participants or intent

### 1.7 Interactive Selection (TTY)

Triggered when:
- `--meeting-type auto`
- stdin is a TTY
- and NOT `--auto`
- and NOT `--no-interactive`

Menu behavior:
- Arrow keys ↑ ↓ to select type
- Enter to confirm
- Esc selects recommended type
- Show top 5 candidates with confidence
- Show evidence phrases for the recommended type

Non-interactive runs (stdin not TTY):
- Do not prompt
- Use recommended type

### 1.8 Templates

Templates are stored as versioned assets:
- `mnemofy/templates/status.md`
- `mnemofy/templates/planning.md`
- ...

Each template defines:
- Section order
- Required fields
- Optional sections
- Extraction rules (what to look for)

#### Template invariants (must exist in all types)
- `Decisions` (or explicit “No explicit decisions found”)
- `Action Items` (include owner if stated; else `owner: unknown`)
- `Concrete Mentions` (names, projects, companies, dates, numbers, URLs) with timestamps
- `Transcript References`

#### Example templates (section headers)
**status**
- Highlights
- Progress (by owner/team if possible)
- Blockers
- Next steps
- Decisions
- Action Items
- Mentions
- Transcript references

**planning**
- Goal / Outcome
- Scope / Non-scope
- Options discussed
- Estimates / Timeline
- Risks
- Decisions
- Action Items
- Mentions
- Transcript references

**incident**
- Impact
- Timeline
- Root cause (from transcript only)
- Contributing factors
- Fixes applied
- Preventive actions
- Decisions
- Action Items
- Mentions
- Transcript references

### 1.9 Notes Generation (Grounded Summaries)

Notes can be generated in two modes:
- `--notes basic` (deterministic)
- `--notes llm` (richer, requires LLM engine)

#### Basic mode (deterministic)
- time buckets summary (e.g., every 8–12 minutes)
- frequent keywords
- always includes transcript references
- no invented facts

#### LLM mode (strict)
LLM receives:
- chosen meeting type
- the template structure
- transcript with timestamps

LLM must:
- populate template sections using transcript evidence only
- include timestamps for each extracted item
- mark ambiguous statements as `unclear`

Mandatory prompt constraints:
- “Use ONLY the transcript; do not invent facts.”
- “If unclear, mark as unclear and cite timestamp.”
- “Every decision/action/mention must have timestamps.”

### 1.10 Output Files
Alongside transcript outputs:
- `*.notes.md` uses the selected template structure
- `*.meeting-type.json` (optional) stores:
  - detected type
  - confidence
  - evidence
  - engine used (heuristic/llm)
  - timestamp

### 1.11 Failure Modes
- Mixed meetings (status + demo + planning): classifier may be uncertain.
  - Behavior: return low confidence; show top candidates; allow user pick.
- Very short recordings: insufficient evidence.
  - Behavior: default to `status` with low confidence and explain.
- Non-English transcript: heuristics may degrade.
  - Behavior: rely on LLM classifier (if enabled), or allow explicit `--meeting-type`.

### 1.12 Acceptance Criteria
- With `--meeting-type auto`, tool outputs a recommended type + confidence + evidence.
- TTY: interactive selection works via arrow keys.
- Non-TTY: never prompts; uses recommendation.
- Notes output conforms to selected template and includes required invariant sections.
- LLM mode never removes raw transcripts and never produces ungrounded claims without timestamp.

---

## Feature 2: Pluggable LLM Engine (API vs Ollama)

### 2.1 Problem
Users may want:
- a hosted API (OpenAI-like, enterprise gateway, etc.)
- a local engine (Ollama)
- a compatible provider (OpenAI-compatible endpoints)

We need a clean abstraction so that:
- notes/classification can switch engines without changing core logic,
- configuration is manageable via config file and CLI overrides,
- secrets are handled safely.

### 2.2 Goals
- Support multiple LLM backends via a single interface:
  - **OpenAI-compatible HTTP API**
  - **Ollama local**
  - extensible to others (e.g., LM Studio OpenAI-compatible)
- Allow configuration via:
  - config file
  - environment variables
  - CLI flags (highest precedence)
- Ensure safe defaults:
  - LLM features are opt-in
  - missing credentials degrades gracefully

### 2.3 Non-Goals (v0.2)
- Provider-specific “advanced tools” (function calling, vision, etc.)
- Automatic credential discovery beyond standard env vars.

### 2.4 LLM Engine Interface (Implementation Contract)

Define a single internal interface:
```python
class LLMClient:
    def generate_markdown(self, prompt: str) -> str: ...
    def classify_json(self, prompt: str) -> dict: ...
```

Required behaviors:
- request timeout handling
- retries with exponential backoff (limited)
- deterministic options when possible (temperature=0)
- structured output validation for JSON classification

### 2.5 Configuration Sources & Precedence
Highest to lowest precedence:
1. CLI flags
2. Environment variables
3. Config file
4. Built-in defaults

### 2.6 Config File

Path (recommendation):
- macOS/Linux: `~/.config/mnemofy/config.toml`
- Windows: `%APPDATA%\mnemofy\config.toml`

Example `config.toml`:
```toml
[llm]
enabled = true
engine = "openai"        # openai | ollama | openai_compat
mode = "both"            # notes | classify | both
timeout_s = 60
retries = 2
temperature = 0.0

[llm.openai]
api_key_env = "OPENAI_API_KEY"
base_url = "https://api.openai.com/v1"
model = "gpt-4.1-mini"

[llm.openai_compat]
api_key_env = "MY_COMPAT_KEY"
base_url = "https://gateway.example.com/v1"
model = "gpt-4.1-mini"

[llm.ollama]
base_url = "http://localhost:11434"
model = "qwen2.5:14b-instruct"
keep_alive = "5m"
```

### 2.7 CLI Flags
- `--llm on|off`
- `--llm-engine openai|ollama|openai-compat`
- `--llm-model MODEL`
- `--llm-base-url URL`
- `--llm-api-key KEY` *(supported but discouraged; prefer env)*
- `--llm-timeout SEC`
- `--llm-retries N`

### 2.8 Environment Variables
- `MNEMOFY_LLM_ENGINE`
- `MNEMOFY_LLM_MODEL`
- `MNEMOFY_LLM_BASE_URL`
- `MNEMOFY_LLM_TIMEOUT_S`
- `MNEMOFY_LLM_RETRIES`
- Provider keys (recommended):
  - `OPENAI_API_KEY`
  - custom keys via `api_key_env` mapping

### 2.9 Provider Details

#### 2.9.1 OpenAI / OpenAI-compatible HTTP API
- Must support timeout + retries + temperature=0.
- Must validate structured outputs when expecting JSON (classify).

#### 2.9.2 Ollama
- Use Ollama HTTP API at `http://localhost:11434`.
- Handle “model not pulled” with actionable guidance:
  - `ollama pull <model>`

### 2.10 Failure Modes & Degradation
- LLM enabled but credentials missing:
  - fallback to deterministic modes (`--notes basic`, `--classify heuristic`), print next steps.
- LLM engine unreachable:
  - fallback, print actionable message.
- LLM returns invalid JSON:
  - retry once; fallback to heuristic classifier; mark engine failure in logs.

### 2.11 Observability
When LLM is used, print:
```text
LLM: engine=ollama model=qwen2.5:14b-instruct mode=notes
```
In `--verbose`, include request duration and response size if available.

### 2.12 Acceptance Criteria
- Engine selectable via config/env/CLI with clear precedence.
- Notes generation works with OpenAI-like API and Ollama.
- Missing creds/unreachable engine never breaks transcription; degrades gracefully.
- Classification mode can be enabled independently of notes mode.
- LLM outputs remain grounded and timestamped.

---

## Appendix A: Meeting Type → Template Mapping

| Meeting Type | Template |
|-------------|----------|
| status | `status.md` |
| planning | `planning.md` |
| design | `design.md` |
| demo | `demo.md` |
| talk | `talk.md` |
| incident | `incident.md` |
| discovery | `discovery.md` |
| oneonone | `oneonone.md` |
| brainstorm | `brainstorm.md` |

---

## Appendix B: Suggested Repo Layout

```text
mnemofy/
  cli.py
  config.py
  llm/
    __init__.py
    base.py
    openai_client.py
    openai_compat_client.py
    ollama_client.py
  meeting/
    __init__.py
    classify.py
    templates.py
    templates/
      status.md
      planning.md
      design.md
      demo.md
      talk.md
      incident.md
      discovery.md
      oneonone.md
      brainstorm.md
  notes/
    __init__.py
    basic.py
    llm_notes.py
```

---

## Definition of Done
- Meeting type auto-detection selects a template; never hangs in non-interactive contexts.
- Notes are generated using template structures and include invariant sections.
- LLM engine configurable via config/env/CLI with clear precedence.
- Ollama + OpenAI-like API backends work; failures degrade to deterministic behavior.

---

## 1.13 Transcript Post-processing Pipeline (Before Classification & Notes)

### Purpose
To ensure reproducible, stable downstream classification and extraction, mnemofy defines an explicit post-processing layer that operates **after ASR** and **before meeting-type classification and notes generation**.

---

### 1.13.1 Transcript Normalization (Deterministic, Required)

**Input:** raw ASR segments  
**Output:** normalized transcript segments (stable IDs preserved)

Operations:
- Bounded stuttering / filler reduction
- Sentence stitching across short pauses (≤500 ms)
- Safe normalization of numbers, dates, currencies (only when confident)
- Explicit domain dictionary replacements

Rules:
- Meaning must not change.
- No content invention or deletion.
- Fully deterministic and testable.

---

### 1.13.2 Transcript Repair (LLM, Optional)

Fix obvious ASR errors while preserving meaning.

Required output:
```json
{
  "repaired_text": "...",
  "changes": [
    {
      "ref": "@t=10:42-10:52",
      "before": "we need to ship in march tree",
      "after": "we need to ship in March 3",
      "reason": "ASR number confusion"
    }
  ]
}
```

---

## 1.14 Transcript Reference Contract (Groundedness Schema)

### Canonical Reference Object

```json
{
  "ref_id": "seg-042",
  "start": 642.3,
  "end": 651.8,
  "speaker": "S2",
  "text": "We will release on March 1"
}
```

### Reference Usage

```md
Ref: @t=10:42–10:52 (seg-042)
```

Required for Decisions, Action Items, Mentions.

---

## 1.15 Typed Uncertainty Model

All Decisions and Action Items must include:
```yaml
status: confirmed | unclear
```

If `unclear`, a reason is mandatory.

---

## 1.16 Mixed Meetings (Multi-label Support)

Classifier may return:
```json
{
  "types": ["status", "demo"],
  "primary": "status",
  "confidence": 0.55
}
```

Primary template applies; up to two secondary sections may be added.

---

## 1.17 Acceptance Tests for Groundedness

- Every Action Item has ≥1 transcript reference.
- Mentions must exist in transcript text.
- `unclear` requires reason.
- LLM JSON validated with retry/fallback.
