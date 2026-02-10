# Implementation Plan: Meeting Type Detection & Pluggable LLM Engines

**Branch**: `003-meeting-type-llm` | **Date**: 2026-02-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-meeting-type-llm/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Automatically detect meeting types (status, planning, design, demo, talk, incident, discovery, oneonone, brainstorm) from transcripts and generate template-based, structured notes. Support pluggable LLM backends (OpenAI-compatible APIs, Ollama) for enhanced classification and notes extraction, with safe-by-default execution ensuring the tool remains fully functional offline using deterministic heuristics. All LLM-generated content must be grounded in transcript evidence with timestamp references.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: Jinja2 (templating), requests/httpx (LLM HTTP clients), existing mnemofy dependencies (Whisper models)  
**Storage**: File-based (transcripts, notes, templates, config TOML)  
**Testing**: pytest with contract tests for LLM interfaces, integration tests for classification pipeline  
**Target Platform**: macOS/Linux/Windows CLI (cross-platform)  
**Project Type**: Single Python project (extending existing mnemofy codebase)  
**Performance Goals**: Complete meeting type detection + notes generation within 2× transcript duration (30min meeting → ≤60min processing)  
**Constraints**: Offline-capable (heuristic mode required), <200ms interactive menu latency, graceful LLM fallback within 30s  
**Scale/Scope**: 9 meeting types, ~200 heuristic keywords, support for 2-hour transcripts, 9 Jinja2 templates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
