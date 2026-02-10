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

| Principle | Status | Evidence |
|-----------|--------|----------|
| 1. User Control Over Automation | ✅ PASS | Interactive menu for type selection, CLI flags override auto-detection, explicit --no-interactive flag |
| 2. Safe-by-Default Execution | ✅ PASS | Graceful degradation to heuristic mode, timeout handling, explicit error messages, offline functionality |
| 3. Transparency Over Magic | ✅ PASS | Confidence scores displayed, evidence phrases shown, LLM engine info logged, detection reasoning exposed |
| 4. Deterministic First, Intelligent Second | ✅ PASS | Heuristic mode (deterministic) is default, LLM mode is optional enhancement, raw transcript always preserved |
| 5. Local-First by Default | ✅ PASS | Heuristic classifier works offline, LLM features are opt-in, Ollama provides local LLM option |
| 6. Progressive Disclosure of Complexity | ✅ PASS | Zero-config defaults (auto-detect + heuristic mode), advanced flags optional, interactive guidance provided |
| 7. Performance Is a Feature | ✅ PASS | 2× transcript duration SLA (SC-004), <200ms menu latency (SC-009), token optimization via high-signal segments |
| 8. Explicit Over Implicit Persistence | ✅ PASS | Config file opt-in, API keys via env vars only (never stored), no telemetry, transparent state |
| 9. Media-Agnostic Input | N/A | Feature operates on existing transcripts, does not modify media input handling |
| 10. OSS Quality Bar | ✅ PASS | Comprehensive spec with testable acceptance criteria, stable CLI contracts, documentation required (SC-006) |

**Overall**: ✅ **CLEARED** - No constitutional violations. Feature aligns with all applicable principles.

**Justification for any violations**: None required.

## Project Structure

### Documentation (this feature)

```text
specs/003-meeting-type-llm/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── classification-result.schema.json
│   ├── llm-config.schema.json
│   └── notes-template.schema.json
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/mnemofy/
├── __init__.py
├── audio.py                    # Existing
├── cli.py                      # MODIFIED: Add meeting-type CLI flags
├── formatters.py               # Existing
├── model_selector.py           # Existing
├── notes.py                    # MODIFIED: Extend for template rendering
├── output_manager.py           # MODIFIED: Add meeting-type.json output
├── resources.py                # Existing
├── transcriber.py              # Existing
├── classifier.py               # NEW: Meeting type detection (heuristic + LLM)
├── llm/                        # NEW: LLM integration module
│   ├── __init__.py
│   ├── base.py                 # Abstract LLM engine interface
│   ├── openai_engine.py        # OpenAI-compatible API client
│   ├── ollama_engine.py        # Ollama local client
│   └── config.py               # LLM configuration loader (TOML + env vars)
├── templates/                  # NEW: Jinja2 meeting notes templates
│   ├── status.md
│   ├── planning.md
│   ├── design.md
│   ├── demo.md
│   ├── talk.md
│   ├── incident.md
│   ├── discovery.md
│   ├── oneonone.md
│   └── brainstorm.md
└── tui/
    ├── __init__.py
    ├── model_menu.py           # Existing
    └── meeting_type_menu.py    # NEW: Interactive meeting type selection

tests/
├── __init__.py
├── test_audio.py               # Existing
├── test_cli_integration.py     # MODIFIED: Add meeting-type tests
├── test_formatters.py          # Existing
├── test_integration_pipeline.py # MODIFIED: Add end-to-end meeting workflow
├── test_model_selector.py      # Existing
├── test_notes_enhanced.py      # Existing
├── test_output_manager.py      # MODIFIED: Add meeting-type.json tests
├── test_resources.py           # Existing
├── test_transcriber.py         # Existing
├── test_tui_model_menu.py      # Existing
├── test_classifier.py          # NEW: Heuristic + LLM classification tests
├── test_llm_engines.py         # NEW: Contract tests for LLM interfaces
├── test_llm_config.py          # NEW: Configuration loading tests
├── test_template_rendering.py  # NEW: Jinja2 template tests
└── test_meeting_type_menu.py   # NEW: Interactive menu tests
```

**Structure Decision**: Single Python project structure (Option 1). This feature extends the existing mnemofy CLI with new modules for classification (`classifier.py`), LLM integration (`llm/`), and template rendering (Jinja2 templates in `templates/`). Existing modules (`cli.py`, `notes.py`, `output_manager.py`) are modified to integrate the new functionality.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - This section intentionally left empty. Feature passed all constitutional gates.

---

## Phase 0: Research ✅

**Status**: Complete

**Artifacts**:
- [research.md](./research.md) - Technology decisions for implementation

**Key Decisions**:
1. **Template Rendering**: Jinja2 with autoescape=False for Markdown
2. **HTTP Client**: httpx for LLM API communication (timeout, retry support)
3. **Heuristic Classifier**: Weighted TF-IDF with structural feature boosting
4. **High-Signal Extraction**: Decision marker regex + sliding window
5. **Configuration**: tomli/tomllib for TOML, strict env-var-only for API keys
6. **Interactive TUI**: prompt_toolkit for arrow key navigation
7. **LLM Abstraction**: ABC pattern for pluggable backends
8. **Template Data**: Dataclasses + nested dicts for type safety

---

## Phase 1: Design & Contracts ✅

**Status**: Complete

**Artifacts**:
- [data-model.md](./data-model.md) - Entity definitions and relationships
- [contracts/classification-result.schema.json](./contracts/classification-result.schema.json) - Detection output schema
- [contracts/llm-config.schema.json](./contracts/llm-config.schema.json) - LLM configuration schema
- [contracts/meeting-notes.schema.json](./contracts/meeting-notes.schema.json) - Notes output schema
- [quickstart.md](./quickstart.md) - User documentation
- `.github/agents/copilot-instructions.md` - Updated agent context

**Data Model Summary**:
- 7 core entities defined (MeetingType, ClassificationResult, LLMConfiguration, TranscriptReference, GroundedItem, NotesTemplate, MeetingNotes)
- Validation rules for each entity (confidence ranges, grounding requirements, security constraints)
- Clear data flow: Transcript → Classification → Selection → Generation → Rendering → Output

**Contract Highlights**:
- JSON schemas enforce FR-011 (grounding requirement), FR-016 (API key security), FR-007 (confidence ranges)
- TypeScript-compatible schemas for potential future tooling
- Examples included for all happy paths and edge cases

---

## Post-Design Constitution Re-Check ✅

| Principle | Status | Notes |
|-----------|--------|-------|
| 1. User Control Over Automation | ✅ PASS | Interactive menu design complete, --no-interactive flag defined, CLI overrides documented |
| 2. Safe-by-Default Execution | ✅ PASS | Fallback mechanisms designed, error handling in LLM abstraction, explicit failure modes in contracts |
| 3. Transparency Over Magic | ✅ PASS | ClassificationResult includes evidence, engine_info logged in output, confidence scores visible |
| 4. Deterministic First, Intelligent Second | ✅ PASS | Heuristic classifier is deterministic (TF-IDF), LLM optional, raw transcript preserved |
| 5. Local-First by Default | ✅ PASS | Offline heuristic mode default, Ollama local option designed, no cloud requirement |
| 6. Progressive Disclosure of Complexity | ✅ PASS | Zero-config defaults in schemas, advanced flags optional, quickstart covers beginner → advanced |
| 7. Performance Is a Feature | ✅ PASS | High-signal segment extraction optimizes tokens, <200ms menu latency achievable with prompt_toolkit |
| 8. Explicit Over Implicit Persistence | ✅ PASS | Config validation prevents API key storage, env-var-only enforced in schema, no telemetry |
| 9. Media-Agnostic Input | N/A | No change to media handling |
| 10. OSS Quality Bar | ✅ PASS | Comprehensive docs (quickstart, data model, contracts), stable CLI design, breaking changes avoided |

**Result**: ✅ **CLEARED** - Design maintains constitutional compliance. No new violations introduced.

---

## Next Steps (Phase 2 - Not Part of This Command)

The implementation plan is complete. Next phase (`/speckit.tasks`) will:
1. Break down implementation into prioritized tasks
2. Define test cases for each requirement
3. Create execution checklist aligned with success criteria
4. Link tasks to FR requirements for traceability

**Ready for `/speckit.tasks`**
