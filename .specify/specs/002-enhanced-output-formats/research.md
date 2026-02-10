# Research Notes: Enhanced Output Formats

**Feature**: 002-enhanced-output-formats  
**Date**: 2026-02-10  
**Phase**: 0 (Research & Analysis)  
**Status**: Complete

---

## 1. SRT Format Specification

### SubRip Format Standard
SRT (SubRip) is the most widely compatible subtitle format. Each subtitle entry follows this structure:

```
1
00:00:01,000 --> 00:00:05,000
This is the first subtitle

2
00:00:10,000 --> 00:00:14,000
This is the second subtitle
```

### Timing Format Requirements
- **Format**: `HH:MM:SS,mmm --> HH:MM:SS,mmm`
- **Precision**: Milliseconds (3 decimal places)
- **Separator**: Comma `,` (NOT period `.`)
- **Arrows**: Two hyphens and `>` (` --> `)
- **Hours**: Can exceed 24 (no 00-23 limit)
- **Example**: `00:30:45,123 --> 00:30:50,456`

### Edge Cases & Handling
1. **Overlapping segments**: Merge or accept overlap (SRT editors handle this)
2. **Duration > 24 hours**: Support hours beyond 24 (e.g., `25:30:00,000`)
3. **Special characters**: Allowed in subtitle text; no escaping required
4. **Multi-line subtitles**: Empty line separates sequence number from timing from text
5. **Block separator**: Always blank line between subtitle entries
6. **No trailing content**: File should end after last subtitle text (no blank line needed)

### Validation Rules
✅ Valid:
- Milliseconds with leading zeros: `00:00:01,001`
- Long durations: `45:30:15,500`
- Multi-line text (up to practical limits)
- UTF-8 characters in subtitle text

❌ Invalid:
- Period instead of comma: `00:00:01.001` (breaks compatibility)
- Missing arrows: `00:00:01,000 > 00:00:05,000`
- Duplicate sequence numbers: Two subtitles numbered "1"
- No blank line separator: Sequences run together

### Editor Compatibility Testing
Recommended editors to validate SRT output:
1. **VLC Media Player** (free, cross-platform)
2. **Subtitle Edit** (free, Windows primary)
3. **Aegisub** (free, open-source, professional subtitle authoring)
4. **DaVinci Resolve** (professional video editor)

**Decision**: Validate against at least 2 editors. Critical requirement: all generated SRTs must pass VLC at minimum.

---

## 2. Python File Path Management

### Strategy: pathlib.Path Consistency
Use `pathlib.Path` throughout Feature 002 for cross-platform reliability.

### Path Construction Pattern
```python
from pathlib import Path

# Input video/audio
input_path = Path("/home/user/meeting.mp4")
basename = input_path.stem  # "meeting"
suffix = input_path.suffix  # ".mp4"

# Output directory (with default)
outdir = Path(outdir or input_path.parent)  # Default to input's parent
outdir.mkdir(parents=True, exist_ok=True)   # Create if needed

# Output files
audio_path = outdir / f"{basename}.mnemofy.wav"
txt_path = outdir / f"{basename}.transcript.txt"
srt_path = outdir / f"{basename}.transcript.srt"
json_path = outdir / f"{basename}.transcript.json"
notes_path = outdir / f"{basename}.notes.md"
```

### Cross-Platform Considerations
| Platform | Path Separator | Home Expansion | Example |
|----------|---|---|---|
| Linux/macOS | `/` | `~` works | `/home/user/output` |
| Windows | `\` (backslash) or `/` | `%USERPROFILE%` | `C:\Users\user\output` |

**`pathlib.Path` handles all transparently** - no need for manual OS detection.

### Path Validation
```python
def validate_output_dir(path: str) -> Path:
    """Validate output directory is writable."""
    p = Path(path).expanduser().resolve()  # Handle ~ and relative paths
    
    # Check if parent exists and is writable
    if p.exists():
        if not p.is_dir():
            raise ValueError(f"{p} is not a directory")
        if not os.access(p, os.W_OK):
            raise ValueError(f"{p} is not writable")
    else:
        # Try to create it
        try:
            p.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise ValueError(f"Cannot create {p}: permission denied")
    
    return p
```

### Decision
✅ **Use `pathlib.Path` exclusively** - avoid string concatenation for paths
- Provide paths to functions as `Path` objects
- Accept string input from CLI, convert immediately: `Path(user_input).resolve()`

---

## 3. JSON Schema Versioning

### Selected Format: "1.0" (Major.Minor)
Simpler than semantic versioning for data formats. Aligns with JSON Schema Draft specifications.

### Field Definition
```json
{
  "schema_version": "1.0",
  "transcription_engine_version": "faster-whisper-v20240101",
  "mnemofy_version": "0.8.0",
  "segments": [...]
}
```

### Versioning Strategy

**v1.0 to v1.1**: Minor additions (backward compatible)
- New optional fields in segments
- New optional metadata fields
- Old parsing code can ignore new fields

**v1.0 to v2.0**: Major breaking changes
- Removed fields
- Changed field types
- Restructured data layout

### Migration Guidance for Consumers
```python
def parse_transcript_json(data: dict) -> TranscriptData:
    schema_version = data.get("schema_version", "1.0")
    
    if schema_version.startswith("1."):
        return parse_v1_format(data)
    elif schema_version.startswith("2."):
        return parse_v2_format(data)
    else:
        raise ValueError(f"Unsupported schema version: {schema_version}")
```

### Decision
✅ **Include `schema_version: "1.0"` in all JSON output**
- Enables future format evolution
- Simple to check compatibility
- No impact on current parsing

---

## 4. FFmpeg Audio Extraction

### Command Strategy
```bash
ffmpeg -i input.mp4 -q:a 0 -map a output.wav
```

### Flag Explanations
- `-i input.mp4`: Input file
- `-q:a 0`: Quality: 0 = best quality (lossless/highest bitrate)
- `-map a`: Select audio stream (all if multiple)
- `output.wav`: Output file (forces WAV format via extension)

### Output Format Verification
```bash
ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate,channels,codec_name -of csv=p=0 output.wav
# Expected output: 16000,1,pcm_s16le (or similar)
# - 16000 Hz (16kHz sample rate)
# - 1 channel (mono)
# - pcm_s16le (16-bit PCM audio)
```

### Supported Input Formats
| Container | Codecs | Status |
|-----------|--------|--------|
| MP4 | H.264, H.265, AV1 + AAC, FLAC | ✅ Works |
| MKV | Any (Matroska container) | ✅ Works |
| MOV | Quicktime (typically H.264 + AAC) | ✅ Works |
| WebM | VP8/VP9 + Vorbis/Opus | ✅ Works |
| AVI | MPEG-4, DivX + MP3 | ✅ Works |
| FlV | H.264 + AAC | ✅ Works |

### Edge Case Handling

**1. Corrupted headers**:
```bash
ffmpeg -i input.mp4 -c:a pcm_s16le -ar 16000 -ac 1 output.wav
# -c:a pcm_s16le: Force PCM codec
# -ar 16000: Resample to 16kHz
# -ac 1: Convert to mono
```

**2. No audio stream**:
```bash
ffprobe -v error -select_streams a:0 input.mp4 | grep -q "Stream"
# Check returns non-zero if no audio
```

**3. Exotic codecs (OPUS, FLAC in container)**:
```bash
ffmpeg -i input.mkv -c:a pcm_s16le -ar 16000 -ac 1 output.wav
# Force reencoding to standard PCM
```

### Performance Characteristics
| Duration | Extraction Time | Speedup | Notes |
|----------|---|---|---|
| 30 seconds | ~1-2 sec | 15-30x | Fast |
| 1 hour | ~5-10 sec | 360-720x | Fast (I-frame optimization) |
| 4 hours | ~20-40 sec | 360-720x | Linear scaling |

**Factor**: Audio extraction typically 1-2% of video duration (much faster than playback).

### Decision
✅ **Use ffmpeg with sensible resampling options**:
```python
cmd = [
    "ffmpeg", "-i", str(input_path),
    "-q:a", "0",         # Best quality
    "-ar", "16000",      # Resample to 16kHz
    "-ac", "1",          # Mono
    "-c:a", "pcm_s16le", # Force PCM codec
    str(output_path)
]
```

Error handling: Check ffmpeg return code. If non-zero, report specific error to user.

---

## 5. Timestamp Precision & Handling

### faster-whisper Output
faster-whisper returns segments from `.transcribe()`:
```python
segments = model.transcribe("audio.wav", language="en")
# Returns: List[dict] with keys:
# - "id": int (segment index)
# - "seek": int (sample position)
# - "start": float (seconds, e.g., 1.23)
# - "end": float (seconds, e.g., 5.67)
# - "text": str (transcribed text)
# - "tokens": List[int]
# - "temperature": float
# - "avg_logprob": float
# - "compression_ratio": float
# - "no_speech_prob": float
```

### Conversion Strategy: Float to String (Early)
Convert timestamps immediately after transcription to avoid repeated conversions:

```python
def seconds_to_hms_format(seconds: float, format="txt") -> str:
    """
    Convert float seconds to appropriate format.
    
    Args:
        seconds: Duration in seconds (float)
        format: "txt" (HH:MM:SS), "srt" (HH:MM:SS,mmm), "json" (float)
    
    Returns:
        Formatted string or float
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if format == "txt":
        return f"{hours:02d}:{minutes:02d}:{int(secs):02d}"
    elif format == "srt":
        millis = int((secs % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(secs):02d},{millis:03d}"
    elif format == "json":
        return seconds  # Keep as float for JSON
    
    raise ValueError(f"Unknown format: {format}")
```

### Rounding Strategy: Round Half (Banker's Rounding)
Python's `round()` uses banker's rounding (round to nearest even):
```python
# milliseconds = int(round((secs % 1) * 1000))
# For millisecs in JSON: keep full float precision (not rounded)
```

### Precision Levels by Format
| Format | Precision | Example | Notes |
|--------|-----------|---------|-------|
| TXT | Seconds | `[00:01:23–00:01:27]` | Readable, no sub-second |
| SRT | Milliseconds | `00:01:23,450 --> 00:01:27,200` | SubRip standard |
| JSON | Float seconds | `"start": 83.45` | Preserve full precision |

### Decision
✅ **Format timestamps early after transcription**:
- SRT: `HH:MM:SS,mmm` (milliseconds, rounded banker's style)
- TXT: `HH:MM:SS` (seconds, truncated)
- JSON: Keep as float seconds (preserve precision for analysis)

---

## 6. Error Recovery Patterns

### Recoverable vs Non-Recoverable Errors

| Error Type | Recoverable? | Action |
|---|---|---|
| Write permission denied | ❌ No | Abort, clear error message |
| One formatter fails | ✅ Yes | Skip that formatter, complete others |
| Metadata field missing | ✅ Yes | Use default or empty value |
| 30s minimum not met | ✅ Yes | Skip notes generation only |
| Memory exhaustion | ❌ No | Abort with memory error message |
| Invalid input path | ❌ No | Abort with file not found |
| Transcription fails | ❌ No | Abort with transcription error |

### Best-Effort Error Handling Pattern
```python
def process_transcription(segments, metadata, output_manager):
    """Generate all formats with best-effort error recovery."""
    
    output_files = {}
    errors = []
    
    # Try each formatter
    formatters = {
        'txt': lambda: TranscriptFormatter.to_txt(segments),
        'srt': lambda: TranscriptFormatter.to_srt(segments),
        'json': lambda: TranscriptFormatter.to_json(segments, metadata),
    }
    
    for format_name, formatter_func in formatters.items():
        try:
            content = formatter_func()
            path = output_manager.get_transcript_paths()[format_name]
            path.write_text(content)
            output_files[format_name] = str(path)
            logger.info(f"Generated {format_name.upper()} transcript: {path}")
        except Exception as e:
            errors.append(f"Failed to generate {format_name.upper()}: {str(e)}")
            logger.warning(errors[-1])
    
    # Try notes generation
    try:
        if len(segments) >= 30:  # 30-second minimum
            notes = StructuredNotesGenerator('basic').generate(segments, metadata)
            path = output_manager.get_notes_path()
            path.write_text(notes)
            output_files['notes'] = str(path)
            logger.info(f"Generated notes: {path}")
    except Exception as e:
        errors.append(f"Failed to generate notes: {str(e)}")
        logger.warning(errors[-1])
    
    # Return success if at least one format generated
    if not output_files:
        raise RuntimeError(f"All formatters failed: {'; '.join(errors)}")
    
    if errors:
        logger.warning(f"Partial success: {len(errors)} formatter(s) failed")
    
    return output_files, errors
```

### Logging Strategy
```python
import logging

# Configure logging
logger = logging.getLogger('mnemofy.formatters')
logger.addHandler(logging.StreamHandler())  # stderr
logger.setLevel(logging.INFO)

# Usage:
logger.info(f"Generating transcript: {path}")      # Success info
logger.warning(f"Skipping SRT: {error_msg}")       # Recoverable error
logger.error(f"Cannot write to {path}")            # Non-recoverable error
```

### User-Facing Error Messages
```
✅ SUCCESS - Generated 4 output files:
  - meeting.transcript.txt
  - meeting.transcript.srt
  - meeting.transcript.json
  - meeting.notes.md

⚠️  WARNING - Skipped SRT generation (invalid timing)
              Partial output available in TXT and JSON

❌ ERROR - Cannot write to /output: Permission denied
```

### Decision
✅ **Best-effort approach with detailed logging**:
- Continue when one formatter fails
- Skip notes if <30 seconds
- Log all warnings and errors
- Return success if ≥1 format generated
- Fail only on non-recoverable errors (I/O, permissions, out of memory)

---

## 7. Format Validation Testing Strategy

### SRT Validation
Use the `srt` library for parsing and validation:
```bash
pip install srt
```

```python
import srt

def validate_srt(srt_content: str) -> tuple[bool, list[str]]:
    """Validate SRT format and timing consistency."""
    
    errors = []
    try:
        subtitles = list(srt.parse(srt_content))
        
        # Check sequencing
        for i, subtitle in enumerate(subtitles):
            if subtitle.index != i + 1:
                errors.append(f"Subtitle {i+1}: Index mismatch (got {subtitle.index})")
            
            # Check timing
            if subtitle.start >= subtitle.end:
                errors.append(f"Subtitle {i+1}: Start >= End")
            
            # Check for overlaps (warning, not error)
            if i > 0 and subtitles[i-1].end > subtitle.start:
                errors.append(f"Subtitle {i+1}: Overlaps with previous")
        
        return len(errors) == 0, errors
    except srt.SRTParseError as e:
        return False, [str(e)]
```

### JSON Validation
Use Python's built-in json module + optional jsonschema:
```python
import json
from jsonschema import validate, ValidationError

SCHEMA = {
    "type": "object",
    "required": ["schema_version", "metadata", "segments"],
    "properties": {
        "schema_version": {"type": "string"},
        "metadata": {
            "type": "object",
            "required": ["engine", "model", "language", "duration"],
            "properties": {
                "engine": {"type": "string"},
                "model": {"type": "string"},
                "language": {"type": "string"},
                "duration": {"type": "number"},
                "timestamp": {"type": "string"},
                "schema_version": {"type": "string"}
            }
        },
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["start", "end", "text"],
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "text": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            }
        }
    }
}

def validate_json(json_content: str) -> tuple[bool, list[str]]:
    """Validate JSON format and schema compliance."""
    errors = []
    try:
        data = json.loads(json_content)
        validate(instance=data, schema=SCHEMA)
        return True, []
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {str(e)}"]
    except ValidationError as e:
        return False, [f"Schema violation: {e.message}"]
```

### TXT Validation
Simple format checks:
```python
def validate_txt(txt_content: str) -> tuple[bool, list[str]]:
    """Validate TXT format and consistency."""
    errors = []
    lines = txt_content.strip().split('\n')
    
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        
        # Check timestamp format: [HH:MM:SS–HH:MM:SS]
        if line.startswith('['):
            if not line.startswith('[') or '–' not in line or not line.count(']'):
                errors.append(f"Line {i}: Invalid timestamp format")
    
    return len(errors) == 0, errors
```

### Test Fixtures Strategy
Minimal test samples:
```
tests/fixtures/
├── sample_30s.txt        # 30-second TXT (valid)
├── sample_30s.srt        # 30-second SRT (valid)
├── sample_30s.json       # 30-second JSON (valid)
├── invalid_srt.srt       # Missing blank lines
├── invalid_json.json     # Missing schema_version
└── malformed_txt.txt     # Wrong timestamp format
```

### Acceptance Criteria for Testing
✅ Valid format if:
- Parses without exceptions
- All required fields present
- Timing consistent (start < end)
- Segments in order (no backwards timing)

❌ Invalid format if:
- Parse errors
- Missing required fields
- Invalid timing relationships

### Decision
✅ **Use external libraries for validation**:
- `srt` library for SRT parsing
- `jsonschema` for JSON schema validation
- Custom simple regex for TXT format
- Comprehensive test fixtures in tests/fixtures/

---

## Summary of Key Decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| **SRT Timing** | Milliseconds (HH:MM:SS,mmm) | SubRip standard, editor compatible |
| **Path Handling** | pathlib.Path exclusively | Cross-platform, type-safe |
| **JSON Schema Version** | "1.0" (Major.Minor) | Simple, enables evolution |
| **FFmpeg Command** | `-q:a 0 -ar 16000 -ac 1` | Best quality, normalized output |
| **Timestamp Handling** | Float → String early | Avoid repeated conversions |
| **Error Strategy** | Best-effort (skip failed formatter) | Maximize partial output |
| **Format Validation** | External libraries + regex | Battle-tested parsers |

---

## Open Questions Resolved

✅ **All 7 research areas addressed**
- SRT specification understood → millisecond precision required
- Path management strategy → pathlib.Path throughout
- JSON versioning → "1.0" format with migration path
- FFmpeg extraction → sensible defaults with quality preset
- Timestamp precision → float precision in JSON, milliseconds in SRT
- Error recovery → best-effort with detailed logging
- Format validation → external libraries + test fixtures

---

## Next Steps

**Phase 1: Design** (Ready to proceed)
1. Create `data-model.md` (Segment, Metadata, Notes structures)
2. Create `contracts/` (OutputManager, Formatters, StructuredNotesGenerator, CLI)
3. Create `quickstart.md` (examples and integration test guide)
4. Update agent context with implementation patterns

See [PHASE_0_1_TASKS.md](./PHASE_0_1_TASKS.md) for Phase 1 detailed tasks.

---

**Status**: ✅ **PHASE 0 RESEARCH COMPLETE**  
**Date Completed**: 2026-02-10  
**All Gate Clearances Passed**: ✅

