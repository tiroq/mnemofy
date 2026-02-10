# API Contract: TranscriptFormatter

**Feature**: 002-enhanced-output-formats  
**Phase**: 1 (Design - API Contracts)  
**Module**: `src/mnemofy/formatters.py`

---

## Class: TranscriptFormatter

Static methods to format transcription segments into TXT, SRT, and JSON formats.

### Purpose
Convert a list of transcript segments into three industry-standard formats while maintaining consistency across all outputs.

### Interface

```python
from typing import List, Dict, Any, Optional

class TranscriptFormatter:
    """Format transcript segments into multiple output formats."""
    
    @staticmethod
    def to_txt(segments: List[Dict[str, Any]]) -> str:
        """
        Convert segments to timestamped text format.
        
        Args:
            segments: List of segment dicts from transcription
                     Each segment must have: start, end, text
        
        Returns:
            str: Text with one line per segment, format:
                 [HH:MM:SS–HH:MM:SS] text
        
        Raises:
            ValueError: If segments list is empty
            KeyError: If required fields (start, end, text) missing
            TypeError: If segment timing is not numeric
        
        Output Format:
            [00:00:01–00:00:05] This is the first segment
            [00:00:05–00:00:10] This is the second segment
            [00:00:10–00:00:15] Third segment continues here
        
        Notes:
            - Timing precision: seconds (00:00:01, not 00:00:01,000)
            - Separator: en-dash (–), not hyphen (-)
            - Durations > 1 hour supported: [01:23:45–01:25:30]
            - Empty text segments: included as-is
            - Line endings: \n (Unix style)
        
        Examples:
            segments = [
                {'start': 1.0, 'end': 5.0, 'text': 'Hello world'},
                {'start': 5.0, 'end': 10.0, 'text': 'Second segment'},
            ]
            
            txt = TranscriptFormatter.to_txt(segments)
            # Result:
            # [00:00:01–00:00:05] Hello world
            # [00:00:05–00:00:10] Second segment
        """
        ...
    
    @staticmethod
    def to_srt(segments: List[Dict[str, Any]]) -> str:
        """
        Convert segments to SubRip subtitle format.
        
        Args:
            segments: List of segment dicts from transcription
                     Each segment must have: start, end, text
        
        Returns:
            str: SRT format with sequence, timing, text blocks
        
        Raises:
            ValueError: If segments list is empty or invalid
            KeyError: If required fields missing
            TypeError: If timing not numeric or text not string
        
        Output Format:
            1
            00:00:01,000 --> 00:00:05,000
            This is the first segment
            
            2
            00:00:05,000 --> 00:00:10,000
            This is the second segment
        
        Notes:
            - Timing precision: milliseconds (HH:MM:SS,mmm)
            - Comma separator: . is NOT SubRip compliant
            - Sequence numbers: 1-indexed, sequential
            - Block separators: blank line between entries
            - Multi-line subtitles: supported (up to practical limits)
            - Special chars: no escaping needed (UTF-8 safe)
            - Durations > 24h: supported (hours can exceed 23)
            - Line endings: \n (Unix style)
        
        Examples:
            segments = [
                {'start': 1.0, 'end': 5.0, 'text': 'Hello world'},
                {'start': 5.0, 'end': 10.0, 'text': 'Second segment'},
            ]
            
            srt = TranscriptFormatter.to_srt(segments)
            # Returns properly formatted SRT string
        
        SubRip Spec Compliance:
            - ✅ Timing format: HH:MM:SS,mmm
            - ✅ Arrow separator: ` --> ` (spaces around arrow)
            - ✅ Sequential numbering: 1, 2, 3, ...
            - ✅ Blank line separators between blocks
            - ✅ No content after last subtitle
        """
        ...
    
    @staticmethod
    def to_json(
        segments: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Convert segments and metadata to JSON format.
        
        Args:
            segments: List of segment dicts from transcription
            metadata: Metadata dict with engine, model, language, duration, etc.
            
                     Required metadata fields:
                     - engine: str (e.g., "faster-whisper")
                     - model: str (e.g., "base")
                     - language: str (e.g., "en")
                     - duration: float (audio duration in seconds)
                     
                     Optional metadata fields:
                     - timestamp: str (ISO 8601)
                     - schema_version: str ("1.0" for Feature 002)
                     - transcription_engine_version: str
                     - mnemofy_version: str
                     - Any other fields preserved as-is
        
        Returns:
            str: JSON string (pretty-printed, indent=2)
        
        Raises:
            ValueError: If segments or metadata invalid
            KeyError: If required metadata fields missing
            TypeError: If data structures not JSON-serializable
        
        Output Structure:
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
                  "text": "Hello world",
                  "confidence": 0.95
                },
                {
                  "start": 5.0,
                  "end": 10.0,
                  "text": "Second segment",
                  "confidence": 0.92
                }
              ]
            }
        
        Notes:
            - schema_version: MUST be "1.0" (Feature 002)
            - Metadata required: engine, model, language, duration
            - Timestamps: float seconds (microsecond precision preserved)
            - Segments: array of objects with start, end, text, optional confidence
            - Formatting: 2-space indent (human-readable)
            - Character encoding: UTF-8
            - Line endings: \n (Unix style)
        
        Examples:
            segments = [
                {'start': 1.0, 'end': 5.0, 'text': 'Hello', 'confidence': 0.95},
            ]
            metadata = {
                'engine': 'faster-whisper',
                'model': 'base',
                'language': 'en',
                'duration': 5.0,
                'schema_version': '1.0'
            }
            
            json_str = TranscriptFormatter.to_json(segments, metadata)
            # Returns valid JSON string (can be parsed with json.loads())
        
        Metadata Field Handling:
            - Required: engine, model, language, duration
            - Optional: timestamp, schema_version, mnemofy_version, etc.
            - Forward compatibility: unknown fields preserved in output
        """
        ...
"""

### Helper Functions

```python
# Internal helpers (can be static methods or module functions)

def seconds_to_hms(seconds: float, format: str = "srt") -> str:
    """
    Convert seconds to formatted time string.
    
    Args:
        seconds: Duration in seconds (float)
        format: "txt" (HH:MM:SS), "srt" (HH:MM:SS,mmm)
    
    Returns:
        Formatted time string
    
    Examples:
        seconds_to_hms(65.123, format="txt")   # "00:01:05"
        seconds_to_hms(65.123, format="srt")   # "00:01:05,123"
    """
    ...

def validate_segment(segment: Dict[str, Any]) -> None:
    """
    Validate segment has required fields and correct types.
    
    Raises:
        KeyError: If required fields missing
        TypeError: If fields have wrong types
        ValueError: If values out of valid range
    """
    ...
```

### Validation Requirements

✅ **Input Validation**:
- [ ] segments list not empty
- [ ] Each segment has 'start', 'end', 'text' keys
- [ ] start, end are numeric (int or float)
- [ ] start < end (timing order)
- [ ] text is string (allow empty strings)
- [ ] Metadata has required fields (engine, model, language, duration)
- [ ] Metadata duration is numeric

✅ **Output Validation**:
- [ ] TXT: valid format with timestamps
- [ ] SRT: can be parsed with srt library
- [ ] JSON: valid JSON (parseable with json.loads())
- [ ] All outputs UTF-8 encodable
- [ ] No missing fields
- [ ] Proper formatting (indentation, separators)

### Error Handling

```python
# Example: Empty segments
try:
    txt = TranscriptFormatter.to_txt([])
except ValueError:
    print("Cannot format empty segment list")

# Example: Missing field
segments = [{'start': 1.0}]  # missing 'end' and 'text'
try:
    txt = TranscriptFormatter.to_txt(segments)
except KeyError:
    print("Segment missing required fields")

# Example: Invalid timing
segments = [{'start': 5.0, 'end': 1.0, 'text': 'Bad timing'}]
try:
    txt = TranscriptFormatter.to_txt(segments)
except ValueError:
    print("Start time must be less than end time")

# Example: Missing metadata
try:
    json_str = TranscriptFormatter.to_json(segments, {})  # empty metadata
except KeyError:
    print("Metadata missing required fields")
```

### Usage in Pipeline

```python
from mnemofy.formatters import TranscriptFormatter
from mnemofy.output_manager import OutputManager

# After transcription
segments = model.transcribe("audio.wav")
metadata = {
    'engine': 'faster-whisper',
    'model': 'base',
    'language': 'en',
    'duration': 95.5,
    'schema_version': '1.0'
}

# Generate all formats
txt = TranscriptFormatter.to_txt(segments)
srt = TranscriptFormatter.to_srt(segments)
json_str = TranscriptFormatter.to_json(segments, metadata)

# Save using OutputManager
manager = OutputManager("input.mp4", outdir="/out")
manager.get_transcript_paths()['txt'].write_text(txt)
manager.get_transcript_paths()['srt'].write_text(srt)
manager.get_transcript_paths()['json'].write_text(json_str)
```

### Testing Acceptance Criteria

- [ ] to_txt() produces correct timestamp format
- [ ] to_srt() produces SubRip-compatible output
- [ ] to_json() produces valid, parseable JSON
- [ ] All formats handle edge cases:
  - [ ] Empty text segments
  - [ ] Multi-line text (for SRT)
  - [ ] Special characters (emoji, accents)
  - [ ] Very long segments (>1 hour duration)
  - [ ] Very short segments (<100ms)
  - [ ] Segments with no gaps (consecutive)
  - [ ] Single segment
  - [ ] Many segments (100+)
- [ ] Error handling for invalid input
- [ ] Metadata required fields checked
- [ ] Optional confidence field handled
- [ ] Achieve 95%+ code coverage
- [ ] SRT output validates in real SRT parser library
- [ ] JSON output validates with jsonschema

### Implementation Notes

**Dependencies**:
- `json` (stdlib)
- `math` (stdlib) for time conversion
- Optional: `srt` library for testing (not required for production)

**Performance**:
- Should handle 4-hour transcripts efficiently
- No in-memory multiplexing needed
- String building: use list + join() pattern

**Code Organization**:
- Helper function: `seconds_to_hms()` (used by all formatters)
- Helper function: `validate_segment()` (used by all formatters)
- Class method: `to_txt()`
- Class method: `to_srt()`
- Class method: `to_json()`

---

**Status**: ✅ **CONTRACT DEFINED**

Implementation ready: `src/mnemofy/formatters.py`

