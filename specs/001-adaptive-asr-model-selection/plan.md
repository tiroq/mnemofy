# Implementation Plan: Adaptive ASR Model Selection

**Branch**: `001-adaptive-asr-model-selection` | **Date**: 2026-02-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-adaptive-asr-model-selection/spec.md`

## Summary

Enable mnemofy users to automatically select appropriate Whisper model based on available system resources (RAM, VRAM, CPU). Provides automatic recommendation with interactive override, manual `--model` flag bypass, and headless/CI support. Implements safe-by-default resource detection with fallback to `base` model on detection failure, 85% RAM safety margin to prevent OOM, context-aware timeout handling, and 1-hour TTL caching for performance.

**Key Decisions** (from clarification sprint 2026-02-10):
- Metal GPU on macOS: Treat as GPU-eligible, fit checks on RAM only (unified memory)
- Detection failure fallback: Use `base` model (1.5GB requirement)
- RAM safety margin: 85% available (0.75GB buffer on 5GB system)
- Interactive timeout: Context-aware (timeout in non-interactive, wait in TTY)
- Caching strategy: 1-hour TTL hybrid caching

## Technical Context

**Language/Version**: Python 3.9-3.13 (primary: 3.12)  
**Primary Dependencies**: 
  - `faster-whisper` 0.9+ (ASR engine with CTranslate2)
  - `typer` 0.9+ (CLI framework)
  - `rich` 13.0+ (TUI, prompts, formatting)
  - `pydantic` 2.0+ (data validation)
  - `psutil` 5.9+ (system resource detection)
  - `readchar` 4.0+ (keyboard input handling)

**Storage**: JSON cache file at `~/.mnemofy/cache/model-recommendation.json` with 1-hour TTL  
**Testing**: pytest with mocking for resource detection, TUI, caching  
**Target Platform**: macOS, Linux, Windows (resource detection varies by OS)  
**Project Type**: Python package (single project, CLI-focused)  
**Performance Goals**: 
  - Resource detection: <200ms per run (cached: <10ms within TTL)
  - Interactive menu navigation: <5 seconds per interaction (SC-002)
  - Cold startup: <1s (with detection); warm (cached): <100ms
  
**Constraints**:
  - KMP_DUPLICATE_LIB_OK=TRUE required on macOS for OpenMP conflicts
  - No external GPU management tools (nvidia-smi only for initial detection)
  - Maintain 100% backward compatibility with existing `--model` flag
  - Support headless/CI environments without blocking
  
**Scale/Scope**: ~55 hours implementation; ~42 hour critical path; 7 phases with 28 tasks

## Constitution Check

✅ **GATE: PASSED** - Feature aligns with all 10 mnemofy constitution principles:

1. **User Control Over Automation** ✅ – Interactive selection preserves agency; `--model` flag provides complete override
2. **Safe-by-Default Execution** ✅ – Pre-flight resource checks prevent OOM crashes (SC-003); 85% safety margin implemented
3. **Transparency Over Magic** ✅ – Recommendation reasoning always displayed; fallback explains why `base` was selected
4. **Progressive Disclosure** ✅ – Begin users get auto-recommendation; experts get full manual control via `--model`
5. **Performance Is a Feature** ✅ – 1-hour TTL caching minimizes overhead; resource detection <200ms
6. **Stable & Predictable** ✅ – 100% backward compatible; existing `--model` flag unaffected
7. **Auditable & Debuggable** ✅ – All decisions logged; cache timestamps and detection failures traceable
8. **Minimal Dependencies** ✅ – Only psutil/readchar added (lightweight, well-maintained)
9. **Composition Over Monolith** ✅ – Resource detection, recommendation, UI, CLI are separate modules
10. **Principle-First Design** ✅ – Design decisions pre-validated against constitution

## Project Structure

### Documentation (this feature)

```text
specs/001-adaptive-asr-model-selection/
├── spec.md              # Feature specification with 5 user stories, requirements, success criteria
├── plan.md              # This file - implementation strategy
├── tasks.md             # Detailed task breakdown (28 tasks, 7 phases)
├── research.md          # Technical research - resource detection, GPU handling, model memory
├── data-model.md        # Entity definitions (SystemResources, ModelSpec, ModelRecommendation)
├── README.md            # Quick navigation guide
└── contracts/
    └── cli-interface.md # CLI contract with --auto, --no-gpu, --list-models flags
```

### Source Code (repository root)

```text
src/mnemofy/
├── model_selector/                    # NEW: Core adaptive selection module
│   ├── __init__.py
│   ├── resource_detection.py           # System resource detection (psutil wrapper)
│   ├── recommendation.py               # Model selection algorithm
│   ├── tui.py                          # Terminal UI for interactive selection (rich, readchar)
│   ├── cache.py                        # 1-hour TTL caching with system fingerprint
│   └── models.py                       # Pydantic models (SystemResources, ModelRecommendation)
│
├── cli.py                             # MODIFIED: Add --auto, --no-gpu, --list-models flags
├── transcriber.py                     # MODIFIED: Integration point for auto-selection
├── audio.py                           # (unchanged)
└── notes.py                           # (unchanged)

tests/
├── test_model_selector.py             # NEW: Unit tests for resource detection, recommendation, caching
├── test_tui.py                        # NEW: TUI interaction tests (mocked input)
├── test_cli_flags.py                  # NEW: CLI integration tests
├── test_transcriber.py                # MODIFIED: Test transcriber with auto-selection
├── test_audio.py                      # (unchanged)
└── test_notes.py                      # (unchanged)
```

**Structure Decision**: Single Python package (Option 1) with new `model_selector` submodule. Maintains existing structure while cleanly encapsulating new functionality. CLI integration through modified `cli.py` entry point.

## Architecture & Design

### Module: `model_selector.resource_detection`
Detects available system resources using psutil:
- **RAM Detection**: `psutil.virtual_memory().available` 
- **GPU Detection**: 
  - CUDA: Parse `nvidia-smi` output (if available)
  - Metal (macOS): Platform detection + check for `gpu0` in system info
  - ROCm (AMD): Future; check for rocm installation
- **CPU Detection**: Core count, turbo availability
- **Returns**: `SystemResources(available_ram_gb, available_vram_gb, gpu_available, gpu_type)`
- **Error Handling**: If detection fails, log warning and return conservative defaults (assume no GPU, available_ram = 0)

### Module: `model_selector.recommendation`
Selects best Whisper model based on resources:
```
Algorithm:
1. Load MODEL_SPECS constant (tiny/base/small/medium/large with RAM/VRAM requirements)
2. If GPU available AND available_vram >= model.vram requirement:
   - Filter models by VRAM requirement (use VRAM fit, ignore RAM)
3. Else (CPU mode or GPU detection failed):
   - Filter models by RAM requirement using 85% of available_ram (Q3 clarification)
4. Apply ordering: large > medium > small > base > tiny
5. Return first (best) model that fits within constraints
6. If no model fits, return fallback: `base` model (Q2 clarification)
7. Log reasoning: which constraint was limiting, why fallback chosen
```

### Module: `model_selector.tui`
Interactive model selection using rich + readchar:
- Display recommended model with reasoning
- Show arrow-key selectable list of all models (with padding warnings for unsafe choices)
- Handle keyboard input (arrow keys, Enter, Esc) with readchar
- Context-aware timeout (Q4 clarification):
  - If `sys.stdin.isatty()`: wait indefinitely for user
  - Else (piped/CI): 60-second timeout, auto-select recommended if no input
- Display selection confirmation before returning

### Module: `model_selector.cache`
1-hour TTL caching (Q5 clarification):
- Cache key: SHA256(platform + ram_gb + gpu_available + gpu_type)
- Cache format: `~/.mnemofy/cache/model-recommendation.json`
  ```json
  {
    "system_fingerprint": "sha256hash...",
    "recommended_model": "base",
    "timestamp": 1707504000,
    "ttl_seconds": 3600,
    "detection_details": {...}
  }
  ```
- Load cache if: file exists AND timestamp < now - 3600 seconds
- Otherwise: detect fresh, update cache

### CLI Integration (`cli.py`)
New/modified flags:
- `transcribe FILE [--auto]`: Auto-recommend model (default behavior when no --model)
- `transcribe FILE [--no-gpu]`: Force CPU-only resource detection (disable GPU)
- `transcribe FILE [--list-models]`: Display all available models with resource requirements
- `transcribe FILE [--model tiny|base|small|medium|large]`: Manual override (existing, unchanged)

### Transcriber Integration (`transcriber.py`)
Call `model_selector.get_model_recommendation()` before transcription:
1. If `--model` flag provided: use explicitly (skip auto-selection)
2. Else: call `model_selector.get_model_recommendation(no_gpu=args.no_gpu)`
3. Returns recommended model + reasoning
4. If headless/CI AND timeout expires: use fallback without blocking
5. Pass model to transcriber engine

## Testing Strategy

**Unit Tests** (`test_model_selector.py`):
- Resource detection: Mock psutil, verify correct values parsed
- GPU detection: Test CUDA/Metal/ROCm paths with mocked system calls
- Recommendation: Test each model's RAM/VRAM requirements, edge cases
- Cache: Test expiry, fingerprint generation, fallback on invalid cache
- TUI: Mock keyboard input, verify navigation and selection
- Error handling: Verify fallback to `base` on detection failure

**Integration Tests** (`test_cli_flags.py`):
- `--list-models`: Verify output format and all models listed
- `--no-gpu`: Verify GPU detection disabled
- `--auto` with various RAM levels: Verify appropriate model recommended
- Backward compatibility: `--model tiny` still works unchanged

**Manual Testing** (per acceptance scenarios in spec.md):
- Run on 2GB, 4GB, 16GB RAM systems
- Run on systems with/without GPU
- Run in TTY (interactive) vs piped (non-interactive) contexts
- Verify cache is populated and expiring correctly

## Release Plan

**Phase 1: Resource Detection** (7 tasks, ~12 hours)
- psutil integration
- Per-platform GPU detection (CUDA, Metal, ROCm setup)
- MODEL_SPECS constant definition
- Edge case validation

**Phase 2: Recommendation Algorithm** (3 tasks, ~6 hours)
- Model selection logic with safety margin
- Fallback behavior
- Logging/reasoning

**Phase 3: TUI & Interaction** (4 tasks, ~8 hours)
- readchar integration
- Context-aware timeout detection
- Menu navigation and styling

**Phase 4: Caching** (2 tasks, ~4 hours)
- Cache file management
- TTL expiry logic
- Fingerprinting

**Phase 5: CLI Integration** (3 tasks, ~6 hours)
- Flag parsing (--auto, --no-gpu, --list-models)
- Transcriber hookup
- Backward compatibility validation

**Phase 6: Testing** (4 tasks, ~11 hours)
- Unit tests (all modules)
- Integration tests (CLI flags, end-to-end)
- Performance validation

**Phase 7: Documentation & Polish** (3 tasks, ~8 hours)
- Update CLI help text
- Add examples to README
- Release notes

**Timeline**: ~55 hours total; ~6-7 weeks at 10hrs/week; critical path ~42 hours (can parallelize Phase 1-2 with Phase 3-4)

## Clarifications Reference

All architectural decisions derived from clarification sprint (2026-02-10):
- **Q1 (Metal GPU)**: [spec.md - Clarifications](spec.md#clarifications) – GPU-eligible, RAM-only fit checks
- **Q2 (Fallback)**: [spec.md - Clarifications](spec.md#clarifications) – Use `base` model on detection failure  
- **Q3 (RAM Margin)**: [spec.md - Clarifications](spec.md#clarifications) – 85% available RAM (0.75GB buffer)
- **Q4 (Timeout)**: [spec.md - Clarifications](spec.md#clarifications) – Context-aware TTY detection
- **Q5 (Cache)**: [spec.md - Clarifications](spec.md#clarifications) – 1-hour TTL hybrid caching

See [tasks.md](tasks.md) for detailed task breakdown and [contracts/cli-interface.md](contracts/cli-interface.md) for CLI contract.
