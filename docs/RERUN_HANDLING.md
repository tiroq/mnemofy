# Handling Transcription Reruns

## Overview

When running transcription multiple times on the same input file, mnemofy provides features to prevent data loss and enable model comparison.

## Default Behavior (Overwrites)

By default, reruns **overwrite** previous results:

```bash
# First run with base model
mnemofy transcribe meeting.mp4 --model base
# Creates: meeting.transcript.{txt,srt,json}, meeting.notes.md, etc.

# Second run with small model (OVERWRITES previous results)
mnemofy transcribe meeting.mp4 --model small
# Overwrites: meeting.transcript.{txt,srt,json}, meeting.notes.md, etc.
```

**Result:** Only the latest run's outputs are preserved.

## Model-Suffixed Mode (Preserve & Compare)

Use `--model-suffix` to include the model name in filenames, preventing overwrites and enabling side-by-side comparison:

```bash
# First run with base model
mnemofy transcribe meeting.mp4 --model base --model-suffix
# Creates: meeting.base.transcript.{txt,srt,json}
#          meeting.base.metadata.json
#          meeting.base.artifacts.json
#          meeting.notes.md (no suffix)

# Second run with small model (PRESERVES previous results)
mnemofy transcribe meeting.mp4 --model small --model-suffix  
# Creates: meeting.small.transcript.{txt,srt,json}
#          meeting.small.metadata.json
#          meeting.small.artifacts.json
#          meeting.notes.md (overwrites)

# Third run with medium model
mnemofy transcribe meeting.mp4 --model medium --model-suffix
# Creates: meeting.medium.transcript.{txt,srt,json}
#          meeting.medium.metadata.json
#          meeting.medium.artifacts.json
```

**Result:** All model outputs preserved. You can now compare:

```
meeting.mp4
├── meeting.base.transcript.txt
├── meeting.base.transcript.json
├── meeting.base.metadata.json
├── meeting.base.artifacts.json
├── meeting.small.transcript.txt
├── meeting.small.transcript.json
├── meeting.small.metadata.json
├── meeting.small.artifacts.json
├── meeting.medium.transcript.txt
├── meeting.medium.transcript.json
├── meeting.medium.metadata.json
├── meeting.medium.artifacts.json
├── meeting.notes.md              # Latest only
└── meeting.run-history.jsonl     # Appends all runs
```

### Files That Get Model Suffix

With `--model-suffix`:
- ✅ `*.transcript.txt` → `*.{model}.transcript.txt`
- ✅ `*.transcript.srt` → `*.{model}.transcript.srt`
- ✅ `*.transcript.json` → `*.{model}.transcript.json`
- ✅ `*.metadata.json` → `*.{model}.metadata.json`
- ✅ `*.artifacts.json` → `*.{model}.artifacts.json`

### Files That DON'T Get Model Suffix

- ❌ `*.notes.md` - Always latest (or use `--output` to specify different names)
- ❌ `*.meeting-type.json` - Latest classification
- ❌ `*.changes.md` - Latest changes log
- ❌ `*.mnemofy.wav` - Extracted audio (shared across runs)

## Run History Tracking

Every run is automatically logged to `*.run-history.jsonl` (JSONL format - one JSON object per line):

```jsonl
{"timestamp": "2026-02-11T10:00:00", "model": "base", "duration_seconds": 45.2, "transcript_duration": 285.5, "word_count": 1523, "segment_count": 45, "config": {...}}
{"timestamp": "2026-02-11T10:05:00", "model": "small", "duration_seconds": 67.8, "transcript_duration": 285.5, "word_count": 1587, "segment_count": 43, "config": {...}}
{"timestamp": "2026-02-11T10:15:00", "model": "medium", "duration_seconds": 125.3, "transcript_duration": 285.5, "word_count": 1612, "segment_count": 42, "config": {...}}
```

**Benefits:**
- Tracks all runs regardless of `--model-suffix` usage
- Append-only (never overwrites)
- Includes timing, word counts, configuration
- Enables performance comparison across models

## Comparing Model Runs

### Manual Comparison

Compare transcript quality:

```bash
# Compare word counts
wc -w meeting.base.transcript.txt meeting.small.transcript.txt meeting.medium.transcript.txt

# Compare JSON metadata
jq '.metadata.word_count' meeting.*.transcript.json

# Check processing time
jq '.duration_seconds' meeting.*.metadata.json
```

### Using the Comparison Script

Use the provided `compare_model_runs.py` script:

```bash
python examples/compare_model_runs.py meeting.run-history.jsonl
```

**Output:**

```
MODEL RUN COMPARISON
===================================================================================================
#   Date                Model        Duration   Transcript Words    Segments Config
---------------------------------------------------------------------------------------------------
1   2026-02-11 10:00    base         45.2s      285.5s     1523     45       lang=en
2   2026-02-11 10:05    small        67.8s      285.5s     1587     43       lang=en,norm
3   2026-02-11 10:15    medium       125.3s     285.5s     1612     42       lang=en,norm
===================================================================================================

MODEL PERFORMANCE ANALYSIS
===================================================================================================
Model: base
  Runs: 1
  Avg Processing Time: 45.20s
  Avg Word Count: 1523
  Avg Segments: 45

Model: small
  Runs: 1
  Avg Processing Time: 67.80s
  Avg Word Count: 1587
  Avg Segments: 43
  
...

RECOMMENDATIONS
===================================================================================================
⚡ Fastest: base (45.2s)
🎯 Best Quality: medium (1612 words)
⚖️  Balanced: small (speed rank: 2/3, quality rank: 2/3)
```

## Use Cases

### 1. Quality Benchmarking

Compare different models on the same audio:

```bash
for model in tiny base small medium; do
  mnemofy transcribe speech.mp4 --model $model --model-suffix --auto
done

# Compare results
python examples/compare_model_runs.py speech.run-history.jsonl
```

### 2. Preprocessing Comparison

Test normalization impact:

```bash
# Without normalization
mnemofy transcribe meeting.mp4 --model base --model-suffix

# With normalization (different config, same model)
mnemofy transcribe meeting.mp4 --model base --normalize --model-suffix
# Note: Will overwrite base.transcript.* since model name is the same
# Recommendation: Use different outdir or manually rename files
```

### 3. Development vs Production

Keep development experiments separate:

```bash
# Development: experiment with models
mnemofy transcribe meeting.mp4 --model small --model-suffix --outdir ./dev/

# Production: final approved model
mnemofy transcribe meeting.mp4 --model base --outdir ./prod/
```

## Best Practices

### ✅ DO:

1. **Use `--model-suffix` when comparing models**
   ```bash
   mnemofy transcribe meeting.mp4 --model base --model-suffix
   mnemofy transcribe meeting.mp4 --model small --model-suffix
   ```

2. **Check run history before reruns**
   ```bash
   cat meeting.run-history.jsonl | jq '.model'
   ```

3. **Use different `--outdir` for experiments**
   ```bash
   mnemofy transcribe meeting.mp4 --model tiny --outdir ./experiments/
   ```

4. **Preserve important runs in separate directories**
   ```bash
   mkdir -p results/base results/small
   mnemofy transcribe meeting.mp4 --model base --outdir results/base/
   mnemofy transcribe meeting.mp4 --model small --outdir results/small/
   ```

### ❌ DON'T:

1. **Don't forget `--model-suffix` when comparing**
   - Without it, each run overwrites the previous one

2. **Don't rely on notes.md preservation**
   - Notes are always overwritten (use `--output` for custom names)

3. **Don't delete `run-history.jsonl`**
   - It's the only record of all runs if you forget `--model-suffix`

## API Usage

For programmatic use, leverage model-aware paths:

```python
from mnemofy.output_manager import OutputManager

manager = OutputManager("meeting.mp4")

# Get model-specific paths
base_paths = manager.get_model_aware_transcript_paths("base")
small_paths = manager.get_model_aware_transcript_paths("small")

print(base_paths["json"])   # meeting.base.transcript.json
print(small_paths["json"])  # meeting.small.transcript.json

# Read and compare
import json

with open(base_paths["json"]) as f:
    base_data = json.load(f)
    
with open(small_paths["json"]) as f:
    small_data = json.load(f)

print(f"Base: {base_data['metadata']['word_count']} words")
print(f"Small: {small_data['metadata']['word_count']} words")
```

## Cleaning Up

Remove all model-suffixed outputs:

```bash
# Remove all base model outputs
rm meeting.base.*

# Remove all model variants, keep latest
rm meeting.{tiny,base,small,medium}.*

# Keep only run history
rm meeting.* 
# (excluding .run-history.jsonl)
```

## Summary

| Scenario | Command | Result |
|----------|---------|--------|
| **Single run** | `mnemofy transcribe meeting.mp4` | Standard outputs, overwrites on rerun |
| **Compare models** | `mnemofy transcribe meeting.mp4 --model base --model-suffix`<br>`mnemofy transcribe meeting.mp4 --model small --model-suffix` | Preserves both outputs with model names |
| **Track all runs** | Any run automatically logs to `*.run-history.jsonl` | Append-only history for analysis |
| **Separate experiments** | `--outdir ./experiments/` | Isolate outputs by directory |

With these features, you can safely rerun transcriptions, compare model performance, and maintain a complete audit trail of all processing runs!
