# Feature Specification: Enhanced Output Formats and Pipeline

**Feature ID**: 002  
**Created**: 2026-02-10  
**Status**: Draft  
**Priority**: High  
**Estimated Effort**: 40-50 hours

---

## Overview

Enhance mnemofy's transcription pipeline to produce multiple output formats with structured notes, automatic audio extraction from video, and flexible output directory control. This implements the core output management requirements from the detailed specification.

## Problem Statement

Currently, mnemofy produces basic output files but lacks:
- **Multiple transcript formats** (TXT, SRT, JSON) required for different use cases
- **Automatic audio extraction** with predictable save locations when processing video
- **Structured notes** with required sections (topics, decisions, action items with timestamps)
- **Output directory control** for organizing transcription artifacts
- **Language specification** for non-English content
- **Flexible notes generation** (deterministic basic vs LLM-enhanced)

Users need a complete transcription pipeline that handles video inputs gracefully, produces industry-standard formats, and generates actionable meeting documentation.

## User Stories

### US-001: Automatic Audio Extraction from Video
**As a** user transcribing video recordings  
**I want** mnemofy to automatically extract and save audio next to the original video  
**So that** I have a reusable normalized audio file and understand what mnemofy processed

**Acceptance Criteria**:
- When input is video (mkv, mp4, mov), extract audio automatically
- Save extracted audio as `<basename>.mnemofy.wav` next to the original file
- Normalize to 16kHz mono WAV format
- Use extracted audio for transcription pipeline
- Preserve original video file unmodified
- Log extraction process clearly

---

### US-002: Multiple Transcript Output Formats
**As a** user integrating transcripts into different workflows  
**I want** mnemofy to produce TXT, SRT, and JSON transcript formats  
**So that** I can use transcripts in subtitle editors, parsers, and text analysis tools

**Acceptance Criteria**:
- Generate `.transcript.txt` with timestamped lines `[HH:MM:SS–HH:MM:SS] text`
- Generate `.transcript.srt` in standard SubRip format
- Generate `.transcript.json` with segment-level metadata (start, end, text, confidence if available)
- All formats saved next to input by default
- All formats use same segment boundaries (consistency)
- JSON includes metadata: engine, model, language, duration

---

### US-003: Structured Notes Generation
**As a** user reviewing meeting recordings  
**I want** mnemofy to generate structured Markdown notes with required sections  
**So that** I can quickly identify topics, decisions, and action items without reading full transcripts

**Acceptance Criteria**:
- Generate `.notes.md` with required sections:
  - Metadata (date, source file, duration, engine, model)
  - Topics (with time ranges)
  - Decisions (with timestamps, or "No explicit decisions found")
  - Action Items (with owner if detected, timestamps)
  - Concrete Mentions (names, numbers, URLs) with timestamps
  - Risks/Open Questions with timestamps
  - Link to transcript files
- All extracted information MUST cite timestamps
- No hallucinated information (only transcript-derived)
- Deterministic output for `--notes basic` mode

---

### US-004: Output Directory Control
**As a** user organizing large transcription projects  
**I want** to specify a custom output directory  
**So that** I can organize transcripts by project, date, or category

**Acceptance Criteria**:
- Support `--outdir <path>` flag
- When set, write all outputs (wav, txt, srt, json, md) to specified directory
- Create directory if it doesn't exist
- Preserve input file basenames in outputs
- Default behavior unchanged (outputs next to input)
- Handle relative and absolute paths correctly

---

### US-005: Language Specification
**As a** user transcribing non-English recordings  
**I want** to specify the audio language explicitly  
**So that** transcription accuracy improves for known languages

**Acceptance Criteria**:
- Support `--lang <code>` flag (ISO 639-1 codes: en, ru, es, etc.)
- Default to `--lang auto` (engine auto-detection)
- Pass language to faster-whisper API correctly
- Document supported language codes in help text
- Log detected/specified language in notes metadata

---

### US-006: Notes Generation Modes
**As a** user with different quality and privacy needs  
**I want** to choose between basic deterministic notes and LLM-enhanced notes  
**So that** I can balance quality, speed, and data privacy

**Acceptance Criteria**:
- Support `--notes basic` (default): deterministic, local, no API calls
- Support `--notes llm`: LLM-enhanced with strict anti-hallucination prompt
- Basic mode: extract keywords, time buckets, obvious patterns
- LLM mode: require API key configuration, use non-hallucination prompt
- Both modes MUST cite timestamps for all extracted items
- Document mode differences in README

---

## Technical Approach

### Architecture Changes

#### 1. Output Manager Module (`src/mnemofy/output_manager.py`)
```python
class OutputManager:
    """Manage output file paths and formatting."""
    
    def __init__(self, input_path: Path, outdir: Optional[Path] = None):
        self.input_path = input_path
        self.outdir = outdir or input_path.parent
        self.basename = input_path.stem
    
    def get_audio_path(self) -> Path:
        """Get path for extracted audio (next to input by default)."""
        return self.input_path.parent / f"{self.basename}.mnemofy.wav"
    
    def get_transcript_paths(self) -> dict:
        """Get paths for all transcript formats."""
        return {
            "txt": self.outdir / f"{self.basename}.transcript.txt",
            "srt": self.outdir / f"{self.basename}.transcript.srt",
            "json": self.outdir / f"{self.basename}.transcript.json",
        }
    
    def get_notes_path(self) -> Path:
        """Get path for notes markdown."""
        return self.outdir / f"{self.basename}.notes.md"
```

#### 2. Transcript Formatter Module (`src/mnemofy/formatters.py`)
```python
class TranscriptFormatter:
    """Format transcription segments into multiple output formats."""
    
    @staticmethod
    def to_txt(segments: list) -> str:
        """Format as timestamped text lines."""
    
    @staticmethod
    def to_srt(segments: list) -> str:
        """Format as SubRip subtitles."""
    
    @staticmethod
    def to_json(segments: list, metadata: dict) -> str:
        """Format as JSON with metadata."""
```

#### 3. Enhanced Notes Generator (`src/mnemofy/notes.py` - major refactor)
```python
class StructuredNotesGenerator:
    """Generate structured Markdown notes from transcript."""
    
    def __init__(self, mode: str = "basic"):
        self.mode = mode  # "basic" or "llm"
    
    def generate(self, transcript: list, metadata: dict) -> str:
        """Generate structured notes with required sections."""
        if self.mode == "basic":
            return self._generate_basic(transcript, metadata)
        else:
            return self._generate_llm(transcript, metadata)
    
    def _extract_topics(self, transcript: list) -> list:
        """Extract topics with time ranges."""
    
    def _extract_decisions(self, transcript: list) -> list:
        """Extract decisions with timestamps."""
    
    def _extract_action_items(self, transcript: list) -> list:
        """Extract action items with owners and timestamps."""
    
    def _extract_mentions(self, transcript: list) -> list:
        """Extract concrete mentions (names, URLs, numbers) with timestamps."""
```

#### 4. CLI Integration Updates (`src/mnemofy/cli.py`)
- Add `--outdir`, `--lang`, `--notes`, `--audio-track` flags
- Integrate OutputManager for path management
- Call formatters for multiple outputs
- Orchestrate enhanced notes generation

### Data Flow

```
Input (video/audio)
    ↓
[Video Detection] → Extract Audio → Save <basename>.mnemofy.wav (next to input)
    ↓
[Audio Normalization] → 16kHz mono WAV
    ↓
[Transcription] → segment list with timestamps
    ↓
[Formatters] → TXT + SRT + JSON (to outdir)
    ↓
[Notes Generator] → Structured MD (to outdir)
    ↓
Output: 4-5 files (wav next to input, others in outdir)
```

### File Naming Convention

Given input `/path/to/meeting.mkv` with `--outdir /transcripts`:

- Audio: `/path/to/meeting.mnemofy.wav` (next to input, always)
- TXT: `/transcripts/meeting.transcript.txt`
- SRT: `/transcripts/meeting.transcript.srt`
- JSON: `/transcripts/meeting.transcript.json`
- Notes: `/transcripts/meeting.notes.md`

---

## Success Criteria

### Functional Requirements
1. Video inputs automatically extract audio to `<name>.mnemofy.wav` next to original
2. Three transcript formats (TXT, SRT, JSON) generated for every transcription
3. Notes contain all 7 required sections with timestamps
4. `--outdir` flag controls transcript/notes location (audio stays next to input)
5. `--lang` flag passes language to transcription engine
6. `--notes basic` produces deterministic, local notes
7. `--notes llm` integrates LLM with anti-hallucination prompt

### Non-Functional Requirements
1. **Predictability**: Users can always find extracted audio next to original video
2. **Consistency**: All output formats use identical segment boundaries
3. **No Hallucination**: Notes only contain transcript-derived information with timestamps
4. **Backward Compatibility**: Existing CLI usage still works (new flags optional)
5. **Performance**: Format conversion adds <5% overhead to total pipeline time

### Measurable Outcomes
- 100% of video inputs produce `.mnemofy.wav` next to original
- 100% of transcriptions produce 3 formats + notes (4-5 files total)
- 100% of notes sections cite timestamps
- 0 hallucinated information in `--notes basic` mode
- --outdir creates directory if missing (100% success rate)

---

## Dependencies and Constraints

### Technical Dependencies
- **ffmpeg**: Required for audio extraction (already dependency)
- **faster-whisper**: Core transcription engine (existing)
- **LLM API** (optional): For `--notes llm` mode (OpenAI, Anthropic, local)
- **Python ≥3.9**: Existing constraint

### External Constraints
- SubRip format spec must be followed exactly for compatibility
- JSON format should be machine-parseable (valid JSON)
- Audio extraction must not modify original files

### Assumptions
- Input files are valid media (handled by ffmpeg)
- Disk space sufficient for extracted audio + outputs
- LLM mode users have API keys configured

---

## Scope

### In Scope
- Automatic audio extraction with save-next-to-input behavior
- TXT, SRT, JSON transcript formatters
- Structured notes with 7 required sections
- `--outdir`, `--lang`, `--notes` CLI flags
- Basic (deterministic) notes generation
- LLM notes generation integration (stub for v0.8.0)

### Out of Scope (Future)
- `--audio-track` selection (deferred to v0.9.0)
- Speaker diarization in notes (v0.10.0)
- Word-level timestamps (WhisperX integration, v0.11.0)
- Live/streaming transcription
- Custom notes templates

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Audio extraction fails for exotic codecs | Medium | High | Test with diverse video formats; provide clear error messages |
| SRT format compatibility issues | Low | Medium | Validate against srt spec; test with common subtitle editors |
| LLM hallucination in notes | High | Critical | Strict prompt engineering; timestamp requirement; user education |
| Large files fill disk during extraction | Low | Medium | Check available space before extraction; document requirements |
| Backward compatibility breaks | Low | High | Maintain existing defaults; extensive regression testing |

---

## Testing Strategy

### Unit Tests
- Output Manager path generation (15 tests)
- TXT formatter (10 tests)
- SRT formatter (15 tests - strict format compliance)
- JSON formatter (10 tests - valid JSON, metadata)
- Notes extractor functions (25 tests - topics, decisions, actions, mentions)

### Integration Tests
- Video → audio extraction → transcription → outputs (5 tests)
- --outdir flag with various paths (5 tests)
- --lang flag with different languages (3 tests)
- --notes basic vs llm modes (5 tests)
- Full pipeline with all formats (3 tests)

### Manual Testing
- Test with real meeting recordings (mp4, mkv, mov)
- Verify SRT files in VLC, subtitle editors
- Validate JSON parsability
- Check notes quality and timestamp accuracy

**Target**: 90%+ code coverage, all formats validated

---

## Implementation Plan

See [tasks.md](./tasks.md) for detailed task breakdown.

**High-level phases**:
1. **Phase 1**: Output Manager + Audio Extraction (6-8 hours)
2. **Phase 2**: Transcript Formatters (TXT, SRT, JSON) (8-10 hours)
3. **Phase 3**: Enhanced Notes Generator (12-15 hours)
4. **Phase 4**: CLI Integration (4-6 hours)
5. **Phase 5**: Testing & Validation (6-8 hours)
6. **Phase 6**: Documentation (3-4 hours)
7. **Phase 7**: Release (2-3 hours)

**Total Estimate**: 40-50 hours

---

## Documentation Requirements

### README Updates
- Document new output file structure
- Explain --outdir, --lang, --notes flags
- Show example outputs for each format
- Describe notes sections and timestamp citations

### CHANGELOG
- New features: multi-format output, structured notes, outdir control
- Breaking changes: None (backward compatible)
- New dependencies: None (uses existing)

### Code Documentation
- Docstrings for all new classes/functions
- Type hints on all signatures
- Comments for format-specific logic (SRT timing, JSON structure)

---

## Acceptance Checklist

- [ ] Video inputs extract audio to `.mnemofy.wav` next to original
- [ ] TXT format: timestamped lines `[HH:MM:SS–HH:MM:SS] text`
- [ ] SRT format: valid SubRip, tested in subtitle editor
- [ ] JSON format: valid JSON with segment metadata
- [ ] Notes MD: 7 required sections with timestamps
- [ ] --outdir flag creates directory and writes outputs correctly
- [ ] --lang flag passes to transcription engine
- [ ] --notes basic produces deterministic output
- [ ] 90%+ test coverage
- [ ] Documentation updated (README, CHANGELOG)
- [ ] No regression in existing functionality

---

## References

- [Detailed Specification v0.1](../../../mnemofy_detailed_spec.md)
- [SubRip Format Spec](https://en.wikipedia.org/wiki/SubRip)
- [faster-whisper Documentation](https://github.com/guillaumekln/faster-whisper)
- [Feature 001: Adaptive ASR Model Selection](../001-adaptive-asr-model-selection/spec.md)
