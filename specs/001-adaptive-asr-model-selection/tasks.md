# Task Breakdown: Adaptive ASR Model Selection

**Feature ID**: 001 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This document breaks down the implementation into concrete tasks organized by user story. Each task includes clear acceptance criteria and dependencies. Tasks are designed for incremental delivery with testable milestones.

---

## Phase 0: Research & Foundation

### R-001: Research Resource Detection Libraries
**Phase**: Research  
**User Story**: Foundation  
**Priority**: P0 (Prerequisite)  
**Estimate**: 2 hours

**Description**: Evaluate `psutil` and platform-specific APIs for resource detection.

**Acceptance Criteria**:
- [X] Document psutil capabilities for CPU, RAM, GPU detection
- [X] Test psutil accuracy on macOS, Linux, Windows (if available)
- [X] Document GPU detection approach (CUDA, Metal, ROCm)
- [X] Identify limitations and fallback strategies
- [X] Create research.md with findings

**Dependencies**: None

---

### R-002: Research Rich TUI Components
**Phase**: Research  
**User Story**: US-002  
**Priority**: P0 (Prerequisite)  
**Estimate**: 1 hour

**Description**: Evaluate rich library's capabilities for interactive menus.

**Acceptance Criteria**:
- [X] Prototype arrow key navigation with rich
- [X] Test keyboard input handling
- [X] Document rendering approach for model list
- [X] Verify TTY detection methods
- [X] Add examples to research.md

**Dependencies**: None

---

## Phase 1: Core Resource Detection (US-001, US-003)

### T-001: Implement SystemResources Data Model
**Phase**: Implementation  
**User Story**: US-001  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Create `SystemResources` dataclass to represent hardware capabilities.

**Acceptance Criteria**:
- [X] Define SystemResources dataclass in `src/mnemofy/resources.py`
- [X] Include fields: cpu_cores, cpu_arch, total_ram_gb, available_ram_gb, has_gpu, gpu_type, available_vram_gb
- [X] Add type hints (Python 3.9+ compatible)
- [X] Add docstrings
- [X] Add `__str__` method for debugging

**Dependencies**: R-001

**Files**:
- `src/mnemofy/resources.py` (new)

---

### T-002: Implement CPU Detection
**Phase**: Implementation  
**User Story**: US-001  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Implement `get_cpu_info()` to detect CPU cores and architecture.

**Acceptance Criteria**:
- [X] Implement `get_cpu_info() -> tuple[int, str]`
- [X] Use psutil for core count
- [X] Use platform module for architecture
- [X] Handle detection failure gracefully (log warning, return conservative defaults)
- [X] Write unit tests with mocked psutil

**Dependencies**: T-001

**Files**:
- `src/mnemofy/resources.py` (modify)
- `tests/test_resources.py` (new)

---

### T-003: Implement Memory Detection
**Phase**: Implementation  
**User Story**: US-001  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Implement `get_memory_info()` to detect total and available RAM.

**Acceptance Criteria**:
- [X] Implement `get_memory_info() -> tuple[float, float]`
- [X] Use psutil.virtual_memory()
- [X] Convert to GB with 2 decimal precision
- [X] Handle detection failure gracefully
- [X] Write unit tests with mocked psutil
- [X] Test edge case: available > total (should never happen, but handle)

**Dependencies**: T-001

**Files**:
- `src/mnemofy/resources.py` (modify)
- `tests/test_resources.py` (modify)

---

### T-004: Implement GPU Detection
**Phase**: Implementation  
**User Story**: US-001  
**Priority**: P1  
**Estimate**: 4 hours

**Description**: Implement `get_gpu_info()` to detect GPU availability, type, and VRAM.

**Acceptance Criteria**:
- [X] Implement `get_gpu_info() -> tuple[bool, Optional[str], Optional[float]]`
- [X] Detect CUDA (nvidia-smi or pynvml)
- [X] Detect Metal (macOS platform check)
- [X] Detect ROCm (AMD, linux platform check)
- [X] Return VRAM if available (CUDA only initially)
- [X] Graceful fallback to (False, None, None) if detection fails
- [X] Write unit tests for all platforms
- [X] Document known limitations

**Dependencies**: T-001

**Files**:
- `src/mnemofy/resources.py` (modify)
- `tests/test_resources.py` (modify)

**Notes**: Metal and ROCm VRAM detection may be limited; log warnings appropriately.

---

### T-005: Implement Main Resource Detection Entry Point
**Phase**: Implementation  
**User Story**: US-001  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Implement `detect_system_resources()` orchestration function.

**Acceptance Criteria**:
- [X] Implement `detect_system_resources() -> SystemResources`
- [X] Call get_cpu_info(), get_memory_info(), get_gpu_info()
- [X] Construct SystemResources instance
- [X] Log detected resources at INFO level
- [X] Handle partial detection failures (continue with defaults)
- [X] Write integration test

**Dependencies**: T-002, T-003, T-004

**Files**:
- `src/mnemofy/resources.py` (modify)
- `tests/test_resources.py` (modify)

---

## Phase 2: Model Selection Logic (US-001, US-003)

### T-006: Define ModelSpec Database
**Phase**: Implementation  
**User Story**: US-001  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Create ModelSpec dataclass and hardcoded model database.

**Acceptance Criteria**:
- [X] Define ModelSpec dataclass in `src/mnemofy/model_selector.py`
- [X] Include fields: name, min_ram_gb, min_vram_gb, speed_rating, quality_rating, description
- [X] Create MODEL_SPECS dict with 5 models (tiny, base, small, medium, large-v3)
- [X] Populate accurate RAM/VRAM requirements (research from faster-whisper docs)
- [X] Add docstrings explaining rating scales (1-5)
- [X] Write tests asserting MODEL_SPECS structure is valid

**Dependencies**: R-001

**Files**:
- `src/mnemofy/model_selector.py` (new)
- `tests/test_model_selector.py` (new)

**Research Required**: Confirm faster-whisper memory requirements for each model.

---

### T-007: Implement Model Filtering Logic
**Phase**: Implementation  
**User Story**: US-001  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Implement `filter_compatible_models()` to find models that fit in available resources.

**Acceptance Criteria**:
- [X] Implement `filter_compatible_models(resources, use_gpu) -> list[ModelSpec]`
- [X] Filter by min_ram_gb <= resources.available_ram_gb
- [X] If use_gpu=True and has_gpu, filter by min_vram_gb <= available_vram_gb
- [X] Return sorted list (quality desc, speed desc)
- [X] Handle edge case: no compatible models (return empty list)
- [X] Write tests for various resource scenarios (low RAM, high RAM, GPU, no GPU)

**Dependencies**: T-005, T-006

**Files**:
- `src/mnemofy/model_selector.py` (modify)
- `tests/test_model_selector.py` (modify)

---

### T-008: Implement Recommendation Algorithm
**Phase**: Implementation  
**User Story**: US-001  
**Priority**: P1  
**Estimate**: 3 hours

**Description**: Implement `recommend_model()` to select best model with reasoning.

**Acceptance Criteria**:
- [X] Implement `recommend_model(resources, use_gpu) -> tuple[ModelSpec, str]`
- [X] Call filter_compatible_models()
- [X] Select highest quality compatible model
- [X] Generate reasoning string (e.g., "8GB RAM available, GPU detected → medium model")
- [X] Raise error if no compatible models (SystemResourceError or similar)
- [X] Write tests for edge cases:
  - [X] No compatible models → error
  - [X] Only one model fits → return with reasoning
  - [X] Multiple models fit → highest quality selected
  - [X] GPU vs CPU mode differences

**Dependencies**: T-007

**Files**:
- `src/mnemofy/model_selector.py` (modify)
- `tests/test_model_selector.py` (modify)

---

### T-009: Implement Model Comparison Table Generator
**Phase**: Implementation  
**User Story**: US-005  
**Priority**: P3  
**Estimate**: 2 hours

**Description**: Implement `get_model_table()` to display model comparison.

**Acceptance Criteria**:
- [X] Implement `get_model_table(resources, recommended) -> str`
- [X] Use rich.table to format output
- [X] Columns: Model, Speed, Quality, RAM Req, VRAM Req, Status
- [X] Status: ✓ Recommended, ✓ Compatible, ⚠ Risky (near limit), ✗ Incompatible
- [X] Highlight recommended model
- [X] Return formatted string suitable for console.print()
- [X] Write test asserting table format is valid

**Dependencies**: T-006, T-007

**Files**:
- `src/mnemofy/model_selector.py` (modify)
- `tests/test_model_selector.py` (modify)

---

## Phase 3: Interactive TUI (US-002)

### T-010: Implement TTY Detection
**Phase**: Implementation  
**User Story**: US-002  
**Priority**: P2  
**Estimate**: 1 hour

**Description**: Implement `is_interactive_environment()` to check for TTY.

**Acceptance Criteria**:
- [X] Implement `is_interactive_environment() -> bool` in `src/mnemofy/tui/model_menu.py`
- [X] Check sys.stdin.isatty() and sys.stdout.isatty()
- [X] Return True only if both are TTY
- [X] Write tests with mocked stdin/stdout
- [X] Document when this returns False (CI, pipes, redirects)

**Dependencies**: None

**Files**:
- `src/mnemofy/tui/__init__.py` (new, empty)
- `src/mnemofy/tui/model_menu.py` (new)
- `tests/test_tui_model_menu.py` (new)

---

### T-011: Implement ModelMenu Class
**Phase**: Implementation  
**User Story**: US-002  
**Priority**: P2  
**Estimate**: 4 hours

**Description**: Create interactive menu using rich library.

**Acceptance Criteria**:
- [X] Implement ModelMenu class in `src/mnemofy/tui/model_menu.py`
- [X] Constructor: `__init__(models, recommended, resources)`
- [X] Method: `show() -> Optional[ModelSpec]`
- [X] Render model list with rich.console
- [X] Highlight recommended model (different color/icon)
- [X] Show warnings for risky models (low margin)
- [X] Handle arrow key navigation (↑/↓)
- [X] Handle Enter key (confirm selection)
- [X] Handle Esc key (cancel, return None)
- [X] Handle Ctrl+C gracefully (return None)
- [X] Write tests with mocked keyboard input

**Dependencies**: T-009, T-010, R-002

**Files**:
- `src/mnemofy/tui/model_menu.py` (modify)
- `tests/test_tui_model_menu.py` (modify)

**Notes**: Consider using rich's built-in `Prompt.ask()` with choices if arrow key handling is complex.

---

### T-012: Add Model Details Display on Selection
**Phase**: Implementation  
**User Story**: US-002  
**Priority**: P2  
**Estimate**: 2 hours

**Description**: Show detailed model info when hovering/selecting in menu.

**Acceptance Criteria**:
- [X] Display model description, speed rating, quality rating
- [X] Display RAM requirement vs available
- [X] Display VRAM requirement vs available (if GPU mode)
- [X] Update details panel as user navigates
- [X] Use rich.panel for formatting
- [X] Write test asserting details render correctly

**Dependencies**: T-011

**Files**:
- `src/mnemofy/tui/model_menu.py` (modify)
- `tests/test_tui_model_menu.py` (modify)

---

## Phase 4: CLI Integration (US-001, US-002, US-003, US-004, US-005)

### T-013: Add New CLI Flags
**Phase**: Implementation  
**User Story**: US-003, US-004, US-005  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Add `--model`, `--auto`, `--no-gpu`, `--list-models` flags to CLI.

**Acceptance Criteria**:
- [ ] Add flags to `transcribe` command in `src/mnemofy/cli.py`
- [ ] Update `--model` help text to mention auto-detection
- [ ] Add `--auto` flag (bool, default False)
- [ ] Add `--no-gpu` flag (bool, default False)
- [ ] Add `--list-models` flag (bool, default False)
- [ ] Ensure flags are mutually compatible (--list-models exits early)
- [ ] Update `mnemofy transcribe --help` output

**Dependencies**: None (parallel with other tasks)

**Files**:
- `src/mnemofy/cli.py` (modify)

---

### T-014: Implement --list-models Command
**Phase**: Implementation  
**User Story**: US-005  
**Priority**: P3  
**Estimate**: 1 hour

**Description**: Display model table and exit when `--list-models` is passed.

**Acceptance Criteria**:
- [ ] Check for --list-models flag at start of transcribe command
- [ ] Call detect_system_resources()
- [ ] Call get_model_table() with detected resources
- [ ] Print table to console
- [ ] Exit with code 0 (success)
- [ ] Write integration test

**Dependencies**: T-005, T-009, T-013

**Files**:
- `src/mnemofy/cli.py` (modify)
- `tests/test_cli_integration.py` (new)

---

### T-015: Integrate Explicit Model Override Path
**Phase**: Implementation  
**User Story**: US-003  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Implement `--model <name>` explicit override logic.

**Acceptance Criteria**:
- [ ] Check if --model flag is provided
- [ ] If provided, skip all auto-detection and selection
- [ ] Pass model name directly to Transcriber
- [ ] Log INFO message: "Using explicit model: <name>"
- [ ] Validate model name is in MODEL_SPECS (warn if not, but allow)
- [ ] Write integration test

**Dependencies**: T-006, T-013

**Files**:
- `src/mnemofy/cli.py` (modify)
- `tests/test_cli_integration.py` (modify)

---

### T-016: Integrate Auto-Selection Path
**Phase**: Implementation  
**User Story**: US-001, US-004  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Implement auto-selection (headless mode) logic.

**Acceptance Criteria**:
- [ ] If --model not provided:
  - [ ] Call detect_system_resources()
  - [ ] Call recommend_model(resources, use_gpu=not no_gpu)
  - [ ] If --auto or not TTY:
    - [ ] Auto-select recommended model
    - [ ] Print INFO message: "Auto-selected: <model> (<reasoning>)"
  - [ ] Else: proceed to interactive selection (next task)
- [ ] Write integration tests for:
  - [ ] --auto flag forces auto-selection
  - [ ] Non-TTY environment forces auto-selection
  - [ ] Reasoning message is displayed

**Dependencies**: T-005, T-008, T-013, T-015

**Files**:
- `src/mnemofy/cli.py` (modify)
- `tests/test_cli_integration.py` (modify)

---

### T-017: Integrate Interactive Selection Path
**Phase**: Implementation  
**User Story**: US-002  
**Priority**: P2  
**Estimate**: 2 hours

**Description**: Implement interactive menu display in TTY environments.

**Acceptance Criteria**:
- [ ] If TTY and not --auto:
  - [ ] Call filter_compatible_models() to get full list
  - [ ] Create ModelMenu instance
  - [ ] Call menu.show()
  - [ ] If user cancels (Esc, Ctrl+C): raise typer.Abort()
  - [ ] If user selects model: use selected model
  - [ ] Log INFO message: "Selected model: <name>"
- [ ] Write integration test with mocked TTY and keyboard input

**Dependencies**: T-006, T-007, T-011, T-016

**Files**:
- `src/mnemofy/cli.py` (modify)
- `tests/test_cli_integration.py` (modify)

---

### T-018: Handle Resource Detection Failures
**Phase**: Implementation  
**User Story**: US-001  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Implement graceful error handling for detection failures.

**Acceptance Criteria**:
- [ ] If detect_system_resources() fails:
  - [ ] Log ERROR message with details
  - [ ] Fall back to conservative default (e.g., "base" model)
  - [ ] Display warning to user
  - [ ] Continue execution (don't crash)
- [ ] If recommend_model() returns no compatible models:
  - [ ] Display clear error message: "No Whisper model fits in available RAM (XGB). Try freeing memory or use --model tiny"
  - [ ] Exit with error code 1
- [ ] Write integration tests for both scenarios

**Dependencies**: T-005, T-008, T-016

**Files**:
- `src/mnemofy/cli.py` (modify)
- `tests/test_cli_integration.py` (modify)

---

## Phase 5: Testing & Validation

### T-019: Write Comprehensive Unit Tests
**Phase**: Testing  
**User Story**: All  
**Priority**: P1  
**Estimate**: 4 hours

**Description**: Ensure 90%+ code coverage for new modules.

**Acceptance Criteria**:
- [ ] test_resources.py: 90%+ coverage
  - [ ] Test all platforms (mock psutil for macOS, Linux, Windows)
  - [ ] Test GPU detection (CUDA, Metal, none)
  - [ ] Test detection failures and graceful degradation
- [ ] test_model_selector.py: 90%+ coverage
  - [ ] Test filtering with various RAM/VRAM scenarios
  - [ ] Test recommendation algorithm edge cases
  - [ ] Test table generation
- [ ] test_tui_model_menu.py: 80%+ coverage
  - [ ] Test navigation, selection, cancellation
  - [ ] Mock keyboard input
- [ ] Run pytest with --cov flag, verify coverage

**Dependencies**: All implementation tasks

**Files**:
- `tests/test_resources.py` (modify)
- `tests/test_model_selector.py` (modify)
- `tests/test_tui_model_menu.py` (modify)

---

### T-020: Write Integration Tests
**Phase**: Testing  
**User Story**: All  
**Priority**: P1  
**Estimate**: 3 hours

**Description**: Test end-to-end CLI workflows.

**Acceptance Criteria**:
- [ ] Test: `mnemofy transcribe file.mp4 --model tiny` → uses tiny, no detection
- [ ] Test: `mnemofy transcribe file.mp4 --auto` → auto-selects, no menu
- [ ] Test: `mnemofy transcribe file.mp4` (TTY) → shows menu
- [ ] Test: `mnemofy transcribe file.mp4` (non-TTY) → auto-selects
- [ ] Test: `mnemofy transcribe --list-models` → displays table, exits
- [ ] Test: `mnemofy transcribe file.mp4 --no-gpu` → forces CPU mode
- [ ] All tests use mocked transcription (don't run real Whisper)

**Dependencies**: T-014, T-015, T-016, T-017, T-018

**Files**:
- `tests/test_cli_integration.py` (modify)

---

### T-021: Manual Testing on Diverse Hardware
**Phase**: Testing  
**User Story**: US-001  
**Priority**: P1  
**Estimate**: 4 hours

**Description**: Test on multiple hardware configurations.

**Acceptance Criteria**:
- [ ] Test on low RAM system (4GB or less) → tiny/base model recommended
- [ ] Test on medium RAM system (8GB) → small/medium recommended
- [ ] Test on high RAM system (16GB+) → large-v3 recommended
- [ ] Test on NVIDIA GPU system → GPU mode enabled, VRAM considered
- [ ] Test on macOS (Metal) → Metal detection works
- [ ] Test on headless/CI environment → auto-selection works
- [ ] Document results in manual testing log

**Dependencies**: All implementation tasks

---

### T-022: Edge Case Testing
**Phase**: Testing  
**User Story**: All  
**Priority**: P2  
**Estimate**: 2 hours

**Description**: Test edge cases and error scenarios.

**Acceptance Criteria**:
- [ ] Test: Nearly full RAM (90%+ used) → only tiny model fits
- [ ] Test: Insufficient RAM for any model → clear error message
- [ ] Test: GPU detection fails mid-execution → falls back to CPU
- [ ] Test: Ctrl+C during interactive menu → exits cleanly
- [ ] Test: Invalid --model name → warning but continues (or errors if strict)
- [ ] Test: Extremely slow disk (mock) → resource detection timeout handling
- [ ] Document edge case behavior

**Dependencies**: All implementation tasks

---

## Phase 6: Documentation

### T-023: Update README.md
**Phase**: Documentation  
**User Story**: All  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Add comprehensive documentation for new feature.

**Acceptance Criteria**:
- [ ] Add "Automatic Model Selection" section
- [ ] Document default behavior (auto-detection + interactive)
- [ ] Document --model flag (explicit override)
- [ ] Document --auto flag (headless mode)
- [ ] Document --no-gpu flag
- [ ] Document --list-models flag
- [ ] Provide 3-5 usage examples
- [ ] Add troubleshooting section (GPU detection issues, low RAM)

**Dependencies**: All implementation tasks

**Files**:
- `README.md` (modify)

---

### T-024: Add Inline Documentation
**Phase**: Documentation  
**User Story**: All  
**Priority**: P2  
**Estimate**: 1 hour

**Description**: Ensure all new code has docstrings and comments.

**Acceptance Criteria**:
- [ ] All public functions have docstrings
- [ ] All classes have docstrings
- [ ] Complex algorithms have inline comments
- [ ] pyproject.toml updated if new dependencies added (psutil)
- [ ] Type hints present on all function signatures

**Dependencies**: All implementation tasks

**Files**:
- `src/mnemofy/resources.py` (modify)
- `src/mnemofy/model_selector.py` (modify)
- `src/mnemofy/tui/model_menu.py` (modify)

---

### T-025: Create Examples and Tutorials
**Phase**: Documentation  
**User Story**: All  
**Priority**: P3  
**Estimate**: 2 hours

**Description**: Create usage examples and tutorials.

**Acceptance Criteria**:
- [ ] Add example to README showing interactive selection
- [ ] Add example showing --auto for CI/CD
- [ ] Add example showing --list-models output
- [ ] Add screenshot/GIF of interactive menu (optional)
- [ ] Document model selection algorithm logic

**Dependencies**: T-023

**Files**:
- `README.md` (modify)
- `docs/` (optional: create examples/ directory)

---

## Phase 7: Release

### T-026: Bump Version and Prepare Changelog
**Phase**: Release  
**User Story**: All  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Update version and document changes.

**Acceptance Criteria**:
- [ ] Bump version to 0.7.0 (minor release, new feature)
- [ ] Update pyproject.toml
- [ ] Add CHANGELOG.md entry (or update existing)
- [ ] Document breaking changes (none expected)
- [ ] Document new dependencies (psutil)

**Dependencies**: All testing tasks

**Files**:
- `pyproject.toml` (modify)
- `CHANGELOG.md` (create or modify)

---

### T-027: Final Pre-Release Testing
**Phase**: Release  
**User Story**: All  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Final validation before release.

**Acceptance Criteria**:
- [ ] Run full test suite (pytest)
- [ ] Test installation from source (`pip install -e .`)
- [ ] Test CLI on real audio file (end-to-end)
- [ ] Verify --model, --auto, --list-models all work
- [ ] Check for regressions in existing functionality
- [ ] Review all documentation for accuracy

**Dependencies**: T-026

---

### T-028: Publish to PyPI
**Phase**: Release  
**User Story**: All  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Publish mnemofy v0.7.0 to PyPI.

**Acceptance Criteria**:
- [ ] Build distribution (`python -m build`)
- [ ] Upload to PyPI (`twine upload dist/*`)
- [ ] Verify package installs from PyPI
- [ ] Tag release in git (v0.7.0)
- [ ] Push tag to remote

**Dependencies**: T-027

---

## Summary

**Total Tasks**: 28  
**Estimated Time**: ~55 hours  

**Critical Path**:
1. Research (R-001, R-002) → 3h
2. Resource Detection (T-001 to T-005) → 10h
3. Model Selection (T-006 to T-009) → 9h
4. CLI Integration (T-013, T-015, T-016, T-018) → 6h
5. Testing (T-019, T-020) → 7h
6. Documentation (T-023, T-024) → 3h
7. Release (T-026, T-027, T-028) → 4h

**Total Critical Path**: ~42 hours

**Nice-to-Have** (can be deferred):
- T-010 to T-012 (TUI, P2)
- T-022 (Edge case testing)
- T-025 (Examples)

**Recommended Approach**: Start with critical path (P1 tasks), then add TUI (P2), then polish with P3 tasks.
