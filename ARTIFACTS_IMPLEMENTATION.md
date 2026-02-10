# Model-Aware Artifacts Implementation Summary

## Overview

Added comprehensive model tracking and metadata enrichment to mnemofy, enabling users to understand which models were used for each artifact and providing detailed processing metadata.

## Changes Made

### 1. New Module: `artifacts.py`

Created a comprehensive artifact metadata system with dataclasses:

- **`ASREngineInfo`**: Captures ASR model details (engine, model name, size, ratings)
- **`LLMEngineInfo`**: Captures LLM model details (engine, model name, purpose)
- **`ProcessingConfig`**: Documents processing settings (language, normalization, meeting type, etc.)
- **`ProcessingMetadata`**: Complete processing pipeline metadata
- **`ArtifactInfo`**: Metadata for individual generated files
- **`ArtifactManifest`**: Index of all generated artifacts

**Key Features:**
- JSON serialization support
- Factory functions for easy creation
- Comprehensive field validation
- Extensible design for future enhancements

### 2. Enhanced `output_manager.py`

Added new path management methods:

```python
# New methods
manager.get_metadata_path()              # {basename}.metadata.json
manager.get_artifacts_manifest_path()    # {basename}.artifacts.json
manager.get_model_aware_transcript_paths(model_name)  # {basename}.{model}.transcript.{ext}
```

**Benefits:**
- Consistent path naming across all artifacts
- Support for model-specific file naming
- Enables side-by-side model comparison

### 3. Updated `cli.py`

**Imports Added:**
- Imported all artifact dataclasses
- Added `MODEL_SPECS` for model metadata enrichment
- Added timing and datetime support

**Processing Flow Changes:**
1. **Start Timing**: Capture `process_start_time` at beginning
2. **Enrich Transcript Metadata**: Add model specs, ratings, preprocessing flags
3. **Generate Processing Metadata**: After all processing completes
4. **Create Artifacts Manifest**: Index all generated files
5. **Save Metadata Files**: Write `.metadata.json` and `.artifacts.json`
6. **Enhanced Output Display**: Show metadata file paths

**Metadata Captured:**
- ASR model: name, size, quality/speed ratings
- LLM model (if used): name, purpose (classification, notes, repair)
- Processing config: language, flags, meeting type, modes
- Statistics: word count, segment count, duration
- Timing: start, end, total processing time

### 4. Enhanced `formatters.py`

Updated `TranscriptFormatter.to_json()` to auto-enrich metadata:

```python
# New auto-enriched fields
metadata["generated_at"]     # ISO timestamp
metadata["segment_count"]    # Number of segments
metadata["word_count"]       # Total words
```

**Benefits:**
- Automatic metadata enrichment
- Consistent timestamp format
- No breaking changes to existing code

### 5. New Tests

Created comprehensive test suites:

**`test_artifacts.py`** (250+ lines):
- Test all dataclass creation
- Test JSON serialization
- Test factory functions
- Test manifest building
- Test metadata enrichment

**`test_output_manager_enhancements.py`** (180+ lines):
- Test new path methods
- Test model-aware naming
- Test path consistency
- Test default vs custom outdir

### 6. Documentation

**`docs/MODEL_AWARE_ARTIFACTS.md`**:
- Feature overview
- JSON schema examples
- API usage guide
- Use cases and benefits
- Migration guide

## Files Modified

```
src/mnemofy/
  ├── artifacts.py              [NEW - 300 lines]
  ├── cli.py                    [MODIFIED - added metadata generation]
  ├── formatters.py             [MODIFIED - enriched JSON output]
  └── output_manager.py         [MODIFIED - added metadata paths]

tests/
  ├── test_artifacts.py         [NEW - 250 lines]
  └── test_output_manager_enhancements.py  [NEW - 180 lines]

docs/
  └── MODEL_AWARE_ARTIFACTS.md  [NEW - comprehensive guide]
```

## Example Output

### Before
```
Output files generated:
  Transcript (TXT): meeting.transcript.txt
  Subtitle (SRT): meeting.transcript.srt
  Structured (JSON): meeting.transcript.json
  Notes: meeting.notes.md
```

### After
```
Output files generated:
  Transcript (TXT): meeting.transcript.txt
  Subtitle (SRT): meeting.transcript.srt
  Structured (JSON): meeting.transcript.json  [ENRICHED ✨]
  Meeting Type: meeting.meeting-type.json
  Notes: meeting.notes.md
Metadata:
  Processing Info: meeting.metadata.json      [NEW ✨]
  Artifacts Index: meeting.artifacts.json     [NEW ✨]
```

## Key Benefits

1. **Transparency**: See which models processed your data
2. **Traceability**: Complete audit trail of processing pipeline
3. **Reproducibility**: Recreate processing with exact configuration
4. **Model Comparison**: Support for comparing outputs from different models
5. **Cost Tracking**: Monitor LLM usage across runs
6. **Automation Ready**: Programmatic access to metadata for workflows

## Backward Compatibility

✅ **100% backward compatible**
- All existing functionality unchanged
- Standard file paths remain the same
- New features are additive only
- Model-aware paths are opt-in

## API Examples

### Access Metadata in Code

```python
import json

# Read processing metadata
with open("meeting.metadata.json") as f:
    metadata = json.load(f)
    
print(f"ASR Model: {metadata['asr_engine']['model']}")
print(f"LLM Model: {metadata['llm_engine']['model']}")
print(f"Processing Time: {metadata['duration_seconds']}s")

# Read artifacts manifest
with open("meeting.artifacts.json") as f:
    manifest = json.load(f)
    
total_size_mb = manifest['total_size_bytes'] / (1024 * 1024)
print(f"Total Output Size: {total_size_mb:.2f} MB")
```

### Generate Model-Aware Paths

```python
from mnemofy.output_manager import OutputManager

manager = OutputManager("meeting.mp4")

# Compare outputs from different models
for model in ["tiny", "base", "small"]:
    paths = manager.get_model_aware_transcript_paths(model)
    print(f"{model}: {paths['json']}")
    
# Output:
# tiny: meeting.tiny.transcript.json
# base: meeting.base.transcript.json
# small: meeting.small.transcript.json
```

## Testing

Created comprehensive test suites covering:
- ✅ Dataclass creation and validation
- ✅ JSON serialization/deserialization
- ✅ Factory function behavior
- ✅ Path generation consistency
- ✅ Metadata enrichment
- ✅ Manifest building

Run tests with:
```bash
python -m pytest tests/test_artifacts.py -v
python -m pytest tests/test_output_manager_enhancements.py -v
```

## Summary

This implementation adds powerful metadata tracking and model awareness to mnemofy while maintaining full backward compatibility. Users can now:

1. **Track** which models were used for each artifact
2. **Audit** the complete processing pipeline
3. **Compare** outputs from different models
4. **Automate** workflows using metadata
5. **Understand** processing costs and performance

All changes are non-breaking and additive, ensuring existing users see no disruption while new users benefit from enhanced transparency and traceability.
