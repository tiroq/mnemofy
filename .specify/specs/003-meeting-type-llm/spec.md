# Feature Specification: Meeting Type Detection & Pluggable LLM Engines

**Feature Branch**: `003-meeting-type-llm`  
**Created**: 2026-02-10  
**Status**: Draft  
**Input**: User description: "Meeting Type Detection & Pluggable LLM Engines: Automatically detect meeting types (status, planning, design, demo, talk, incident, discovery, oneonone, brainstorm) and generate template-based notes. Support pluggable LLM backends (OpenAI-compatible APIs, Ollama) for classification and notes generation. Includes transcript post-processing, grounded summaries with timestamp references, and safe-by-default execution with graceful degradation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Auto-Detect Meeting Type & Generate Structured Notes (Priority: P1)

A user transcribes a meeting recording and wants structured, meaningful notes that match the meeting's purpose (status update, planning session, incident review, etc.) without manually specifying the meeting type or template.

**Why this priority**: This is the core value proposition - transforming raw transcripts into actionable, context-appropriate notes. Without this, users get generic outputs that require significant manual reorganization.

**Independent Test**: Can be fully tested by transcribing a 30-minute meeting recording and verifying that the system outputs (1) a detected meeting type with confidence score, (2) structured notes following the appropriate template, and (3) all required sections (Decisions, Action Items, Mentions with timestamps).

**Acceptance Scenarios**:

1. **Given** a finished transcript of a status meeting, **When** the user runs the tool with default settings, **Then** the system detects "status" as the meeting type with confidence >0.6 and generates notes containing Progress, Blockers, Next Steps, Decisions, and Action Items sections.

2. **Given** a finished transcript of a planning meeting, **When** the user runs the tool with default settings, **Then** the system detects "planning" as the meeting type and generates notes containing Goal/Outcome, Scope, Options, Estimates/Timeline, Risks, Decisions, and Action Items sections.

3. **Given** a finished transcript with ambiguous content (low confidence <0.5), **When** detection completes, **Then** the system shows the top 3 candidate meeting types with their confidence scores and evidence phrases.

4. **Given** any detected meeting type, **When** notes are generated, **Then** every Decision and Action Item includes at least one timestamp reference connecting it to the transcript.

---

### User Story 2 - Enhanced Notes with LLM (Priority: P2)

A user wants richer, more nuanced notes than deterministic rules can provide, leveraging AI to extract subtle decisions, infer action item owners, and identify implicit commitments from meeting conversations.

**Why this priority**: Enhances the quality and completeness of notes significantly, but the tool must remain functional without LLM access (local-first principle).

**Independent Test**: Can be tested by configuring an LLM engine, processing the same transcript with LLM mode enabled vs. basic mode, and comparing outputs for completeness, clarity, and grounding (all claims must have timestamps).

**Acceptance Scenarios**:

1. **Given** an LLM engine is configured, **When** the user generates notes with LLM mode enabled, **Then** the notes include contextual summaries, inferred action owners where discussed, and extracted decisions that may be implicit in the conversation.

2. **Given** an LLM is configured but unreachable, **When** notes generation begins, **Then** the system automatically falls back to basic (deterministic) mode and displays a clear message about the fallback.

3. **Given** an LLM generates notes, **When** the notes contain a Decision or Action Item, **Then** each item includes explicit timestamp references (format: @t=MM:SS-MM:SS) grounding it to the source transcript.

4. **Given** an LLM generates notes, **When** any claim cannot be traced to the transcript, **Then** it is marked with status "unclear" and includes a reason explaining the ambiguity.

---

### User Story 3 - Configure & Switch LLM Providers (Priority: P3)

A user wants to use their preferred LLM provider (OpenAI, enterprise API gateway, local Ollama instance) based on cost, privacy, or availability constraints.

**Why this priority**: Provides flexibility and privacy control, essential for enterprise users and privacy-conscious individuals. However, the feature works without any LLM, so this is an enhancement.

**Independent Test**: Can be tested by creating a config file with OpenAI settings, running notes generation, then changing config to Ollama, and verifying both backends work correctly with identical input.

**Acceptance Scenarios**:

1. **Given** no LLM configuration exists, **When** the user tries to enable LLM mode, **Then** the system provides clear guidance on how to configure an LLM engine (config file path, environment variables, CLI flags).

2. **Given** a user configures OpenAI credentials via environment variable, **When** they generate notes with LLM mode, **Then** the system uses OpenAI API and displays engine info (engine=openai, model=gpt-4.1-mini).

3. **Given** a user configures Ollama via config file, **When** they generate notes, **Then** the system connects to the Ollama local instance and uses the specified model.

4. **Given** multiple configuration sources exist (config file, env vars, CLI flags), **When** the user runs the tool, **Then** CLI flags override env vars, and env vars override config file values.

5. **Given** a required Ollama model is not pulled, **When** the user tries to use it, **Then** the system displays an actionable error message instructing them to run "ollama pull <model>".

---

### User Story 4 - Interactive Meeting Type Selection (Priority: P4)

When using the tool interactively in a terminal, a user wants to review and optionally override the auto-detected meeting type before notes generation begins.

**Why this priority**: Provides user control and transparency over automation, aligning with the "User Control Over Automation" principle. Less critical than auto-detection because many users will trust the automatic choice.

**Independent Test**: Can be tested by running the tool in a terminal (TTY), verifying an interactive menu appears showing detected type and alternatives, and confirming that arrow keys and Enter work for selection.

**Acceptance Scenarios**:

1. **Given** the tool is run in an interactive terminal (stdin is TTY) with auto-detection, **When** detection completes, **Then** a menu displays the recommended type, top 5 candidate types with confidence scores, and evidence phrases.

2. **Given** the interactive menu is displayed, **When** the user presses arrow keys (↑ ↓), **Then** the selection moves between meeting type options.

3. **Given** the user selects a meeting type and presses Enter, **When** notes generation begins, **Then** the selected type's template is used.

4. **Given** the user presses Esc in the menu, **When** the selection completes, **Then** the system uses the recommended (auto-detected) type.

5. **Given** the tool is run in a non-interactive context (piped input or --no-interactive flag), **When** detection completes, **Then** no prompt appears and the recommended type is used automatically.

---

### User Story 5 - Post-Process Transcripts for Quality (Priority: P5)

A user wants transcripts to be normalized and optionally repaired (fixing ASR errors) before classification and notes generation to improve accuracy and consistency.

**Why this priority**: Improves downstream quality significantly but is an enhancement rather than a core requirement. The tool works fine with raw transcripts.

**Independent Test**: Can be tested by processing a transcript with known ASR errors (e.g., "march tree" instead of "March 3"), enabling transcript repair, and verifying the output shows corrections with change logs.

**Acceptance Scenarios**:

1. **Given** a raw transcript with stuttering and repeated words, **When** normalization runs (deterministic), **Then** the output reduces stutters and stitches sentences across short pauses without changing meaning.

2. **Given** a raw transcript with ASR errors and LLM repair enabled, **When** repair runs, **Then** the output includes a changes log showing before/after text, timestamps, and reasons for each correction.

3. **Given** any transcript repair is applied, **When** notes generation uses the repaired text, **Then** the original timestamps and segment references remain intact and traceable.

---

### Edge Cases

- **What happens when a meeting has mixed types** (e.g., starts as status, transitions to planning)? System detects the dominant type or returns low confidence with multiple candidates. User can manually select or accept primary recommendation.

- **How does the system handle very short recordings** (<5 minutes)? Confidence may be low due to insufficient evidence. System defaults to "status" type (most general) and explains the limitation in output.

- **What if transcript is non-English?** Heuristic classification may degrade. LLM classifier (if enabled and multilingual) can still work. Otherwise, user should specify meeting type explicitly via --meeting-type flag.

- **What if LLM returns invalid JSON during classification?** System retries once with stricter prompt; if still invalid, falls back to heuristic classifier and logs the engine failure.

- **What if user specifies explicit meeting type but wrong template?** Explicit meeting type takes precedence (skips detection), but user can override template separately with --template flag.

- **What if no timestamps exist in transcript?** Notes generation proceeds but cannot include timestamp references. System marks this limitation in output.

- **What if config file exists but has invalid syntax?** System loads defaults, displays a warning about config syntax error with line number, and proceeds with env vars and CLI overrides.

## Requirements *(mandatory)*

### Functional Requirements

**Meeting Type Detection:**

- **FR-001**: System MUST detect one of nine meeting types: status, planning, design, demo, talk, incident, discovery, oneonone, brainstorm.
- **FR-002**: System MUST support auto-detection (default), explicit user selection via flag, and interactive terminal selection.
- **FR-003**: Detection MUST output a confidence score (0.0-1.0) and evidence phrases (keywords/patterns that led to the classification).
- **FR-004**: System MUST provide two detection modes: heuristic (default, deterministic, offline) and LLM (optional, requires configured engine).
- **FR-005**: Heuristic detection MUST use keyword/phrase dictionaries, bigrams/trigrams, and structural markers (question density, timeline vocab, estimate vocab).
- **FR-006**: LLM detection MUST accept a condensed transcript window (first 10-15 minutes + high-signal segments) and return structured JSON with type, confidence, evidence, and notes_focus fields.
- **FR-007**: When confidence is low (<0.5), system MUST display top 3 candidate meeting types with scores and allow user selection in interactive mode.

**Template-Based Notes Generation:**

- **FR-008**: System MUST map each meeting type to a predefined notes template (status.md, planning.md, design.md, etc.).
- **FR-009**: Every template MUST include invariant sections: Decisions, Action Items, Concrete Mentions (with timestamps), and Transcript References.
- **FR-010**: System MUST support two notes generation modes: basic (deterministic, time-bucketed summaries + frequent keywords) and LLM (richer extraction requiring configured engine).
- **FR-011**: LLM-generated notes MUST be grounded in transcript evidence - every Decision, Action Item, and Mention requires timestamp references (format: @t=MM:SS-MM:SS).
- **FR-012**: LLM prompts MUST include constraints: "Use ONLY the transcript; do not invent facts" and "If unclear, mark as unclear and cite timestamp."
- **FR-013**: System MUST mark ambiguous statements as "unclear" with status field and mandatory reason when LLM cannot confidently extract from transcript.

**LLM Engine Support:**

- **FR-014**: System MUST support multiple LLM backends via a unified interface: OpenAI-compatible HTTP API and Ollama local instance.
- **FR-015**: System MUST allow configuration via three sources with precedence order: CLI flags (highest) > environment variables > config file > built-in defaults.
- **FR-016**: LLM features MUST be opt-in; tool remains fully functional without any LLM configuration (degrades to deterministic modes).
- **FR-017**: System MUST handle missing credentials, unreachable engines, and invalid responses by falling back to deterministic behavior and displaying actionable guidance.
- **FR-018**: LLM requests MUST include timeout handling, exponential backoff retries (max 2 retries), and deterministic settings (temperature=0) when possible.

**Configuration & CLI:**

- **FR-019**: System MUST support CLI flags: --meeting-type (auto|status|planning|...), --template <name>, --classify (heuristic|llm|off), --llm (on|off), --llm-engine, --llm-model, --llm-base-url, --llm-timeout, --llm-retries, --no-interactive.
- **FR-020**: System MUST support environment variables prefixed with MNEMOFY_LLM_* for engine, model, base URL, timeout, retries.
- **FR-021**: Config file MUST be TOML format located at ~/.config/mnemofy/config.toml (macOS/Linux) or %APPDATA%\mnemofy\config.toml (Windows).
- **FR-022**: System MUST load config from file if exists, apply env var overrides, then apply CLI flag overrides.

**Transcript Post-Processing (Optional):**

- **FR-023**: System MUST support deterministic normalization: bounded stutter/filler reduction, sentence stitching across pauses ≤500ms, safe number/date normalization.
- **FR-024**: System MUST support optional LLM-based transcript repair that outputs repaired text plus a changes log (before/after/reason with timestamps).
- **FR-025**: Normalization and repair MUST preserve original meaning and never invent content.

**Output & Transparency:**

- **FR-026**: System MUST output detected meeting type, confidence, evidence terms, and selected template to stdout before generating notes.
- **FR-027**: System MUST create output files: *.notes.md (using selected template) and optionally *.meeting-type.json (detection metadata).
- **FR-028**: When LLM is used, system MUST display engine info: engine name, model, mode (notes|classify|both).
- **FR-029**: In verbose mode, system MUST log LLM request duration and response size.

**Non-Interactive Mode:**

- **FR-030**: System MUST support fully non-interactive execution via --no-interactive flag or when stdin is not a TTY.
- **FR-031**: In non-interactive mode, system MUST never prompt for user input and uses recommended/default values automatically.

### Key Entities

- **Meeting Type**: One of nine supported categories (status, planning, design, demo, talk, incident, discovery, oneonone, brainstorm). Has associated template, detection keywords, and structural patterns.

- **Notes Template**: Defines section structure for a meeting type. Contains ordered sections, required fields, optional fields, and extraction rules. Invariant sections across all templates: Decisions, Action Items, Concrete Mentions, Transcript References.

- **Transcript Segment**: Timestamped text chunk from ASR output. Contains start time, end time, speaker ID (optional), and text content. May be normalized or repaired before use.

- **Classification Result**: Output of meeting type detection. Contains detected type, confidence score (0.0-1.0), evidence phrases (list of keywords/patterns), optional secondary types, and detection engine used (heuristic or llm).

- **LLM Configuration**: Settings for LLM backend. Contains engine type (openai, ollama, openai_compat), model name, base URL, API key source (env var name), timeout, retry count, temperature.

- **Grounded Note Item**: A Decision, Action Item, or Mention extracted from transcript. Must contain the claim text, status (confirmed or unclear), reason if unclear, and one or more transcript references with timestamps.

- **Transcript Reference**: Links a note item to source transcript. Contains reference ID, start timestamp, end timestamp, speaker, and original text snippet.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System detects correct meeting type with confidence ≥0.6 for at least 90% of test meetings across all nine supported types.

- **SC-002**: Generated notes contain all required invariant sections (Decisions, Action Items, Mentions, Transcript References) for 100% of processed transcripts.

- **SC-003**: When LLM mode is enabled, 95% of extracted Decisions and Action Items include valid timestamp references linking to the source transcript.

- **SC-004**: System completes meeting type detection and notes generation within 2× the transcript duration (e.g., 30-minute recording processed in ≤60 minutes) for transcripts up to 2 hours.

- **SC-005**: Tool remains fully functional (transcription and basic notes generation) when no LLM is configured, with 100% success rate in offline/deterministic mode.

- **SC-006**: Configuration setup (adding LLM credentials and selecting engine) can be completed by a user in under 5 minutes following provided documentation.

- **SC-007**: In non-interactive mode (stdin not TTY or --no-interactive flag), system never prompts for input and completes automatically 100% of the time.

- **SC-008**: When LLM engine is unreachable or returns errors, system successfully falls back to deterministic mode within 30 seconds and continues processing.

- **SC-009**: Interactive meeting type selection menu responds to arrow key navigation and Enter/Esc commands with <200ms latency.
