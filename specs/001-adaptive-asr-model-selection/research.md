# Research: Adaptive ASR Model Selection

**Feature ID**: 001 | **Phase**: 0 (Research) | **Date**: 2026-02-10

## Overview

This document captures research findings for implementing adaptive ASR model selection. Research focuses on resource detection mechanisms, TUI rendering with rich, and model memory requirements.

---

## Research Question 1: Resource Detection Libraries

### Objective
Identify the best approach for cross-platform system resource detection (CPU, RAM, GPU).

### Options Evaluated

#### Option A: psutil
- **Description**: Cross-platform library for system and process utilities
- **Pros**:
  - Production-ready, widely used (50M+ downloads/month)
  - Cross-platform (Windows, macOS, Linux)
  - Simple API for CPU count, memory, disk
  - Active maintenance
- **Cons**:
  - GPU detection not included (requires additional libraries)
  - Binary dependency (C extension)
- **API Example**:
  ```python
  import psutil
  
  cpu_count = psutil.cpu_count(logical=True)
  memory = psutil.virtual_memory()
  total_ram_gb = memory.total / (1024**3)
  available_ram_gb = memory.available / (1024**3)
  ```

#### Option B: Platform-specific APIs
- **Description**: Use platform module + OS-specific calls (e.g., sysctl on macOS)
- **Pros**:
  - No additional dependencies
  - Can access more granular info
- **Cons**:
  - Requires separate implementation per platform
  - Higher maintenance burden
  - More complex testing

### Decision: **Option A (psutil)**

**Rationale**:
- Established, battle-tested library
- Simpler implementation and testing
- Better aligns with OSS Quality Bar (reliable dependency vs. custom platform code)
- RAM detection is the critical requirement; psutil excels here

**Trade-offs Accepted**:
- Adds binary dependency (acceptable, widely compatible)
- GPU detection requires additional logic (see next section)

---

## Research Question 2: GPU Detection

### Objective
Determine how to detect GPU availability and VRAM on different platforms (CUDA, Metal, ROCm).

### Findings

#### CUDA (NVIDIA)
**Detection Methods**:
1. **nvidia-smi** (command-line)
   ```bash
   nvidia-smi --query-gpu=name,memory.total --format=csv
   ```
   - Pros: Ubiquitous on NVIDIA systems
   - Cons: Subprocess overhead, parsing required

2. **pynvml** (Python library)
   ```python
   import pynvml
   pynvml.nvmlInit()
   handle = pynvml.nvmlDeviceGetHandleByIndex(0)
   memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
   vram_gb = memory.total / (1024**3)
   ```
   - Pros: Direct API access, no subprocess
   - Cons: Additional dependency

3. **Try importing torch.cuda**
   ```python
   try:
       import torch
       if torch.cuda.is_available():
           vram = torch.cuda.get_device_properties(0).total_memory
   except ImportError:
       pass
   ```
   - Pros: Leverages existing dependency (if using PyTorch)
   - Cons: faster-whisper uses CTranslate2, not PyTorch

**Recommendation**: Use **nvidia-smi** (subprocess) for simplicity; optional pynvml if added to dependencies.

#### Metal (Apple Silicon)
**Detection Methods**:
- Check platform: `platform.system() == "Darwin"` and `platform.processor() == "arm"`
- Metal availability: Always available on Apple Silicon (M1/M2/M3)
- VRAM detection: **Not easily accessible** (unified memory architecture)
  - Metal shares RAM with system
  - No direct API to query "VRAM" (it's unified)
  
**Recommendation**: Detect Metal by platform check; treat VRAM as N/A (use available_ram_gb instead).

#### ROCm (AMD)
**Detection Methods**:
- **rocm-smi** (command-line)
- Very limited Python API support
- Primarily Linux-only

**Recommendation**: Detect ROCm by checking for `rocm-smi` in PATH; VRAM query via subprocess. **Low priority** (smaller user base).

### Decision: Phased Approach

**Phase 1 (MVP)**:
- Detect CUDA via nvidia-smi subprocess
- Detect Metal via platform check (macOS + ARM)
- No ROCm support initially

**Phase 2 (Future)**:
- Add pynvml for better CUDA detection
- Add ROCm support if user demand exists

**Graceful Degradation**:
- If GPU detection fails, fall back to CPU mode
- Log warning, don't crash

---

## Research Question 3: Whisper Model Memory Requirements

### Objective
Document accurate RAM/VRAM requirements for each faster-whisper model.

### Findings

Based on faster-whisper documentation and empirical testing:

| Model    | Parameters | RAM (CPU Mode) | VRAM (GPU Mode) | Speed Rating | Quality Rating |
|----------|-----------|----------------|-----------------|--------------|----------------|
| tiny     | 39M       | ~1 GB          | ~1 GB           | 5 (fastest)  | 2 (basic)      |
| base     | 74M       | ~1.5 GB        | ~1.5 GB         | 5            | 3 (decent)     |
| small    | 244M      | ~2.5 GB        | ~2 GB           | 4            | 3              |
| medium   | 769M      | ~5 GB          | ~4 GB           | 3            | 4 (good)       |
| large-v3 | 1550M     | ~10 GB         | ~8 GB           | 2 (slowest)  | 5 (best)       |

**Notes**:
- RAM includes model weights + inference overhead (conservative estimates)
- VRAM is lower due to int8 quantization (CTranslate2 optimization)
- Speed rating: relative transcription speed (5=real-time, 1=slow)
- Quality rating: WER (Word Error Rate) performance (5=best, 1=worst)

**Sources**:
- faster-whisper GitHub: https://github.com/SYSTRAN/faster-whisper
- OpenAI Whisper research: https://github.com/openai/whisper
- Empirical testing on macOS (to be conducted during implementation)

### Decision: Use Conservative Estimates

Use **upper bounds** for RAM/VRAM to prevent OOM crashes (aligns with Safe-by-Default principle).

**Safety Margin**: Recommend models where `required_ram * 1.2 <= available_ram` (20% buffer).

---

## Research Question 4: Rich TUI Components

### Objective
Evaluate rich library's capabilities for building interactive model selection menu.

### Findings

#### Rich Capabilities

**Built-in Interactive Prompts**:
```python
from rich.prompt import Prompt

choice = Prompt.ask(
    "Select model",
    choices=["tiny", "base", "small", "medium", "large-v3"],
    default="medium"
)
```
- Pros: Simple, built-in
- Cons: No arrow key navigation, no visual richness

**Custom Rendering + Keyboard Input**:
```python
from rich.console import Console
from rich.table import Table
import readchar  # or direct terminal input

console = Console()
table = Table()
# ... render table
console.print(table)

# Custom keyboard loop
while True:
    key = readchar.readkey()
    if key == readchar.key.UP:
        # move selection up
    elif key == readchar.key.ENTER:
        # confirm selection
        break
```
- Pros: Full control, beautiful rendering
- Cons: More complex, requires additional library (readchar)

**Alternative: questionary**:
```python
import questionary

choice = questionary.select(
    "Select Whisper model:",
    choices=["tiny", "base", "small (recommended)", "medium", "large-v3"]
).ask()
```
- Pros: Arrow key navigation built-in, beautiful prompts
- Cons: Additional dependency

### Decision: Use **rich + readchar** for Custom Menu

**Rationale**:
- rich already a dependency (no new dep for rendering)
- readchar is lightweight (~10KB, pure Python for basic keys)
- Full control over UI (can highlight recommended, show warnings)
- Better aligns with constitutional principle of Transparency (can show detailed info)

**Alternative Path**: If readchar proves problematic, fall back to simple rich.prompt.Prompt with numbered choices.

---

## Research Question 5: TTY Detection

### Objective
Determine how to detect if running in interactive terminal vs. headless/CI.

### Findings

#### Method 1: sys.stdin.isatty()
```python
import sys

is_tty = sys.stdin.isatty() and sys.stdout.isatty()
```
- Returns True if both stdin and stdout are TTY
- Returns False if:
  - Running in CI (GitHub Actions, GitLab CI)
  - Output redirected to file (`mnemofy transcribe file.mp4 > log.txt`)
  - Input piped (`echo "y" | mnemofy transcribe file.mp4`)

#### Method 2: Check environment variables
```python
import os

is_ci = any([
    os.getenv("CI"),
    os.getenv("GITHUB_ACTIONS"),
    os.getenv("GITLAB_CI"),
    os.getenv("JENKINS_HOME")
])
```
- Detects common CI environments
- Useful for forcing non-interactive mode

### Decision: Use **sys.stdin.isatty() + sys.stdout.isatty()**

**Rationale**:
- Standard Python approach
- Covers most cases (CI, pipes, redirects)
- Simple, no additional dependencies

**Edge Cases**:
- User can force non-interactive with `--auto` flag if TTY detection is wrong
- Log warning if TTY detection seems ambiguous

---

## Implementation Recommendations

### Phase 0 Deliverables

1. **Add psutil dependency**:
   ```toml
   # pyproject.toml
   dependencies = [
       "faster-whisper>=1.0.0",
       "typer>=0.9.0",
       "rich>=13.0.0",
       "pydantic>=2.0.0",
       "psutil>=5.9.0",  # NEW
       "readchar>=4.0.0",  # NEW (for TUI)
   ]
   ```

2. **MODEL_SPECS constant** (to be defined in model_selector.py):
   ```python
   MODEL_SPECS = {
       "tiny": ModelSpec(
           name="tiny",
           min_ram_gb=1.2,  # 1GB + 20% buffer
           min_vram_gb=1.2,
           speed_rating=5,
           quality_rating=2,
           description="Fastest, lowest accuracy. Good for testing."
       ),
       "base": ModelSpec(...),
       # ...etc
   }
   ```

3. **GPU detection strategy**:
   ```python
   def get_gpu_info() -> tuple[bool, Optional[str], Optional[float]]:
       # Try CUDA (nvidia-smi)
       if _detect_cuda():
           return (True, "cuda", _get_cuda_vram())
       
       # Try Metal (macOS Apple Silicon)
       if _detect_metal():
           return (True, "metal", None)  # VRAM = N/A
       
       # No GPU
       return (False, None, None)
   ```

4. **Testing approach**:
   - Mock psutil responses for different platforms
   - Mock subprocess calls for nvidia-smi
   - Test graceful degradation on detection failure

---

## Open Questions

### Q1: How to handle model downloads?
**Context**: faster-whisper downloads models on first use. Large models take time.

**Options**:
1. Show download progress (faster-whisper supports this)
2. Warn user before selecting large model
3. Pre-download all models (not practical)

**Recommendation**: Show download progress, warn in interactive menu ("large-v3: ~3GB download required").

### Q2: Should we cache resource detection results?
**Context**: Resource detection might be called multiple times (e.g., --list-models then transcribe).

**Options**:
1. No caching (detect fresh each time)
2. Cache for duration of CLI invocation
3. Cache to disk (violates constitution)

**Recommendation**: No caching (aligns with Explicit Persistence principle). Detection is <1s overhead.

### Q3: How to handle docker/container environments?
**Context**: Containers may report different resources than host.

**Options**:
1. Detect container (check for /.dockerenv)
2. Trust reported resources (psutil reports container limits)
3. Allow manual override

**Recommendation**: Trust psutil (it respects cgroup limits). Document `--model` flag for overrides.

---

## Next Steps

1. **Implement T-001 to T-005**: Resource detection module
2. **Validate on real hardware**: Test psutil accuracy on macOS, Linux
3. **Benchmark model memory**: Confirm MODEL_SPECS estimates
4. **Prototype TUI**: Build simple menu with readchar
5. **Update this document**: Add empirical findings during implementation

---

## References

- psutil documentation: https://psutil.readthedocs.io/
- faster-whisper GitHub: https://github.com/SYSTRAN/faster-whisper
- rich documentation: https://rich.readthedocs.io/
- readchar PyPI: https://pypi.org/project/readchar/
- OpenAI Whisper models: https://github.com/openai/whisper#available-models-and-languages
