# Feature Specification: Adaptive ASR Model Selection

**Feature Branch**: `001-adaptive-asr-model-selection`  
**Created**: 2026-02-10  
**Status**: Draft  
**Input**: User description: "Automatic and interactive selection of speech-to-text (ASR) model based on available system resources"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Model Recommendation (Priority: P1) 🎯 MVP

A user runs mnemofy without specifying a model, and the system automatically detects available resources (RAM, VRAM, CPU) and recommends the best Whisper model that fits their hardware constraints.

**Why this priority**: Core value proposition - enables users to get started without understanding hardware constraints. This alone delivers immediate value.

**Independent Test**: Can be fully tested by running `mnemofy transcribe meeting.mp4` (without `--model`) and verifying the system recommends an appropriate model based on detected resources.

**Acceptance Scenarios**:

1. **Given** 16GB RAM available, **When** user runs `mnemofy transcribe file.mp4`, **Then** system recommends `large-v3` model with explanation
2. **Given** 4GB RAM available, **When** user runs `mnemofy transcribe file.mp4`, **Then** system recommends `medium` model with resource warning
3. **Given** 1.5GB RAM available, **When** user runs `mnemofy transcribe file.mp4`, **Then** system recommends `base` model with clear reasoning
4. **Given** GPU with 6GB VRAM available, **When** user runs without `--no-gpu`, **Then** system detects GPU and recommends GPU-accelerated model
5. **Given** insufficient RAM (<1GB), **When** user runs transcribe command, **Then** system displays clear error message before execution

---

### User Story 2 - Interactive Model Selection (Priority: P2)

After seeing the recommendation, users can interactively select a different model using keyboard navigation (arrow keys) if they want to override the automatic choice.

**Why this priority**: Provides user control without requiring CLI expertise. Essential for user agency (Constitution Principle 1).

**Independent Test**: Can be tested by running `mnemofy transcribe file.mp4`, observing the recommendation, then using arrow keys to select a different model and pressing Enter.

**Acceptance Scenarios**:

1. **Given** system recommends `medium`, **When** user presses ↓ arrow, **Then** selector highlights `small` model
2. **Given** model selector is displayed, **When** user presses Enter, **Then** selected model is confirmed and transcription begins
3. **Given** model selector is displayed, **When** user presses Esc, **Then** operation is cancelled
4. **Given** recommended model is highlighted, **When** user navigates to risky model (insufficient RAM), **Then** warning indicator is displayed
5. **Given** interactive mode, **When** user selects any model, **Then** their choice is explicitly confirmed before proceeding

---

### User Story 3 - Explicit Model Override (Priority: P1)

Power users can bypass automatic detection entirely by specifying `--model <name>` flag, maintaining full manual control.

**Why this priority**: Critical for maintaining user agency. Users must always be able to override automation (Constitution Principle 1).

**Independent Test**: Can be tested by running `mnemofy transcribe file.mp4 --model tiny` and verifying that automatic detection is skipped and tiny model is used directly.

**Acceptance Scenarios**:

1. **Given** `--model tiny` flag provided, **When** command executes, **Then** no resource detection or interactive prompt occurs
2. **Given** `--model large-v3` on low-RAM system, **When** command executes, **Then** system warns but respects user choice
3. **Given** explicit model specified, **When** insufficient resources detected, **Then** clear warning is shown but user can proceed

---

### User Story 4 - Automated Headless Mode (Priority: P2)

In CI/CD or headless environments, the system automatically selects the recommended model without prompting, using `--auto` flag or detecting non-interactive environment.

**Why this priority**: Enables automation and scripting. Required for CI/CD integration and unattended operation.

**Independent Test**: Can be tested by running `mnemofy transcribe file.mp4 --auto` or in a non-TTY environment and verifying no interactive prompt appears.

**Acceptance Scenarios**:

1. **Given** `--auto` flag provided, **When** command executes, **Then** recommended model is selected without prompting
2. **Given** non-interactive environment (no TTY), **When** command executes, **Then** system behaves as if `--auto` was specified
3. **Given** CI environment variable detected, **When** transcription runs, **Then** automatic selection occurs without user input
4. **Given** `--auto` in headless mode, **When** no suitable model found, **Then** graceful error with actionable message is shown

---

### User Story 5 - Model Information Display (Priority: P3)

Users can view detailed information about all available models using `--list-models` flag without executing transcription.

**Why this priority**: Educational feature that helps users understand options. Lower priority but valuable for transparency (Constitution Principle 3).

**Independent Test**: Can be tested by running `mnemofy transcribe --list-models` and verifying a formatted table is displayed with model characteristics.

**Acceptance Scenarios**:

1. **Given** `--list-models` flag, **When** command executes, **Then** formatted table shows all models with RAM/VRAM requirements, speed, and quality ratings
2. **Given** model table displayed, **When** user views output, **Then** recommended model for current system is highlighted
3. **Given** `--list-models`, **When** GPU not available, **Then** VRAM column shows "N/A" or is omitted
4. **Given** `--list-models` with `--no-gpu`, **When** command executes, **Then** only CPU models are shown or GPU models are marked as unavailable

---

### Edge Cases

- What happens when no model fits available memory (< 1GB RAM)?
  - System displays error: "Error: no transcription model fits into available memory" with actionable advice (close other apps, use smaller audio file, or upgrade RAM)
  
- How does system handle GPU detection failure?
  - Falls back to CPU-only mode gracefully, logs warning, continues with CPU recommendations
  
- What if user Ctrl+C during interactive selection?
  - Operation is cleanly cancelled with "Operation cancelled by user" message, no partial state
  
- What if resource detection fails (permission issues, unsupported OS)?
  - System logs warning, falls back to conservative defaults (base or small model), explains limitation to user
  
- What if faster-whisper model files are not cached?
  - First use triggers download with progress indicator, user is warned about download size and prompted to continue

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect available system RAM before recommending a model
- **FR-002**: System MUST detect GPU availability and VRAM when GPU is present
- **FR-003**: System MUST filter models that exceed available memory resources
- **FR-004**: System MUST recommend the highest quality model that fits available resources
- **FR-005**: System MUST display interactive model selector with keyboard navigation when not in headless mode
- **FR-006**: System MUST support ↑/↓ arrow keys for model selection navigation
- **FR-007**: System MUST support Enter key to confirm model selection
- **FR-008**: System MUST support Esc key to cancel operation
- **FR-009**: System MUST respect `--model <name>` flag and skip auto-detection when provided
- **FR-010**: System MUST support `--auto` flag for non-interactive automatic selection
- **FR-011**: System MUST detect non-interactive environments (no TTY) and behave as headless
- **FR-012**: System MUST support `--no-gpu` flag to ignore GPU even if present
- **FR-013**: System MUST support `--list-models` flag to display model information table
- **FR-014**: System MUST display resource requirements (RAM, VRAM) for each model
- **FR-015**: System MUST show speed and quality indicators for each model
- **FR-016**: System MUST display warnings for models that may not fit in available memory
- **FR-017**: System MUST explain why a particular model is recommended (transparency requirement)
- **FR-018**: System MUST fail gracefully with actionable error when no model fits memory
- **FR-019**: System MUST preserve user's model choice and honor it over automatic selection
- **FR-020**: System MUST log resource detection results for debugging purposes

### Key Entities

- **SystemResources**: Detected hardware capabilities including CPU cores, total RAM, available RAM, GPU presence, VRAM
- **ModelSpec**: Model definition including name, minimum RAM, minimum VRAM, speed rating, quality rating, use case description
- **ModelRecommendation**: Result of recommendation algorithm including selected model, reasoning, resource fit analysis, warnings

### Non-Functional Requirements

- **NFR-001**: Resource detection MUST complete in under 1 second
- **NFR-002**: Interactive selector MUST respond to keyboard input within 50ms
- **NFR-003**: Model information table MUST fit in standard 80-column terminal
- **NFR-004**: Error messages MUST be actionable and explain next steps
- **NFR-005**: Recommendation reasoning MUST be explainable in one paragraph

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of users on standard hardware (2GB+ RAM) receive appropriate model recommendation without manual intervention
- **SC-002**: Users can select preferred model using keyboard navigation in under 5 seconds
- **SC-003**: Zero crashes due to out-of-memory errors when using recommended model
- **SC-004**: 100% of headless/CI environments successfully auto-select model without human input
- **SC-005**: Users understand why a model was recommended (measured by absence of confusion-related support tickets)
- **SC-006**: Power users can override with `--model` flag and bypass detection in 100% of cases

## Design Principles Alignment

This feature aligns with mnemofy constitution principles:

1. **User Control Over Automation**: Interactive selection preserves user agency; `--model` flag provides complete override
2. **Safe-by-Default Execution**: Pre-flight resource checks prevent OOM crashes
3. **Transparency Over Magic**: Recommendation reasoning is always displayed
4. **Progressive Disclosure**: Beginners get automatic recommendations; experts get full manual control
5. **Performance Is a Feature**: Optimized resource detection ensures minimal overhead

## Clarifications

### Session 2026-02-10

- Q: How should Metal GPU be handled on macOS? → A: Treat Metal as GPU-eligible. Base fit checks on RAM only (available_ram_gb), ignore VRAM since Metal uses unified memory. This counts as GPU mode for feature purposes.
- Q: When system resource detection fails, which fallback model should we use? → A: Use `base` model (1.5GB RAM requirement). Provides balanced quality while staying conservative. Log warning explaining fallback behavior.
- Q: When system resource detection fails, which fallback model should we use? → A: Use `base` model (1.5GB RAM requirement). Provides balanced quality while staying conservative. Log warning explaining fallback behavior.
- Q: When recommending a model based on available RAM, should we apply a safety margin to prevent OOM crashes? → A: Use 85% of available RAM (0.75GB buffer on 5GB system). Balances OOM crash prevention with maximizing usable model flexibility. Aligns with SC-003 (zero OOM crashes) and Safe-by-Default principle.
- Q: In interactive selection mode (--auto flag without immediate choice), should the menu have a timeout, or should we wait indefinitely for user input? → A: Use context-aware detection. Timeout in non-interactive (piped/CI) scenarios, wait indefinitely when interactive terminal detected. Respects user control in shells while preventing CI hangs. Aligns with User Control and Safe-by-Default principles.
- Q: Should model recommendations be cached per system, or should we perform fresh resource detection on each run? → A: Use hybrid approach with 1-hour TTL cache. Provides performance benefit for typical workflow (multiple transcriptions in same session) while respecting system state changes within reasonable timeframe. Balances Performance Is a Feature with Safe-by-Default principles.
