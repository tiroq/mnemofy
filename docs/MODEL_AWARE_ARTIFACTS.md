# Model-Aware Artifacts and Enriched Metadata

## Overview

Mnemofy now includes enriched metadata and artifact management to provide comprehensive visibility into the processing pipeline, including which models were used for transcription, classification, and notes generation.

## What's New

### 1. **Enriched Transcript JSON Metadata**

The transcript JSON files now include detailed model information:

```json
{
  "schema_version": "1.0",
  "metadata": {
    "engine": "faster-whisper",
    "model": "base",
    "model_size_gb": 1.5,
    "quality_rating": 3,
    "speed_rating": 5,
    "language": "en",
    "duration": 285.5,
    "generated_at": "2026-02-10T14:30:00",
    "segment_count": 45,
    "word_count": 1523,
    "preprocessing": {
      "normalized": true,
      "repaired": false,
      "remove_fillers": false
    }
  },
  "segments": [...]
}
```

**New Fields:**
- `model_size_gb`: Approximate model size in GB
- `quality_rating`: Model quality rating (1-5)
- `speed_rating`: Model speed rating (1-5)
- `generated_at`: ISO timestamp of generation
- `segment_count`: Number of transcript segments
- `word_count`: Total word count
- `preprocessing`: Flags indicating applied transformations

### 2. **Processing Metadata Artifact**

A new `.metadata.json` file captures the complete processing pipeline:

**File:** `<basename>.metadata.json`

```json
{
  "schema_version": "1.0",
  "input_file": "meeting.mp4",
  "start_timestamp": "2026-02-10T14:25:00",
  "end_timestamp": "2026-02-10T14:30:45",
  "duration_seconds": 345.2,
  "asr_engine": {
    "engine": "faster-whisper",
    "model": "base",
    "model_size_gb": 1.5,
    "quality_rating": 3,
    "speed_rating": 5
  },
  "llm_engine": {
    "engine": "openai",
    "model": "gpt-4o-mini",
    "purpose": "meeting_type_detection, notes_generation"
  },
  "config": {
    "language": "en",
    "normalize": true,
    "repair": false,
    "meeting_type": "status",
    "classify_mode": "llm",
    "notes_mode": "llm"
  },
  "language_detected": "en",
  "transcript_duration_seconds": 285.5,
  "word_count": 1523,
  "segment_count": 45
}
```

**Use Cases:**
- Audit which models were used for processing
- Reproduce processing with same configuration
- Track processing time and performance
- Understand LLM usage for cost tracking

### 3. **Artifacts Manifest**

A new `.artifacts.json` file indexes all generated files:

**File:** `<basename>.artifacts.json`

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-02-10T14:30:45",
  "input_file": "meeting.mp4",
  "model_name": "base",
  "total_size_bytes": 45678,
  "artifacts_by_type": {
    "transcript": [
      {
        "path": "meeting.transcript.txt",
        "format": "txt",
        "description": "Plain text transcript with timestamps",
        "size_bytes": 12345,
        "model_used": "base"
      },
      {
        "path": "meeting.transcript.srt",
        "format": "srt",
        "description": "SubRip subtitle format transcript",
        "size_bytes": 13456,
        "model_used": "base"
      },
      {
        "path": "meeting.transcript.json",
        "format": "json",
        "description": "Structured JSON transcript with metadata",
        "size_bytes": 15234,
        "model_used": "base",
        "schema_version": "1.0"
      }
    ],
    "notes": [
      {
        "path": "meeting.notes.md",
        "format": "md",
        "description": "Structured meeting notes",
        "size_bytes": 3456,
        "model_used": "gpt-4o-mini"
      }
    ],
    "classification": [
      {
        "path": "meeting.meeting-type.json",
        "format": "json",
        "description": "Meeting type classification result",
        "size_bytes": 567,
        "model_used": "gpt-4o-mini"
      }
    ],
    "metadata": [
      {
        "path": "meeting.metadata.json",
        "format": "json",
        "description": "Processing metadata and configuration",
        "size_bytes": 620,
        "schema_version": "1.0"
      }
    ]
  }
}
```

**Use Cases:**
- Understand which files were generated
- Track which model generated each artifact
- Calculate total storage usage
- Automate batch processing workflows

### 4. **Model-Aware File Naming (API)**

The `OutputManager` now supports model-aware file naming:

```python
from mnemofy.output_manager import OutputManager

manager = OutputManager("meeting.mp4")

# Standard paths (no model in filename)
paths = manager.get_transcript_paths()
# {'txt': 'meeting.transcript.txt', ...}

# Model-aware paths (model name in filename)
paths = manager.get_model_aware_transcript_paths("base")
# {'txt': 'meeting.base.transcript.txt', ...}

# Different models can coexist
base_paths = manager.get_model_aware_transcript_paths("base")
small_paths = manager.get_model_aware_transcript_paths("small")
```

**Pattern:** `{basename}.{model}.transcript.{ext}`

**Use Case:** Compare outputs from different models side-by-side.

## File Output Summary

After processing, you'll now see:

```
Output files generated:
  Transcript (TXT): meeting.transcript.txt
  Subtitle (SRT): meeting.transcript.srt
  Structured (JSON): meeting.transcript.json
  Meeting Type: meeting.meeting-type.json
  Notes: meeting.notes.md
Metadata:
  Processing Info: meeting.metadata.json
  Artifacts Index: meeting.artifacts.json
```

## API Usage

### Creating Processing Metadata

```python
from datetime import datetime
from mnemofy.artifacts import (
    create_processing_metadata,
    ASREngineInfo,
    ProcessingConfig,
)

# Define ASR engine info
asr_info = ASREngineInfo(
    engine="faster-whisper",
    model="small",
    model_size_gb=2.5,
    quality_rating=3,
    speed_rating=4,
)

# Define processing config
config = ProcessingConfig(
    language="en",
    normalize=True,
    meeting_type="planning",
    notes_mode="llm",
)

# Create metadata
metadata = create_processing_metadata(
    input_file="meeting.mp4",
    asr_engine=asr_info,
    config=config,
    start_time=datetime.now(),
    end_time=datetime.now(),
    word_count=2000,
    segment_count=60,
)

# Save to file
with open("meeting.metadata.json", "w") as f:
    f.write(metadata.to_json())
```

### Creating Artifact Manifest

```python
from mnemofy.artifacts import create_artifact_manifest

# Create manifest
manifest = create_artifact_manifest(
    input_file="meeting.mp4",
    model_name="small",
)

# Add artifacts
manifest.add_artifact(
    artifact_type="transcript",
    path="meeting.transcript.json",
    format="json",
    description="Structured transcript",
    size_bytes=15000,
    model_used="small",
    schema_version="1.0",
)

manifest.add_artifact(
    artifact_type="notes",
    path="meeting.notes.md",
    format="md",
    description="Meeting notes",
    size_bytes=3500,
    model_used="gpt-4o-mini",
)

# Save to file
with open("meeting.artifacts.json", "w") as f:
    f.write(manifest.to_json())
```

## Benefits

1. **Transparency**: Know exactly which models processed your data
2. **Reproducibility**: Recreate processing with same configuration
3. **Auditability**: Track what was generated, when, and how
4. **Cost Tracking**: Monitor LLM usage across processing runs
5. **Model Comparison**: Compare outputs from different models
6. **Automation**: Build workflows that inspect metadata programmatically

## Backward Compatibility

All existing functionality remains unchanged. The new features are additive:
- Standard transcript paths remain the same
- Existing code continues to work without modification
- New metadata files are generated automatically
- Model-aware paths are opt-in via API

## Future Enhancements

Potential future additions:
- Model performance benchmarking data
- Token usage tracking for LLM calls
- Confidence scores per segment
- Alternative model recommendations
- Batch processing with model rotation
