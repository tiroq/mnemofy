# Tasks: Meeting Type Detection & Pluggable LLM Engines

**Input**: Design documents from `/specs/003-meeting-type-llm/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependencies

- [ ] T001 Add new dependencies to pyproject.toml (jinja2>=3.1.0, httpx>=0.25.0, tomli>=2.0.0; tomli-w>=1.0.0)
- [ ] T002 [P] Create src/mnemofy/templates/ directory for Jinja2 templates
- [ ] T003 [P] Create src/mnemofy/llm/ directory for LLM engine modules
- [ ] T004 Install/verify prompt_toolkit dependency (already used in project)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create MeetingType enum/config in src/mnemofy/classifier.py (9 types: status, planning, design, demo, talk, incident, discovery, oneonone, brainstorm)
- [ ] T006 [P] Define meeting type keyword dictionaries in src/mnemofy/classifier.py (heuristic detection data)
- [ ] T007 [P] Create Jinja2 template loader utility in src/mnemofy/notes.py (handles bundled + user override paths ~/.config/mnemofy/templates/)
- [ ] T008 Create TranscriptReference dataclass in src/mnemofy/classifier.py (reference_id, start_time, end_time, speaker, text_snippet)
- [ ] T009 Create GroundedItem dataclass in src/mnemofy/classifier.py (text, status, reason, references, item_type, metadata)
- [ ] T010 Create ClassificationResult dataclass in src/mnemofy/classifier.py (detected_type, confidence, evidence, secondary_types, engine, timestamp)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Auto-Detect Meeting Type & Generate Structured Notes (Priority: P1) 🎯 MVP

**Goal**: Automatically detect meeting type from transcript using deterministic heuristics and generate structured notes using appropriate template. Works completely offline with no LLM required.

**Independent Test**: Run `mnemofy meeting.mp3` and verify (1) detected meeting type with confidence score, (2) structured notes file with Decisions/Action Items/Mentions sections, (3) all output includes timestamp references.

### Implementation for User Story 1

#### Core Classification Engine

- [ ] T011 [P] [US1] Implement heuristic meeting type detector in src/mnemofy/classifier.py (HeuristicClassifier class with detect_meeting_type method)
- [ ] T012 [US1] Implement TF-IDF scoring logic for keywords in src/mnemofy/classifier.py (weighted term frequency with meeting-type dictionaries)
- [ ] T013 [US1] Implement structural feature extraction in src/mnemofy/classifier.py (question density, timeline vocab, estimate markers)
- [ ] T014 [US1] Implement confidence scoring in src/mnemofy/classifier.py (normalize top score to 0-1, calculate margin from second-place)
- [ ] T015 [US1] Implement secondary types ranking in src/mnemofy/classifier.py (return top 5 alternatives sorted by score)

#### Template System

- [ ] T016 [P] [US1] Create status meeting template in src/mnemofy/templates/status.md
- [ ] T017 [P] [US1] Create planning meeting template in src/mnemofy/templates/planning.md
- [ ] T018 [P] [US1] Create design meeting template in src/mnemofy/templates/design.md
- [ ] T019 [P] [US1] Create demo meeting template in src/mnemofy/templates/demo.md
- [ ] T020 [P] [US1] Create talk meeting template in src/mnemofy/templates/talk.md
- [ ] T021 [P] [US1] Create incident meeting template in src/mnemofy/templates/incident.md
- [ ] T022 [P] [US1] Create discovery meeting template in src/mnemofy/templates/discovery.md
- [ ] T023 [P] [US1] Create oneonone meeting template in src/mnemofy/templates/oneonone.md
- [ ] T024 [P] [US1] Create brainstorm meeting template in src/mnemofy/templates/brainstorm.md

#### Basic Notes Generation

- [ ] T025 [US1] Implement basic notes extractor in src/mnemofy/notes.py (BasicNotesExtractor class with time-bucketed summaries)
- [ ] T026 [US1] Implement keyword frequency extraction in src/mnemofy/notes.py (identify frequent terms per time window)
- [ ] T027 [US1] Implement timestamp reference extraction in src/mnemofy/notes.py (create TranscriptReference objects from segments)
- [ ] T028 [US1] Implement decision marker detection in src/mnemofy/notes.py (regex patterns for "agreed", "decided", "will do")
- [ ] T029 [US1] Implement action item extraction in src/mnemofy/notes.py (detect commitments with simple rules)
- [ ] T030 [US1] Implement template rendering pipeline in src/mnemofy/notes.py (load template, populate data, render to Markdown)

#### CLI Integration

- [ ] T031 [US1] Add --meeting-type flag to src/mnemofy/cli.py (auto|status|planning|design|demo|talk|incident|discovery|oneonone|brainstorm)
- [ ] T032 [P] [US1] Add --template flag to src/mnemofy/cli.py (custom template filename)
- [ ] T033 [P] [US1] Add --classify flag to src/mnemofy/cli.py (heuristic|llm|off)
- [ ] T034 [US1] Integrate classification into main CLI workflow in src/mnemofy/cli.py (call detector after transcription)
- [ ] T035 [US1] Implement confidence threshold logic in src/mnemofy/cli.py (≥0.6 auto-accept, 0.5-0.6 warn, <0.5 defer to interactive)

#### Output Management

- [ ] T036 [US1] Add meeting-type.json output in src/mnemofy/output_manager.py (save ClassificationResult as JSON)
- [ ] T037 [US1] Modify notes.md output in src/mnemofy/output_manager.py (use detected template instead of generic)
- [ ] T038 [US1] Add detection info to console output in src/mnemofy/cli.py (display type, confidence, evidence before generating notes)

#### Testing for User Story 1

- [ ] T039 [P] [US1] Add heuristic classifier tests in tests/test_classifier.py (test all 9 meeting types with sample transcripts)
- [ ] T040 [P] [US1] Add template rendering tests in tests/test_template_rendering.py (verify all 9 templates render correctly)
- [ ] T041 [P] [US1] Add basic notes extraction tests in tests/test_notes_enhanced.py (verify decisions, actions, mentions extracted)
- [ ] T042 [P] [US1] Add CLI integration tests in tests/test_cli_integration.py (end-to-end: audio → transcript → classification → notes)
- [ ] T043 [US1] Update integration pipeline tests in tests/test_integration_pipeline.py (add meeting type detection step)

**Checkpoint**: User Story 1 complete - tool can auto-detect meeting types and generate structured notes offline without LLM

---

## Phase 4: User Story 2 - Enhanced Notes with LLM (Priority: P2)

**Goal**: Leverage LLM to extract richer, more nuanced notes with inferred context, implicit decisions, and grounded timestamp references. Falls back to basic mode if LLM unavailable.

**Independent Test**: Configure LLM engine, process same transcript with --llm vs without, compare outputs for completeness and grounding (all claims have timestamps).

**Dependencies**: Can start after Foundational phase; US3 (config) complements this but isn't blocking (can use defaults initially)

### Implementation for User Story 2

#### LLM Abstraction Layer

- [ ] T044 [P] [US2] Create base LLM engine interface in src/mnemofy/llm/base.py (ABC with classify_meeting_type, generate_notes, health_check methods)
- [ ] T045 [P] [US2] Implement OpenAI engine in src/mnemofy/llm/openai_engine.py (OpenAIEngine class implementing base interface)
- [ ] T046 [P] [US2] Implement Ollama engine in src/mnemofy/llm/ollama_engine.py (OllamaEngine class implementing base interface)
- [ ] T047 [US2] Implement LLM engine factory in src/mnemofy/llm/__init__.py (get_llm_engine with health check and fallback logic)

#### High-Signal Segment Extraction

- [ ] T048 [US2] Implement decision marker extraction in src/mnemofy/classifier.py (extract_high_signal_segments using regex patterns: "we'll", "let's", "agreed", "will do", "TODO", "should we", "what if")
- [ ] T049 [US2] Implement sliding window context in src/mnemofy/classifier.py (±50 words around each marker)
- [ ] T050 [US2] Implement segment deduplication in src/mnemofy/classifier.py (avoid overlapping segments, limit to top 5 by diversity)

#### LLM Classification

- [ ] T051 [US2] Implement LLM transcript window preparation in src/mnemofy/classifier.py (first 10-15 min + high-signal segments)
- [ ] T052 [US2] Create LLM classification prompt in src/mnemofy/classifier.py (structured prompt requesting JSON: type, confidence, evidence, notes_focus)
- [ ] T053 [US2] Implement LLM classifier in src/mnemofy/classifier.py (LLMClassifier class with detect_meeting_type method)
- [ ] T054 [US2] Add JSON response validation in src/mnemofy/classifier.py (retry once with stricter prompt if invalid, fallback to heuristic)

#### LLM Notes Generation

- [ ] T055 [US2] Create LLM notes extraction prompt in src/mnemofy/notes.py (constraints: "Use ONLY transcript", "mark unclear with reason", "include timestamps")
- [ ] T056 [US2] Implement LLM notes extractor in src/mnemofy/notes.py (LLMNotesExtractor class extracting decisions, actions, mentions with grounding)
- [ ] T057 [US2] Implement grounding validator in src/mnemofy/notes.py (verify all GroundedItems have valid TranscriptReferences)
- [ ] T058 [US2] Implement unclear status handler in src/mnemofy/notes.py (mark items as unclear with mandatory reason when LLM cannot trace to transcript)
- [ ] T059 [US2] Add LLM timeout and retry logic in src/mnemofy/llm/base.py (max 2 retries with exponential backoff, timeout=30s)

#### CLI Integration

- [ ] T060 [US2] Add --llm flag to src/mnemofy/cli.py (on|off, enables LLM for both classification and notes)
- [ ] T061 [P] [US2] Add --llm-engine flag to src/mnemofy/cli.py (openai|ollama|openai_compat)
- [ ] T062 [P] [US2] Add --llm-model flag to src/mnemofy/cli.py (model name override)
- [ ] T063 [US2] Integrate LLM fallback in src/mnemofy/cli.py (catch LLM failures, display warning, fall back to heuristic/basic mode within 30s)
- [ ] T064 [US2] Add engine info to console output in src/mnemofy/cli.py (display: engine=openai, model=gpt-4o-mini, mode=notes|classify|both)

#### Testing for User Story 2

- [ ] T065 [P] [US2] Add LLM engine contract tests in tests/test_llm_engines.py (mock OpenAI/Ollama APIs, test interface compliance)
- [ ] T066 [P] [US2] Add high-signal extraction tests in tests/test_classifier.py (verify decision markers detected, segments extracted)
- [ ] T067 [P] [US2] Add LLM notes grounding tests in tests/test_notes_enhanced.py (verify all items have timestamps, unclear items have reasons)
- [ ] T068 [P] [US2] Add fallback behavior tests in tests/test_llm_engines.py (simulate LLM failures, verify graceful degradation)
- [ ] T069 [US2] Update CLI integration tests in tests/test_cli_integration.py (test --llm flag, engine info display)

**Checkpoint**: User Story 2 complete - LLM-enhanced notes work when configured, gracefully fall back when not

---

## Phase 5: User Story 3 - Configure & Switch LLM Providers (Priority: P3)

**Goal**: Support multiple LLM providers (OpenAI, Ollama, enterprise gateways) via config file, env vars, and CLI flags with secure API key handling.

**Independent Test**: Create config file with OpenAI settings, run notes generation, then change config to Ollama, verify both backends work correctly with identical input.

**Dependencies**: Can start after Foundational phase; complements US2

### Implementation for User Story 3

#### Configuration Loading

- [ ] T070 [US3] Implement TOML config loader in src/mnemofy/llm/config.py (load_llm_config from ~/.config/mnemofy/config.toml)
- [ ] T071 [US3] Implement env var override in src/mnemofy/llm/config.py (MNEMOFY_LLM_* variables override file config)
- [ ] T072 [US3] Implement precedence chain in src/mnemofy/llm/config.py (CLI > env vars > file > defaults)
- [ ] T073 [US3] Add API key security validation in src/mnemofy/llm/config.py (raise error if API key found in TOML file, require env var)
- [ ] T074 [US3] Implement default model selection in src/mnemofy/llm/config.py (gpt-4o-mini for OpenAI, llama3.2:3b for Ollama)

#### Configuration Schema

- [ ] T075 [P] [US3] Add config validation in src/mnemofy/llm/config.py (engine_type valid, timeout > 0, temperature 0-2, model non-empty)
- [ ] T076 [P] [US3] Add TOML syntax error handling in src/mnemofy/llm/config.py (catch parse errors, display line number, use defaults)
- [ ] T077 [US3] Integrate config loader in src/mnemofy/llm/__init__.py (use config in engine factory)

#### CLI Integration

- [ ] T078 [P] [US3] Add --llm-base-url flag to src/mnemofy/cli.py (custom API endpoint)
- [ ] T079 [P] [US3] Add --llm-timeout flag to src/mnemofy/cli.py (request timeout in seconds)
- [ ] T080 [P] [US3] Add --llm-retries flag to src/mnemofy/cli.py (max retry attempts)
- [ ] T081 [US3] Update CLI config precedence in src/mnemofy/cli.py (apply CLI flag overrides to loaded config)

#### Error Handling & Guidance

- [ ] T082 [US3] Add missing credentials handler in src/mnemofy/cli.py (detect missing API key, display setup instructions with config file path and env var names)
- [ ] T083 [US3] Add Ollama model check in src/mnemofy/llm/ollama_engine.py (detect unpulled model, display "ollama pull <model>" instruction)
- [ ] T084 [US3] Add engine reachability check in src/mnemofy/llm/base.py (display actionable error for network failures)

#### Testing for User Story 3

- [ ] T085 [P] [US3] Add config loading tests in tests/test_llm_config.py (test precedence: CLI > env > file > defaults)
- [ ] T086 [P] [US3] Add API key security tests in tests/test_llm_config.py (verify error when key found in TOML)
- [ ] T087 [P] [US3] Add env var override tests in tests/test_llm_config.py (verify MNEMOFY_LLM_* variables work)
- [ ] T088 [P] [US3] Add TOML error handling tests in tests/test_llm_config.py (test invalid syntax, missing file, permissions)
- [ ] T089 [US3] Update CLI tests in tests/test_cli_integration.py (test all --llm-* flags)

**Checkpoint**: User Story 3 complete - users can configure and switch between LLM providers easily

---

## Phase 6: User Story 4 - Interactive Meeting Type Selection (Priority: P4)

**Goal**: When run in terminal, display interactive menu showing detected type and alternatives, allow arrow key navigation to override before notes generation.

**Independent Test**: Run tool in TTY, verify menu appears with detected type and top 5 candidates, confirm arrow keys work for selection, Esc uses recommended type.

**Dependencies**: Requires US1 (classification); independent of US2/US3

### Implementation for User Story 4

#### Interactive Menu

- [ ] T090 [US4] Create meeting type selector in src/mnemofy/tui/meeting_type_menu.py (select_meeting_type function using prompt_toolkit radiolist_dialog)
- [ ] T091 [US4] Implement menu rendering in src/mnemofy/tui/meeting_type_menu.py (display recommended type, top 5 candidates with scores, evidence phrases)
- [ ] T092 [US4] Add arrow key navigation in src/mnemofy/tui/meeting_type_menu.py (↑↓ to move, Enter to confirm, Esc for recommended)
- [ ] T093 [US4] Add confidence-based menu behavior in src/mnemofy/tui/meeting_type_menu.py (high ≥0.6: brief confirm, medium 0.5-0.6: warning + override, low <0.5: multi-select)

#### CLI Integration

- [ ] T094 [US4] Add --no-interactive flag to src/mnemofy/cli.py (skip menu, use recommended type)
- [ ] T095 [US4] Add TTY detection in src/mnemofy/cli.py (check stdin.isatty(), skip menu if piped or --no-interactive)
- [ ] T096 [US4] Integrate menu into CLI workflow in src/mnemofy/cli.py (show menu after classification if interactive, before notes generation)
- [ ] T097 [US4] Add non-interactive default behavior in src/mnemofy/cli.py (auto-accept recommended for low confidence when --no-interactive)

#### Testing for User Story 4

- [ ] T098 [P] [US4] Add menu rendering tests in tests/test_meeting_type_menu.py (verify display format, candidate ordering)
- [ ] T099 [P] [US4] Add menu interaction tests in tests/test_meeting_type_menu.py (simulate arrow keys, Enter, Esc)
- [ ] T100 [P] [US4] Add TTY detection tests in tests/test_cli_integration.py (test behavior when stdin is/isn't TTY)
- [ ] T101 [US4] Add --no-interactive flag tests in tests/test_cli_integration.py (verify menu skipped, recommended type used)

**Checkpoint**: User Story 4 complete - interactive mode provides user control over automation

---

## Phase 7: User Story 5 - Post-Process Transcripts for Quality (Priority: P5)

**Goal**: Normalize transcripts (stutter reduction, sentence stitching) and optionally repair ASR errors with LLM, outputting change logs while preserving timestamps.

**Independent Test**: Process transcript with known ASR errors, enable repair, verify output shows corrections with change logs and original timestamps intact.

**Dependencies**: Independent of other stories; optional enhancement

### Implementation for User Story 5

#### Deterministic Normalization

- [ ] T102 [P] [US5] Implement stutter reduction in src/mnemofy/transcriber.py (detect repeated words like "I I I", reduce to single instance with bounds)
- [ ] T103 [P] [US5] Implement filler word filtering in src/mnemofy/transcriber.py (optional removal of "um", "uh", "like" with conservative bounds)
- [ ] T104 [P] [US5] Implement sentence stitching in src/mnemofy/transcriber.py (join segments across pauses ≤500ms)
- [ ] T105 [US5] Implement safe number/date normalization in src/mnemofy/transcriber.py (standardize "march three" → "March 3" when unambiguous)

#### LLM-Based Repair

- [ ] T106 [US5] Create transcript repair prompt in src/mnemofy/transcriber.py (prompt: "Fix ASR errors, preserve meaning, log changes")
- [ ] T107 [US5] Implement LLM repair in src/mnemofy/transcriber.py (call LLM with transcript, extract repaired text + changes log)
- [ ] T108 [US5] Implement changes log format in src/mnemofy/transcriber.py (before/after text, timestamp, reason for each correction)
- [ ] T109 [US5] Add timestamp preservation in src/mnemofy/transcriber.py (ensure original segment timestamps remain intact after repair)

#### CLI Integration

- [ ] T110 [P] [US5] Add --normalize flag to src/mnemofy/cli.py (enable deterministic normalization)
- [ ] T111 [P] [US5] Add --repair flag to src/mnemofy/cli.py (enable LLM-based repair, requires --llm)
- [ ] T112 [US5] Integrate normalization into pipeline in src/mnemofy/cli.py (run after transcription, before classification)
- [ ] T113 [US5] Add changes log output in src/mnemofy/output_manager.py (save repair changes to separate file if repair enabled)

#### Testing for User Story 5

- [ ] T114 [P] [US5] Add normalization tests in tests/test_transcriber.py (verify stutter reduction, sentence stitching, timestamp preservation)
- [ ] T115 [P] [US5] Add LLM repair tests in tests/test_transcriber.py (mock LLM, verify changes log format)
- [ ] T116 [US5] Add CLI integration tests in tests/test_cli_integration.py (test --normalize and --repair flags)

**Checkpoint**: User Story 5 complete - transcript quality improvements available

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T117 [P] Update README.md with meeting type detection feature documentation
- [ ] T118 [P] Create example transcript samples in examples/ for each meeting type
- [ ] T119 [P] Add verbose mode logging in src/mnemofy/cli.py (LLM request duration, response size, detection details)
- [ ] T120 Validate quickstart.md instructions (run all examples, verify outputs)
- [ ] T121 [P] Add performance benchmarks in tests/ (verify SC-004: 2× transcript duration SLA)
- [ ] T122 [P] Add menu latency tests in tests/test_meeting_type_menu.py (verify SC-009: <200ms response time)
- [ ] T123 Code cleanup and refactoring (remove debug code, optimize imports)
- [ ] T124 [P] Security review of API key handling (verify env-var-only, no leakage in logs)
- [ ] T125 [P] Update CHANGELOG.md with feature summary

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - MVP TARGET
- **User Story 2 (Phase 4)**: Depends on Foundational completion - Can start in parallel with US1 but naturally follows for integration
- **User Story 3 (Phase 5)**: Depends on Foundational completion - Complements US2 (provides config for LLM)
- **User Story 4 (Phase 6)**: Depends on Foundational + US1 (needs classification) - UI enhancement
- **User Story 5 (Phase 7)**: Depends on Foundational completion - Independent preprocessing enhancement
- **Polish (Phase 8)**: Depends on desired user stories being complete

### User Story Dependencies & Independence

- **US1 (P1)**: FULLY INDEPENDENT - Core offline functionality, no LLM required
  - Deliverable: Auto-detect meeting type + structured notes (heuristic mode)
  - Test: `mnemofy meeting.mp3` → produces notes with detected type
  
- **US2 (P2)**: INDEPENDENT (can use hardcoded defaults initially)
  - Integrates with: US1 (uses classification), US3 (uses config - but can default)
  - Deliverable: LLM-enhanced notes with grounding
  - Test: `mnemofy meeting.mp3 --llm` → richer notes with timestamps
  
- **US3 (P3)**: FULLY INDEPENDENT - Configuration system
  - Enhances: US2 (provides flexible config)
  - Deliverable: Multi-provider LLM configuration
  - Test: Create config → switch providers → verify both work
  
- **US4 (P4)**: DEPENDS on US1 (needs classification output)
  - Integrates with: US1 (displays classification results interactively)
  - Deliverable: Interactive meeting type selection menu
  - Test: Run in TTY → menu appears → arrow keys work
  
- **US5 (P5)**: FULLY INDEPENDENT - Preprocessing enhancement
  - Enhances: All stories (improves input quality)
  - Deliverable: Transcript normalization and repair
  - Test: `mnemofy meeting.mp3 --normalize --repair` → corrections logged

### Within Each User Story

**US1 (Core MVP)**:
1. Templates (T016-T024) - all can be parallel
2. Classifier core (T011-T015) - sequential dependencies
3. Notes extraction (T025-T030) - depends on classifier
4. CLI integration (T031-T038) - depends on classifier + notes
5. Tests (T039-T043) - can be parallel, independent of implementation order

**US2 (LLM Enhancement)**:
1. LLM abstraction (T044-T047) - can be parallel
2. High-signal extraction (T048-T050) - sequential
3. LLM classification (T051-T054) - depends on abstraction + signal extraction
4. LLM notes (T055-T059) - depends on abstraction
5. CLI integration (T060-T064) - depends on LLM components
6. Tests (T065-T069) - can be parallel

**US3 (Configuration)**:
1. Config loading (T070-T074) - sequential (precedence chain)
2. Validation (T075-T077) - depends on loader
3. CLI integration (T078-T081) - depends on loader
4. Error handling (T082-T084) - can be parallel
5. Tests (T085-T089) - can be parallel

**US4 (Interactive Menu)**:
1. Menu implementation (T090-T093) - sequential
2. CLI integration (T094-T097) - depends on menu
3. Tests (T098-T101) - can be parallel

**US5 (Preprocessing)**:
1. Normalization (T102-T105) - can be parallel
2. LLM repair (T106-T109) - sequential
3. CLI integration (T110-T113) - depends on both
4. Tests (T114-T116) - can be parallel

### Parallel Opportunities

**Within Setup**: T002, T003 can run in parallel

**Within Foundational**: T006, T007 can run in parallel

**Within US1**:
- Templates: T016-T024 (all 9 templates in parallel)
- Tests: T039-T042 (all test files in parallel)
- CLI flags: T032, T033 (in parallel)

**Within US2**:
- LLM engines: T044-T046 (all 3 in parallel: base, OpenAI, Ollama)
- Tests: T065-T068 (all test suites in parallel)
- CLI flags: T061, T062 (in parallel)

**Within US3**:
- Validation + error handling: T075, T076, T082-T084 (all in parallel)
- CLI flags: T078-T080 (all in parallel)
- Tests: T085-T088 (all in parallel)

**Within US4**:
- Tests: T098-T100 (all in parallel)

**Within US5**:
- Normalization: T102-T104 (all in parallel)
- CLI flags: T110, T111 (in parallel)
- Tests: T114, T115 (in parallel)

**Within Polish**:
- T117-T119, T121-T122, T124-T125 (all documentation/validation tasks in parallel)

**Across User Stories** (once Foundational complete):
- US1, US2, US3, US5 can all start in parallel (different files)
- US4 should wait for US1 to complete (depends on classification)

---

## Parallel Example: User Story 1

```bash
# Launch all template creation tasks together:
Task T016: "Create status meeting template"
Task T017: "Create planning meeting template"
Task T018: "Create design meeting template"
Task T019: "Create demo meeting template"
Task T020: "Create talk meeting template"
Task T021: "Create incident meeting template"
Task T022: "Create discovery meeting template"
Task T023: "Create oneonone meeting template"
Task T024: "Create brainstorm meeting template"

# Launch all test tasks together (after implementation):
Task T039: "Add heuristic classifier tests"
Task T040: "Add template rendering tests"
Task T041: "Add basic notes extraction tests"
Task T042: "Add CLI integration tests"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only) - RECOMMENDED

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T010) - CRITICAL checkpoint
3. Complete Phase 3: User Story 1 (T011-T043)
4. **STOP and VALIDATE**: 
   - Test: `mnemofy sample.mp3`
   - Verify: Detected type, structured notes, timestamp references
   - Success criteria: SC-001, SC-002, SC-005, SC-007
5. **Deploy/Demo MVP** - Full offline meeting type detection working!

### Incremental Delivery (MVP + Enhancements)

1. Complete Setup + Foundational → Foundation ready
2. Complete User Story 1 (T011-T043) → Test independently → **Deploy MVP** ✅
3. Complete User Story 3 (T070-T089) → Add config system → **Deploy v1.1**
4. Complete User Story 2 (T044-T069) → Add LLM enhancement → **Deploy v1.2** 
5. Complete User Story 4 (T090-T101) → Add interactive menu → **Deploy v1.3**
6. Complete User Story 5 (T102-T116) → Add preprocessing → **Deploy v1.4**
7. Complete Polish (T117-T125) → Final quality pass → **Deploy v2.0**

Each increment delivers value without breaking previous functionality.

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (T001-T010)
2. **Once Foundational done, parallelize**:
   - Developer A: User Story 1 (T011-T043) - Core MVP
   - Developer B: User Story 3 (T070-T089) - Config system
   - Developer C: User Story 5 (T102-T116) - Preprocessing
3. **After US1 complete**:
   - Developer D: User Story 4 (T090-T101) - Interactive menu (depends on US1)
4. **After US3 complete**:
   - Any developer: User Story 2 (T044-T069) - LLM enhancement (benefits from US3 config)
5. **All stories complete**: Polish together (T117-T125)

---

## Task Count Summary

- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 6 tasks
- **Phase 3 (US1 - MVP)**: 33 tasks
- **Phase 4 (US2 - LLM)**: 26 tasks
- **Phase 5 (US3 - Config)**: 20 tasks
- **Phase 6 (US4 - Interactive)**: 12 tasks
- **Phase 7 (US5 - Preprocessing)**: 15 tasks
- **Phase 8 (Polish)**: 9 tasks

**Total**: 125 tasks

**MVP Only** (Phases 1-3): 43 tasks
**MVP + LLM** (Phases 1-5): 89 tasks

---

## Success Criteria Mapping

| SC-001 | Maps to T011-T015 (heuristic classifier achieving 90% accuracy) |
| SC-002 | Maps to T016-T024, T030 (all templates have invariant sections) |
| SC-003 | Maps to T056-T058 (LLM notes with timestamp references) |
| SC-004 | Maps to T048-T050, T121 (high-signal extraction + performance benchmarks) |
| SC-005 | Maps to T011-T043 (full offline functionality in US1) |
| SC-006 | Maps to T070-T089, T120 (config setup + quickstart validation) |
| SC-007 | Maps to T094-T097 (--no-interactive flag) |
| SC-008 | Maps to T047, T054, T063 (LLM fallback mechanism) |
| SC-009 | Maps to T090-T093, T122 (menu latency) |

---

## Notes

- [P] tasks = different files, no shared state, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- MVP is just US1 (43 tasks) - delivers core value proposition
- US2-US5 are optional enhancements that layer on top
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid premature optimization - get US1 working first!
