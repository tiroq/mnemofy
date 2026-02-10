# CLI Interface Contract: Adaptive ASR Model Selection

**Feature ID**: 001 | **Contract Type**: CLI | **Version**: 1.0

## Overview

This contract defines the command-line interface additions for adaptive ASR model selection. All changes are **backward compatible** and additive (no breaking changes to existing CLI).

---

## Command Signature

### Existing Command (Modified)

```bash
mnemofy transcribe [OPTIONS] AUDIO_FILE
```

### New Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--model`, `-m` | Choice[str] | `None` (auto) | Explicit model selection. Bypasses auto-detection. |
| `--auto` | Flag | `False` | Auto-select recommended model without interactive prompt. |
| `--no-gpu` | Flag | `False` | Disable GPU acceleration even if available. |
| `--list-models` | Flag | `False` | Display available models and system compatibility, then exit. |

---

## Option Specifications

### --model / -m

**Type**: `Optional[str]`  
**Valid Values**: `"tiny"`, `"base"`, `"small"`, `"medium"`, `"large-v3"`, or any valid faster-whisper model name  
**Default**: `None` (triggers auto-detection)

**Behavior**:
- If provided: Use specified model, skip all auto-detection and interactive selection
- If not provided: Enter auto-detection flow (see [Flow Diagram](#flow-diagram))
- Invalid model names: Log warning but proceed (faster-whisper will error if truly invalid)

**Examples**:
```bash
mnemofy transcribe meeting.mp4 --model tiny
mnemofy transcribe meeting.mp4 -m large-v3
```

**Backward Compatibility**: 
- Previously, `--model` flag did not exist (model selection was not exposed)
- Now, `--model` provides explicit control
- If users relied on default behavior (no model selection), they will now see interactive menu (can disable with `--auto`)

---

### --auto

**Type**: `bool` (flag)  
**Default**: `False`

**Behavior**:
- If `True`: Auto-select recommended model without showing interactive menu
- If `False` and TTY detected: Show interactive menu
- If `False` and no TTY (CI, pipe, redirect): Auto-select (same as `True`)

**Use Cases**:
- CI/CD pipelines where no user interaction is available
- Scripting (batch processing multiple files)
- Users who prefer automatic behavior

**Examples**:
```bash
mnemofy transcribe meeting.mp4 --auto
mnemofy transcribe meeting.mp4 --auto --no-gpu
```

**Interaction with --model**:
- If `--model` is provided, `--auto` has no effect (model is explicit)

---

### --no-gpu

**Type**: `bool` (flag)  
**Default**: `False`

**Behavior**:
- If `True`: Force CPU-only mode, do not use GPU even if available
- If `False`: Use GPU if detected

**Use Cases**:
- GPU is Available but user prefers CPU (e.g., GPU busy with other tasks)
- Testing CPU performance
- Workarounds for GPU driver issues

**Examples**:
```bash
mnemofy transcribe meeting.mp4 --no-gpu
mnemofy transcribe meeting.mp4 --no-gpu --model medium
```

**Interaction with --model**:
- `--no-gpu` affects resource detection but not explicit model selection
- Explicit `--model` still uses GPU if available (unless `--no-gpu` is set)

---

### --list-models

**Type**: `bool` (flag)  
**Default**: `False`

**Behavior**:
- If `True`: Display model compatibility table, then exit (do not transcribe)
- Detects system resources
- Shows all models with compatibility status (✓, ⚠, ✗)
- Exit with code `0` (success)

**Use Cases**:
- User wants to see available models before transcribing
- User wants to check system compatibility
- Debugging resource detection

**Examples**:
```bash
mnemofy transcribe --list-models
```

**Output Format** (example):
```text
System Resources:
  CPU: 8 cores (arm64)
  RAM: 16.0 GB (14.2 GB available)
  GPU: Metal (Apple M2)

Available Whisper Models:

┌──────────┬───────┬─────────┬──────────┬─────────┬────────────┐
│ Model    │ Speed │ Quality │ RAM Req  │ VRAM    │ Status     │
├──────────┼───────┼─────────┼──────────┼─────────┼────────────┤
│ tiny     │ ★★★★★ │ ★★☆☆☆   │ 1.2 GB   │ 1.2 GB  │ ✓ OK       │
│ base     │ ★★★★★ │ ★★★☆☆   │ 1.5 GB   │ 1.5 GB  │ ✓ OK       │
│ small    │ ★★★★☆ │ ★★★☆☆   │ 2.5 GB   │ 2.0 GB  │ ✓ OK       │
│ medium   │ ★★★☆☆ │ ★★★★☆   │ 5.0 GB   │ 4.0 GB  │ ✓ OK       │
│ large-v3 │ ★★☆☆☆ │ ★★★★★   │ 10.0 GB  │ 8.0 GB  │ ✓ Rec.     │
└──────────┴───────┴─────────┴──────────┴─────────┴────────────┘

Recommended: large-v3 (sufficient RAM, GPU available)

Use --model <name> to select a specific model.
```

**Interaction with other flags**:
- `--list-models` takes precedence; other flags are ignored
- `AUDIO_FILE` argument becomes optional when `--list-models` is used

---

## Flow Diagram

```text
START
  │
  ├─> [--list-models?] ─YES─> Display table → EXIT(0)
  │                    └NO
  │
  ├─> [--model specified?] ─YES─> Use explicit model → CONTINUE
  │                        └NO
  │
  ├─> Detect system resources
  │
  ├─> Recommend model (filter compatible, select best)
  │
  ├─> [--auto OR non-TTY?] ─YES─> Auto-select recommended → CONTINUE
  │                         └NO
  │
  ├─> Show interactive menu
  │   ├─> User selects model → CONTINUE
  │   └─> User cancels (Esc/Ctrl+C) → EXIT(1)
  │
CONTINUE
  │
  └─> Transcribe with selected model
```

---

## Exit Codes

| Code | Scenario |
|------|----------|
| `0` | Success (transcription completed or --list-models displayed) |
| `1` | Error (user cancelled, file not found, transcription failed) |
| `2` | Invalid arguments (malformed CLI usage) |

---

## Error Messages

### Insufficient Resources

**Scenario**: No model fits in available RAM.

**Message**:
```text
Error: Insufficient RAM for any Whisper model.
  Available: 1.5 GB
  Minimum required: 2.0 GB (tiny model)

Try:
  - Closing other applications to free memory
  - Using a system with more RAM
  - Using --model tiny (at your own risk)
```

**Exit Code**: `1`

---

### Resource Detection Failure

**Scenario**: psutil or GPU detection fails.

**Message**:
```text
Warning: Could not detect system resources.
  Error: [specific error message]

Falling back to conservative default: base model.
Use --model to override if needed.
```

**Behavior**: Continue with fallback model (don't crash).

---

### Model Download Required

**Scenario**: Selected model not cached locally (first use).

**Message**:
```text
Downloading model: large-v3 (~3GB)
[====================] 100% (3.2GB / 3.2GB)
```

**Behavior**: Show progress bar (faster-whisper built-in), continue when complete.

---

## Interactive Menu Specification

### Display Format

```text
Select Whisper Model:

  ↓ tiny     (★★★★★ speed, ★★☆☆☆ quality) - 1.2 GB RAM
    base     (★★★★★ speed, ★★★☆☆ quality) - 1.5 GB RAM
  ★ medium   (★★★☆☆ speed, ★★★★☆ quality) - 5.0 GB RAM [Recommended]
    large-v3 (★★☆☆☆ speed, ★★★★★ quality) - 10.0 GB RAM ⚠ High memory

Use ↑↓ arrow keys to navigate, Enter to confirm, Esc to cancel.
```

**Legend**:
- `→`: Current selection (cursor)
- `★`: Recommended model (icon/color)
- `⚠`: Warning (near resource limit)

### Keyboard Controls

| Key | Action |
|-----|--------|
| `↑` (Up Arrow) | Move selection up |
| `↓` (Down Arrow) | Move selection down |
| `Enter` | Confirm selection |
| `Esc` | Cancel (exit with code 1) |
| `Ctrl+C` | Cancel (exit with code 1) |

---

## Backward Compatibility

### Breaking Changes

**None.** This feature is fully backward compatible.

### Behavioral Changes

1. **New default behavior**: If no `--model` is specified, interactive menu appears (TTY) or auto-selection occurs (non-TTY).
   - **Migration**: Users who want old behavior (no prompts) can use `--auto` flag.

2. **Model selection now exposed**: Previously, model was hardcoded or not configurable.
   - **Migration**: No action needed; feature is additive.

---

## Validation Rules

### CLI Argument Validation

1. **AUDIO_FILE**: Required unless `--list-models` is used
2. **--model**: If provided, must be non-empty string
3. **--auto, --no-gpu, --list-models**: Boolean flags, no value required

### Runtime Validation

1. **Resource detection**: Must complete within 5 seconds (timeout)
2. **Model compatibility**: Must have at least 20% RAM margin (safety buffer)
3. **Interactive menu**: Must render within 500ms

---

## Testing Contract

### Unit Tests

- Test flag parsing (typer CLI)
- Test flag combinations (--model + --auto, etc.)
- Test exit codes
- Test error messages

### Integration Tests

- Test `--model` bypasses detection
- Test `--auto` skips interactive menu
- Test `--no-gpu` forces CPU mode
- Test `--list-models` displays and exits
- Test TTY vs non-TTY behavior
- Test user cancellation in interactive menu

### Manual Tests

- Test on real hardware (diverse RAM/GPU configurations)
- Test in CI environment (GitHub Actions)
- Test with piped input/output
- Test with invalid model names

---

## Documentation Requirements

1. **README.md**: Add examples for all new flags
2. **CLI help text**: `mnemofy transcribe --help` must document new options
3. **Error messages**: Must guide users to resolution
4. **Changelog**: Document new flags in v0.7.0 release notes

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-10 | Initial contract definition |

---

## Notes

- This contract is binding for mnemofy v0.7.0 release
- Any changes to this contract require updating this document and incrementing version
- Constitution alignment: User Control (--model), Transparency (--list-models), Safe-by-Default (recommendation algorithm)
