# Feature 001: Adaptive ASR Model Selection

**Status**: Planning Complete | **Version**: 1.0 | **Date**: 2026-02-10

## Quick Links

- **[Feature Specification](./spec.md)** - User stories, requirements, success criteria
- **[Implementation Plan](./plan.md)** - Technical architecture, dependencies, phases
- **[Task Breakdown](./tasks.md)** - Detailed implementation tasks (28 tasks, ~55 hours)
- **[Research Notes](./research.md)** - Technical research findings (psutil, GPU detection, TUI)
- **[Data Model](./data-model.md)** - Entity definitions and relationships
- **[CLI Contract](./contracts/cli-interface.md)** - Command-line interface specification

## Overview

This feature introduces intelligent ASR model selection that automatically detects system resources (RAM, VRAM, CPU) and recommends the most suitable Whisper model. Users get fast, keyboard-driven interactive selection with the ability to override recommendations.

### Key Capabilities

- ✅ **Automatic model recommendation** based on available RAM/VRAM
- ✅ **Interactive TUI selector** with arrow key navigation
- ✅ **Explicit override** via `--model` flag
- ✅ **Headless/CI mode** with `--auto` flag
- ✅ **Model information** via `--list-models` flag

### Project Alignment

**Constitution Principles**:
- User Control Over Automation (Principle 1)
- Safe-by-Default Execution (Principle 2)
- Transparency Over Magic (Principle 3)
- Progressive Disclosure (Principle 6)
- Performance Is a Feature (Principle 7)

## User Stories (Prioritized)

| ID | Story | Priority | Status |
|----|-------|----------|--------|
| US-001 | Automatic model recommendation | P1 | Planning |
| US-002 | Interactive selection | P2 | Planning |
| US-003 | Explicit override (`--model`) | P1 | Planning |
| US-004 | Headless mode (`--auto`) | P2 | Planning |
| US-005 | Model info (`--list-models`) | P3 | Planning |

## Success Criteria

- [ ] 95%+ users get appropriate model recommendation
- [ ] Zero OOM crashes when using recommended model
- [ ] Interactive selection completes in <5 seconds
- [ ] 100% headless/CI environments supported
- [ ] Resource detection completes in <1 second
- [ ] Full backward compatibility maintained

## Technical Architecture

### New Modules

```
src/mnemofy/
├── resources.py          # System resource detection (psutil)
├── model_selector.py     # Model recommendation logic
└── tui/
    └── model_menu.py     # Interactive TUI (rich + readchar)
```

### Dependencies Added

- `psutil>=5.9.0` - System resource detection
- `readchar>=4.0.0` - Keyboard input for TUI

### CLI Additions

```bash
--model <name>      # Explicit model selection (bypass auto-detection)
--auto              # Auto-select without interactive prompt
--no-gpu            # Force CPU mode
--list-models       # Display model compatibility table
```

## Implementation Phases

| Phase | Description | Est. Hours | Status |
|-------|-------------|------------|--------|
| 0 | Research (psutil, GPU detection, TUI) | 3 | Not Started |
| 1 | Resource detection module | 10 | Not Started |
| 2 | Model selection logic | 9 | Not Started |
| 3 | Interactive TUI | 7 | Not Started |
| 4 | CLI integration | 6 | Not Started |
| 5 | Testing (unit + integration) | 9 | Not Started |
| 6 | Documentation | 3 | Not Started |
| 7 | Release (v0.7.0) | 4 | Not Started |

**Total Estimated Effort**: ~55 hours

## Critical Path Tasks

1. **R-001**: Research psutil capabilities (2h)
2. **T-001 to T-005**: Implement resource detection (10h)
3. **T-006 to T-008**: Implement model selection logic (7h)
4. **T-013, T-015, T-016**: CLI integration (4h)
5. **T-019, T-020**: Testing (7h)
6. **T-023**: Documentation (2h)
7. **T-026 to T-028**: Release (4h)

**Critical Path Total**: ~42 hours

## Model Database

| Model | RAM | VRAM | Speed | Quality | Use Case |
|-------|-----|------|-------|---------|----------|
| tiny | 1.2GB | 1.2GB | ★★★★★ | ★★☆☆☆ | Testing, drafts |
| base | 1.5GB | 1.5GB | ★★★★★ | ★★★☆☆ | Quick transcriptions |
| small | 2.5GB | 2.0GB | ★★★★☆ | ★★★☆☆ | General use |
| medium | 5.0GB | 4.0GB | ★★★☆☆ | ★★★★☆ | Production (recommended) |
| large-v3 | 10.0GB | 8.0GB | ★★☆☆☆ | ★★★★★ | High-end hardware |

## Testing Strategy

### Unit Tests (90% coverage target)
- `test_resources.py` - Resource detection, validation, error handling
- `test_model_selector.py` - Filtering, recommendation, table generation
- `test_tui_model_menu.py` - Navigation, selection, cancellation

### Integration Tests
- CLI flag combinations (`--model`, `--auto`, `--no-gpu`, `--list-models`)
- TTY vs non-TTY behavior
- End-to-end workflows

### Manual Testing
- Low RAM system (4GB): tiny/base recommended
- High RAM system (16GB+): large-v3 recommended
- GPU systems (NVIDIA, Metal): GPU detection works
- Headless/CI: auto-selection without prompts

## Documentation Requirements

- [x] Feature specification (this folder)
- [x] Implementation plan
- [x] Task breakdown
- [x] CLI contract
- [x] Data model
- [ ] README.md update (usage examples)
- [ ] CLI help text (`--help`)
- [ ] Troubleshooting guide

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GPU detection fails on some platforms | Medium | Graceful fallback to CPU mode |
| Resource detection overhead | Low | Benchmark, optimize, <1s SLA |
| TUI rendering issues | Low | Use rich's battle-tested lib |
| Model specs become outdated | Low | Easy to update MODEL_SPECS |

## Release Plan

**Target Version**: v0.7.0 (minor release - new feature, backward compatible)

1. Feature developed in `001-adaptive-asr-model-selection` branch
2. Internal testing on diverse hardware (low RAM, high RAM, GPU, no GPU)
3. Update README and CLI help
4. Merge to main, publish to PyPI
5. Monitor for issues (especially Windows)

## Next Steps

1. **Now**: Review this specification with stakeholders
2. **Phase 0**: Begin research (R-001, R-002) - 3 hours
3. **Phase 1**: Implement resource detection - 10 hours
4. **Phase 2-7**: Follow task breakdown in [tasks.md](./tasks.md)

## Questions?

See [research.md](./research.md) for technical details and [spec.md](./spec.md) for complete requirements.

---

**Last Updated**: 2026-02-10  
**Maintained By**: mnemofy project  
**Specification Version**: 1.0
