# Feature Specification: Adaptive ASR Model Selection

## Overview
This feature introduces automatic and interactive selection of the speech-to-text (ASR) model in **mnemofy** based on the user’s available system resources.
The goal is to provide the best possible transcription quality without requiring users to understand hardware constraints, while still allowing full manual control.

The feature is triggered when the user does **not** explicitly specify a model via CLI.

---

## Goals
- Automatically recommend the most suitable Whisper model based on available resources.
- Provide a fast, keyboard-driven interactive selection (arrow keys + Enter).
- Allow users to override the recommendation and select any model.
- Avoid unexpected failures due to insufficient RAM / VRAM.
- Remain transparent and explain *why* a model is recommended.

---

## Non-Goals
- No automatic model downloads without user confirmation.
- No forced GPU usage.
- No background benchmarking.

---

## Trigger Conditions
The adaptive model selection flow is activated when:
- `--model` is **not** provided
- and `--auto` is **not** provided

Example:
```bash
mnemofy meeting.mkv
```

---

## Resource Detection

At startup, mnemofy collects runtime system information:

### CPU
- Number of logical cores
- Architecture (`x86_64`, `arm64`)
- SIMD capabilities (optional)

### Memory
- Total RAM
- Available (free) RAM

### GPU (if present)
- GPU availability
- Backend type (CUDA / Metal / ROCm)
- Available VRAM

---

## Model Capability Matrix

| Model | Min RAM | Min VRAM | Speed | Quality | Typical Use Case |
|------|--------|----------|-------|---------|------------------|
| tiny | 1 GB | – | 🔥🔥🔥 | ⭐ | quick notes |
| base | 1.5 GB | – | 🔥🔥 | ⭐⭐ | short audio |
| small | 2 GB | – | 🔥🔥 | ⭐⭐⭐ | laptops |
| medium | 4 GB | – | 🔥 | ⭐⭐⭐⭐ | default CPU |
| large-v3 | 8 GB | 6 GB | 🐢 | ⭐⭐⭐⭐⭐ | best quality |

---

## Recommendation Algorithm

1. Filter out models that do not fit into currently available RAM / VRAM.
2. Sort remaining models by:
   - Highest quality first
   - Then highest speed
3. Select the top candidate as the **recommended model**.

---

## Interactive Model Selection (TUI)

If `--auto` is not specified, mnemofy presents an interactive selector.

### UX Requirements
- Keyboard navigation using ↑ / ↓
- Confirm with Enter
- Cancel with Esc
- Recommended model highlighted
- Risky models marked with a warning

---

## CLI Flags

| Flag | Description |
|----|------------|
| `--model <name>` | Explicit model selection, skips auto-detection |
| `--auto` | Automatically select recommended model without prompting |
| `--list-models` | Print model table and exit |
| `--no-gpu` | Ignore GPU even if present |

---

## Failure Modes

### No Suitable Model
If no model fits available memory:
```text
Error: no transcription model fits into available memory.
```

### Headless / CI Environment
- Automatically behave as if `--auto` was specified.
- Never prompt interactively.

---

## Design Principles
- Safe by default
- User in control
- Transparent recommendations
- Fast UX

---

## Summary
This feature enables mnemofy to intelligently adapt to the user’s hardware while preserving explicit user control.
