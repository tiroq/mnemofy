# Data Model: Enhanced Output Formats

**Feature**: 002-enhanced-output-formats  
**Phase**: 1 (Design - Data Models)  
**Reference**: [research.md](./research.md)

---

## Segment Structure

A single transcript segment with timing and content.

```python
from typing import TypedDict, Optional
from dataclasses import dataclass

# As TypedDict (from faster-whisper)
class Segment(TypedDict):
    """Transcript segment from faster-whisper.transcribe()."""
    id: int                      # Segment index
    seek: int                    # Sample position in audio
    start: float                 # Start time in seconds
    end: float                   # End time in seconds
    text: str                    # Transcribed text
    tokens: list[int]            # Token IDs
    temperature: float           # Decoding temperature
    avg_logprob: float           # Average log probability
    compression_ratio: float     # Compression ratio metric
    no_speech_prob: float        # Probability no speech detected

# Alternative: as dataclass for type safety
@dataclass
class TranscriptSegment:
    """Type-safe segment representation."""
    start: float                 # Seconds
    end: float                   # Seconds
    text: str                    # Transcribed text
    confidence: Optional[float] = None  # 0.0-1.0 (optional)
```

**Usage**:
```python
# From faster-whisper
segments = model.transcribe("audio.wav")  # Returns list[dict] (TypedDict)

# For Feature 002, normalize to:
for seg in segments:
    start_ms = int(seg['start'] * 1000)
    end_ms = int(seg['end'] * 1000)
    # Use in formatters
```

---

## Metadata Structure

Transcription metadata for all output files.

```python
from typing import TypedDict
from datetime import datetime

class Metadata(TypedDict, total=False):
    """Transcription metadata."""
    # Required
    engine: str                          # "faster-whisper"
    model: str                           # "tiny", "base", "small", "medium", "large"
    language: str                        # "en", "es", "fr" (ISO 639-1)
    duration: float                      # Total audio duration in seconds
    
    # Optional but recommended
    timestamp: str                       # ISO 8601: "2026-02-10T14:30:45Z"
    schema_version: str                  # "1.0" for Feature 002
    transcription_engine_version: str    # e.g., "faster-whisper-v20240101"
    mnemofy_version: str                 # e.g., "0.8.0"
    input_file: str                      # Original filename
    language_detected: bool              # Was language auto-detected?
```

**Example Metadata**:
```python
metadata = {
    "engine": "faster-whisper",
    "model": "base",
    "language": "en",
    "duration": 125.45,
    "timestamp": "2026-02-10T14:30:45Z",
    "schema_version": "1.0",
    "transcription_engine_version": "faster-whisper-v20240101",
    "mnemofy_version": "0.8.0",
    "input_file": "meeting.mp4",
    "language_detected": False
}
```

---

## Output File Paths

StandardOutputManager generates these paths.

```python
from pathlib import Path

class OutputPaths(TypedDict):
    """All output file paths for a transcription."""
    audio: Path                          # meeting.mnemofy.wav
    transcript_txt: Path                 # meeting.transcript.txt
    transcript_srt: Path                 # meeting.transcript.srt
    transcript_json: Path                # meeting.transcript.json
    notes: Path                          # meeting.notes.md

# Example generation
input_path = Path("/home/user/meeting.mp4")
outdir = Path("/output")
basename = input_path.stem  # "meeting"

paths = {
    "audio": outdir / f"{basename}.mnemofy.wav",
    "transcript_txt": outdir / f"{basename}.transcript.txt",
    "transcript_srt": outdir / f"{basename}.transcript.srt",
    "transcript_json": outdir / f"{basename}.transcript.json",
    "notes": outdir / f"{basename}.notes.md"
}
```

---

## Notes Section Structures

The 7 required sections in `.notes.md` output.

### Section 1: Metadata
```markdown
# Meeting Notes: Meeting Title

**Date**: 2026-02-10  
**Source**: meeting.mp4 (125 seconds)  
**Language**: English (en)  
**Engine**: faster-whisper (base model)  
**Generated**: 2026-02-10 14:30:45 UTC
```

**Data Structure**:
```python
class NotesMetadata(TypedDict):
    title: str                           # Meeting title (from filename or user)
    date: str                            # ISO 8601 date
    source_file: str                     # Original video/audio filename
    duration: str                        # "2m 5s" or "125 seconds"
    language: str                        # "English (en)"
    engine: str                          # "faster-whisper (base model)"
    generated: str                       # ISO 8601 timestamp
```

### Section 2: Topics
```markdown
## Topics

- **[00:00–00:30]** Project kickoff and Q1 goals
- **[00:30–01:15]** Engineering roadmap priorities
- **[01:15–02:05]** Budget and resource allocation
```

**Data Structure**:
```python
class Topic(TypedDict):
    start_time: str                      # "00:00" (HH:MM)
    end_time: str                        # "00:30" (HH:MM)
    description: str                     # Topic summary
    keywords: list[str]                  # Optional: ["kickoff", "goals"]

Topics = list[Topic]
```

### Section 3: Decisions
```markdown
## Decisions

- **[00:45]** Approved Q1 budget: $2.5M
- **[01:20]** Postpone mobile rewrite to Q3
- No explicit decisions found in final segment

*Note: Only explicit decision statements are listed (deterministic extraction).*
```

**Data Structure**:
```python
class Decision(TypedDict):
    timestamp: str                       # "00:45" (HH:MM)
    statement: str                       # Decision summary
    context: str                         # Optional surrounding context

Decisions = list[Decision]
```

### Section 4: Action Items
```markdown
## Action Items

- **[01:10]** John: Complete RFP by Feb 15
- **[01:35]** Sarah: Review architecture docs before meeting
- **[01:50]** Team: Schedule follow-up for Feb 17

*Format: [timestamp] Owner: Task*
```

**Data Structure**:
```python
class ActionItem(TypedDict):
    timestamp: str                       # "01:10" (HH:MM)
    owner: str                           # Person assigned (or "Team")
    task: str                            # What needs to be done
    due_date: Optional[str]              # Optional: "Feb 15"

ActionItems = list[ActionItem]
```

### Section 5: Concrete Mentions
```markdown
## Concrete Mentions

### Names
- Alice Johnson (budget discussion)
- Bob Chen (technical lead)

### Numbers & Metrics
- Q1 budget: $2.5M [00:45]
- Timeline: 6-week sprint [01:20]
- Performance target: 99.9% uptime [02:00]

### URLs & References
- https://github.com/team/roadmap (mentioned at [01:15])

*Extracted from transcript with timestamps.*
```

**Data Structure**:
```python
class Mention(TypedDict):
    type: str                            # "name", "number", "url"
    value: str                           # The actual mention
    context: str                         # Surrounding text
    timestamp: str                       # "00:45" (HH:MM)

ConcreteM mentions = list[Mention]
```

### Section 6: Risks & Open Questions
```markdown
## Risks & Open Questions

### Risks
- Budget allocation may be insufficient for Q1 goals
- Mobile rewrite postponement could impact user satisfaction

### Open Questions
- When will marketing finalize campaign budget?
- What's the process for cross-team conflict resolution?
- Has performance baseline been established?

*Items marked as uncertain or conditional in transcript.*
```

**Data Structure**:
```python
class RiskOrQuestion(TypedDict):
    category: str                        # "risk" or "question"
    statement: str                       # Risk or question text
    timestamp: str                       # "01:20" (HH:MM)
    confidence: str                      # "high", "medium", "low"

RisksAndQuestions = list[RiskOrQuestion]
```

### Section 7: Transcript Links
```markdown
## Transcript Files

- **Full Transcript (TXT)**: [meeting.transcript.txt](meeting.transcript.txt)
- **Subtitle Format (SRT)**: [meeting.transcript.srt](meeting.transcript.srt)
- **Structured Data (JSON)**: [meeting.transcript.json](meeting.transcript.json)
- **Audio (WAV)**: [meeting.mnemofy.wav](meeting.mnemofy.wav)

All files saved to: `/output`
```

**Data Structure**:
```python
class TranscriptLink(TypedDict):
    format: str                          # "txt", "srt", "json", "audio"
    filename: str                        # "meeting.transcript.txt"
    path: str                            # "/output/meeting.transcript.txt"
    size_bytes: int                      # File size

TranscriptLinks = list[TranscriptLink]
```

---

## Complete Notes Document Structure

```python
from typing import TypedDict

class StructuredNotes(TypedDict):
    """Complete structured meeting notes."""
    metadata: NotesMetadata
    topics: Topics                       # Section 2
    decisions: Decisions                 # Section 3
    action_items: ActionItems            # Section 4
    concrete_mentions: list[Mention]     # Section 5
    risks_and_questions: list[RiskOrQuestion]  # Section 6
    transcript_links: list[TranscriptLink]     # Section 7
```

---

## TXT Format Structure

Line-by-line timestamps with text.

```
[00:00:01–00:00:05] This is the first segment of the meeting
[00:00:05–00:00:10] We're discussing project timelines
[00:00:10–00:00:15] The deadline is Q1 2026

[00:01:30–00:01:35] Let's talk about budget allocation
...
```

**Pattern**: `[HH:MM:SS–HH:MM:SS] text`
- Start and end times in seconds precision
- En-dash (–) as separator
- Text content following space

---

## SRT Format Structure

SubRip subtitle format with millisecond precision.

```
1
00:00:01,000 --> 00:00:05,000
This is the first segment of the meeting

2
00:00:05,000 --> 00:00:10,000
We're discussing project timelines

3
00:00:10,000 --> 00:00:15,000
The deadline is Q1 2026
```

**Pattern**: 
- Sequence number
- Timing: `HH:MM:SS,mmm --> HH:MM:SS,mmm`
- Text (can be multi-line)
- Blank line separator

---

## JSON Format Structure

Structured JSON with metadata and segments.

```json
{
  "schema_version": "1.0",
  "metadata": {
    "engine": "faster-whisper",
    "model": "base",
    "language": "en",
    "duration": 95.5,
    "timestamp": "2026-02-10T14:30:45Z",
    "transcription_engine_version": "faster-whisper-v20240101",
    "mnemofy_version": "0.8.0"
  },
  "segments": [
    {
      "start": 1.0,
      "end": 5.0,
      "text": "This is the first segment of the meeting",
      "confidence": 0.95
    },
    {
      "start": 5.0,
      "end": 10.0,
      "text": "We're discussing project timelines",
      "confidence": 0.92
    }
  ]
}
```

**Schema**:
- Top level: `schema_version`, `metadata`, `segments`
- Metadata: engine, model, language, duration, timestamp, etc.
- Segments: array of {start, end, text, confidence}

---

## Type Hints Summary

```python
from typing import TypedDict, Optional, List
from pathlib import Path
from dataclasses import dataclass

# Basic types
Segment = dict  # Simplest: from faster-whisper

@dataclass
class Metadata:
    engine: str
    model: str
    language: str
    duration: float
    timestamp: Optional[str] = None
    schema_version: str = "1.0"

@dataclass
class OutputPaths:
    audio: Path
    transcript_txt: Path
    transcript_srt: Path
    transcript_json: Path
    notes: Path

# For Type checking (mypy)
TranscriptList = List[dict]  # List of segments
```

---

## Design Decisions

✅ **Use dict/TypedDict over dataclass**:
- faster-whisper returns dicts
- JSON serialization natural
- Less memory overhead
- Use TypedDict for type hints

✅ **Timestamps as strings in files**:
- Precision: milliseconds (SRT), seconds (TXT), float (JSON)
- Convert at output time (not storage)

✅ **Metadata in every file**:
- Ensures self-contained outputs
- Enables format upgrade tracking
- schema_version critical for future compatibility

✅ **7 required notes sections**:
- Covers meeting documentation needs
- Deterministic basic mode (no hallucination)
- All timestamps included

✅ **Path as Path objects**:
- Type safety
- Cross-platform compatibility
- Clear semantics

---

**Status**: ✅ **PHASE 1 - DATA MODEL COMPLETE**

Next: Create API contracts (OutputManager, Formatters, StructuredNotesGenerator, CLI flags) and quickstart guide.

