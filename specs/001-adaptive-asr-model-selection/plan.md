# Implementation Plan: Adaptive ASR Model Selection

**Branch**: `001-adaptive-asr-model-selection` | **Date**: 2026-02-10 | **Spec**: [spec.md](./spec.md)

## Summary

This feature introduces intelligent ASR model selection that automatically detects system resources (RAM, VRAM, CPU) and recommends the most suitable Whisper model. Users get fast, keyboard-driven interactive selection with the ability to override recommendations. The technical approach uses Python's `psutil` for resource detection, `rich` for TUI rendering, and `typer` for CLI integration.

## Technical Context

**Language/Version**: Python 3.9-3.13 (current mnemofy requirement)  
**Primary Dependencies**: 
- `psutil>=5.9.0` (system resource detection)
- `rich>=13.0.0` (already in deps, TUI rendering)
- `typer>=0.9.0` (already in deps, CLI framework)
- `faster-whisper>=1.0.0` (already in deps, ASR engine)

**Storage**: N/A (stateless feature, no persistence required)  
**Testing**: pytest (existing test framework)  
**Target Platform**: macOS, Linux, Windows (cross-platform)  
**Project Type**: single (CLI application)  
**Performance Goals**: 
- Resource detection: <1 second
- Interactive selector response: <50ms
- Model recommendation: <100ms

**Constraints**: 
- Must maintain CLI compatibility (no breaking changes)
- Must work in headless/CI environments
- Must respect existing `--model` flag behavior
- OpenMP library conflicts require KMP_DUPLICATE_LIB_OK workaround on macOS

**Scale/Scope**: 
- 5 Whisper models (tiny, base, small, medium, large-v3)
- ~500-1000 LOC across 3 new modules
- 20-30 test cases

## Constitution Check

### Principle Compliance

✅ **User Control Over Automation**: 
- Interactive selection preserves agency
- `--model` flag provides complete override
- `--auto` flag available for scripting

✅ **Safe-by-Default Execution**: 
- Pre-flight resource checks prevent OOM crashes
- Resource detection validates before model loading
- Clear error messages when no model fits

✅ **Transparency Over Magic**: 
- Recommendation reasoning always displayed
- `--list-models` provides full transparency
- No silent fallbacks or hidden behavior

✅ **Deterministic First, Intelligent Second**: 
- Explicit model selection (`--model`) is deterministic
- Auto-selection is deterministic given same resources
- No AI/ML in recommendation logic (pure heuristic)

✅ **Progressive Disclosure of Complexity**: 
- Beginners: automatic recommendation
- Intermediate: interactive selection
- Advanced: `--model` flag for full control

✅ **Performance Is a Feature**: 
- Resource detection optimized <1s
- Minimal overhead to existing transcription flow
- Uses efficient system APIs

✅ **Explicit Over Implicit Persistence**: 
- No state persisted between runs
- Each invocation detects fresh state
- No hidden configuration files

✅ **Media-Agnostic Input**: 
- Feature enhances existing media support
- No impact on supported formats

✅ **OSS Quality Bar**: 
- Clear documentation required
- CLI contract remains stable
- Feature is additive (non-breaking)

### Violations

**No violations identified.** Feature fully aligns with constitution.

## Project Structure

### Documentation (this feature)

```text
.specify/specs/001-adaptive-asr-model-selection/
├── spec.md              # Feature specification (this file's sibling)
├── plan.md              # This file (implementation plan)
├── research.md          # (To be created: resource detection research)
├── contracts/           # (To be created: CLI contract definitions)
│   └── cli-flags.md     # New CLI flags and behavior
└── tasks.md             # (To be created: task breakdown)
```

### Source Code (repository root)

```text
src/mnemofy/
├── __init__.py
├── cli.py                    # [MODIFIED] Add new CLI flags, integrate selector
├── transcriber.py            # [EXISTING] No changes required
├── audio.py                  # [EXISTING] No changes required
├── notes.py                  # [EXISTING] No changes required
├── resources.py              # [NEW] System resource detection
├── model_selector.py         # [NEW] Model recommendation logic
└── tui/                      # [NEW] Terminal UI components
    ├── __init__.py
    └── model_menu.py         # [NEW] Interactive model selection menu

tests/
├── test_audio.py             # [EXISTING] No changes
├── test_notes.py             # [EXISTING] No changes
├── test_transcriber.py       # [EXISTING] No changes
├── test_resources.py         # [NEW] Resource detection tests
├── test_model_selector.py    # [NEW] Model selection logic tests
└── test_tui_model_menu.py    # [NEW] TUI component tests
```

**Structure Decision**: Single project structure maintained. New modules added to existing `src/mnemofy/` directory following established conventions. TUI components grouped in subdirectory for organization.

## Architecture

### Component Overview

```
┌─────────────┐
│  CLI Entry  │  cli.py (typer commands)
│   (typer)   │
└──────┬──────┘
       │
       ├──> [NEW] resources.py
       │    ├── detect_system_resources()
       │    ├── get_cpu_info()
       │    ├── get_memory_info()
       │    └── get_gpu_info()
       │
       ├──> [NEW] model_selector.py
       │    ├── ModelSpec (dataclass)
       │    ├── filter_compatible_models()
       │    ├── recommend_model()
       │    └── get_model_table()
       │
       └──> [NEW] tui/model_menu.py
            ├── ModelMenu (interactive selector)
            ├── render_model_list()
            └── handle_keyboard_input()
```

### Data Flow

1. **CLI invocation**: User runs `mnemofy transcribe file.mp4`
2. **Check explicit model**: If `--model` provided, skip to transcription
3. **Resource detection**: `resources.py` queries system (psutil)
4. **Model filtering**: `model_selector.py` filters compatible models
5. **Recommendation**: Select highest quality compatible model
6. **Interactive/Auto**:
   - If TTY + not `--auto`: Show interactive menu
   - Else: Auto-select recommended model
7. **Transcription**: Pass selected model to existing transcriber

### Key Design Decisions

**Decision 1: Use psutil for resource detection**
- **Rationale**: Cross-platform, well-maintained, already used in ecosystem
- **Alternative rejected**: Platform-specific APIs (adds complexity)

**Decision 2: Build TUI with rich**
- **Rationale**: Already a dependency, excellent terminal UI support
- **Alternative rejected**: Custom ANSI escape codes (reinventing wheel)

**Decision 3: No model preference persistence**
- **Rationale**: Aligns with Constitution Principle 8 (explicit persistence)
- **Alternative rejected**: Config file persistence (implicit, violates principle)

**Decision 4: Deterministic recommendation algorithm**
- **Rationale**: Aligns with Constitution Principle 4 (deterministic first)
- **Alternative rejected**: ML-based prediction (non-deterministic, overkill)

## Module Specifications

### resources.py

**Purpose**: Detect and report system hardware capabilities

**Public API**:
```python
@dataclass
class SystemResources:
    cpu_cores: int
    cpu_arch: str
    total_ram_gb: float
    available_ram_gb: float
    has_gpu: bool
    gpu_type: Optional[str]  # "cuda", "metal", "rocm", None
    available_vram_gb: Optional[float]

def detect_system_resources() -> SystemResources:
    """Detect current system resources."""
    ...

def get_cpu_info() -> tuple[int, str]:
    """Returns (core_count, architecture)."""
    ...

def get_memory_info() -> tuple[float, float]:
    """Returns (total_gb, available_gb)."""
    ...

def get_gpu_info() -> tuple[bool, Optional[str], Optional[float]]:
    """Returns (has_gpu, gpu_type, vram_gb)."""
    ...
```

**Dependencies**: `psutil`, `platform`

**Error Handling**: 
- Graceful degradation if detection fails
- Log warnings, use conservative defaults
- Never crash on detection failure

---

### model_selector.py

**Purpose**: Model recommendation logic and filtering

**Public API**:
```python
@dataclass
class ModelSpec:
    name: str
    min_ram_gb: float
    min_vram_gb: Optional[float]
    speed_rating: int  # 1-5, 5=fastest
    quality_rating: int  # 1-5, 5=best
    description: str

MODEL_SPECS: dict[str, ModelSpec] = {...}  # Hardcoded model database

def filter_compatible_models(
    resources: SystemResources,
    use_gpu: bool = True
) -> list[ModelSpec]:
    """Filter models that fit in available resources."""
    ...

def recommend_model(
    resources: SystemResources,
    use_gpu: bool = True
) -> tuple[ModelSpec, str]:
    """Returns (recommended_model, reasoning)."""
    ...

def get_model_table(
    resources: SystemResources,
    recommended: ModelSpec
) -> str:
    """Generate formatted model comparison table."""
    ...
```

**Algorithm**: 
1. Filter models by RAM requirement <= available RAM
2. If GPU available and `use_gpu=True`, consider VRAM
3. Sort by quality descending, then speed descending
4. Return top model with reasoning

---

### tui/model_menu.py

**Purpose**: Interactive terminal UI for model selection

**Public API**:
```python
class ModelMenu:
    def __init__(
        self,
        models: list[ModelSpec],
        recommended: ModelSpec,
        resources: SystemResources
    ):
        ...
    
    def show(self) -> Optional[ModelSpec]:
        """Display menu, return selected model or None if cancelled."""
        ...

def is_interactive_environment() -> bool:
    """Check if running in interactive terminal (has TTY)."""
    ...
```

**UI Requirements**:
- Arrow keys (↑/↓) for navigation
- Enter to confirm
- Esc to cancel
- Highlight recommended model
- Show warning icon for risky models
- Display model details on hover/selection

---

### CLI Integration (cli.py modifications)

**New Flags**:
```python
@app.command()
def transcribe(
    ...,  # existing params
    model: Optional[str] = typer.Option(
        None,
        "--model", "-m",
        help="Whisper model (tiny, base, small, medium, large-v3). Auto-detected if not specified."
    ),
    auto: bool = typer.Option(
        False,
        "--auto",
        help="Automatically select recommended model without prompting"
    ),
    no_gpu: bool = typer.Option(
        False,
        "--no-gpu",
        help="Disable GPU acceleration even if available"
    ),
    list_models: bool = typer.Option(
        False,
        "--list-models",
        help="Show available models and exit"
    ),
):
    ...
```

**Flow Integration**:
```python
if list_models:
    display_model_table_and_exit()

if model:
    # Explicit model specified, use it
    selected_model = model
else:
    # Auto-detection path
    resources = detect_system_resources()
    recommended, reasoning = recommend_model(resources, use_gpu=not no_gpu)
    
    if auto or not is_interactive_environment():
        selected_model = recommended.name
        console.print(f"Auto-selected: {recommended.name} ({reasoning})")
    else:
        # Interactive selection
        menu = ModelMenu(models, recommended, resources)
        selected = menu.show()
        if selected is None:
            raise typer.Abort()
        selected_model = selected.name

# Continue with existing transcription flow
transcriber = Transcriber(model_name=selected_model)
...
```

## Testing Strategy

### Unit Tests

**test_resources.py**:
- Mock psutil responses
- Test CPU detection accuracy
- Test memory detection accuracy
- Test GPU detection on various platforms
- Test graceful degradation on detection failure

**test_model_selector.py**:
- Test model filtering logic
- Test recommendation algorithm with various resource scenarios
- Test table generation formatting
- Test edge cases (no compatible model, all models compatible)

**test_tui_model_menu.py**:
- Mock keyboard input
- Test navigation logic
- Test selection confirmation
- Test cancellation
- Test TTY detection

### Integration Tests

**test_cli_integration.py** (new):
- Test `--model` flag bypasses detection
- Test `--auto` skips interactive prompt
- Test `--no-gpu` forces CPU mode
- Test `--list-models` displays table
- Test interactive selection in mock TTY
- Test headless auto-selection

### Manual Testing Scenarios

1. **Low RAM system** (2GB): Verify `base` or `small` recommended
2. **High RAM system** (16GB+): Verify `large-v3` recommended
3. **GPU system**: Verify GPU detection and model recommendation
4. **Headless environment**: Verify auto-selection without prompt
5. **Interactive environment**: Verify keyboard navigation works
6. **Explicit model override**: Verify `--model tiny` bypasses detection

## Complexity Tracking

**No complexity violations.** Feature adds new modules without violating architecture principles.

## Risk Mitigation

### Risk 1: GPU detection may fail on some platforms
**Mitigation**: Graceful fallback to CPU-only mode with logged warning

### Risk 2: Resource detection overhead
**Mitigation**: Benchmark and optimize; cache results if needed; <1s SLA

### Risk 3: Interactive menu rendering issues in different terminals
**Mitigation**: Use rich library's battle-tested rendering; fallback to simple prompts

### Risk 4: Model database becomes outdated as faster-whisper evolves
**Mitigation**: Document model specs clearly; easy to update MODEL_SPECS constant

## Implementation Phases

1. **Phase 0: Research** - Verify psutil capabilities, rich TUI APIs
2. **Phase 1: Resources** - Implement and test resource detection
3. **Phase 2: Selector** - Implement model filtering and recommendation logic
4. **Phase 3: TUI** - Build interactive menu
5. **Phase 4: Integration** - Integrate with CLI, add flags
6. **Phase 5: Testing** - Comprehensive testing, edge cases
7. **Phase 6: Documentation** - Update README, add examples

## Documentation Requirements

### README.md Updates

Add section:
```markdown
### Automatic Model Selection

mnemofy automatically selects the best Whisper model for your system:

\`\`\`bash
mnemofy transcribe meeting.mp4
# System detects 8GB RAM → recommends 'medium' model
# Interactive menu appears → select with arrow keys
\`\`\`

Override automatic selection:
\`\`\`bash
mnemofy transcribe meeting.mp4 --model tiny
\`\`\`

Automated/headless mode:
\`\`\`bash
mnemofy transcribe meeting.mp4 --auto
\`\`\`

View available models:
\`\`\`bash
mnemofy transcribe --list-models
\`\`\`
```

### CLI Help Text

Ensure `mnemofy transcribe --help` clearly explains new flags and behavior.

## Rollout Plan

1. Feature developed in `001-adaptive-asr-model-selection` branch
2. Internal testing on diverse hardware (low RAM, high RAM, GPU, no GPU)
3. Update README and documentation
4. Merge to main, release as minor version (v0.7.0)
5. Monitor for issues, especially on Windows (less tested platform)

## Success Metrics

- 95%+ users successfully get appropriate model recommendation
- Zero OOM crashes when using recommended model
- Interactive selection completes in <5 seconds average
- No regression in existing `--model` flag behavior
