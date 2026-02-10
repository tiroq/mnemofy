# Task Breakdown: Enhanced Output Formats and Pipeline

**Feature ID**: 002 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This document breaks down the implementation into 54 concrete tasks organized by phase. Each task includes clear acceptance criteria, dependencies, and time estimates.

---

## Phase 1: Foundation - Output Manager (6-8 hours)

### T-001: Create OutputManager Module
**Phase**: Foundation  
**Priority**: P0 (Prerequisite)  
**Estimate**: 1.5 hours

**Description**: Create `src/mnemofy/output_manager.py` module with `OutputManager` class.

**Acceptance Criteria**:
- [X] Create `src/mnemofy/output_manager.py`
- [X] Define `OutputManager` class with `__init__(input_path, outdir=None)`
- [X] Add type hints (Path types)
- [X] Add module docstring
- [X] Add basic class docstring

**Dependencies**: None

**Files**:
- `src/mnemofy/output_manager.py` (new)

---

### T-002: Implement Path Generation Methods
**Phase**: Foundation  
**Priority**: P0  
**Estimate**: 2 hours

**Description**: Implement all path generation methods in OutputManager.

**Acceptance Criteria**:
- [X] Implement `get_audio_path()` → returns Path in outdir (`<basename>.mnemofy.wav`)
- [X] Implement `get_transcript_paths()` → returns dict with txt/srt/json keys (in outdir)
- [X] Implement `get_notes_path()` → returns Path for notes.md (in outdir)
- [X] Handle both relative and absolute outdir paths correctly
- [X] Preserve input basename in all outputs
- [X] Add method docstrings with examples

**Dependencies**: T-001

**Files**:
- `src/mnemofy/output_manager.py` (modify)

---

### T-003: Add --outdir CLI Flag
**Phase**: Foundation  
**Priority**: P0  
**Estimate**: 1 hour

**Description**: Add `--outdir` flag to CLI transcribe command.

**Acceptance Criteria**:
- [X] Add `--outdir` option to transcribe command in `cli.py`
- [X] Type: Optional[Path]
- [X] Help text: "Output directory for transcript and notes files (default: same as input)"
- [X] Validate directory is writable (or can be created)
- [X] Pass outdir to OutputManager initialization

**Dependencies**: T-001, T-002

**Files**:
- `src/mnemofy/cli.py` (modify)

---

### T-004: Write OutputManager Unit Tests
**Phase**: Foundation  
**Priority**: P0  
**Estimate**: 2 hours

**Description**: Create comprehensive tests for OutputManager path logic.

**Acceptance Criteria**:
- [X] Create `tests/test_output_manager.py`
- [X] Test audio path (in outdir)
- [X] Test transcript paths (in outdir)
- [X] Test notes path (in outdir)
- [X] Test with outdir=None (default to input parent)
- [X] Test with relative outdir path
- [X] Test with absolute outdir path
- [X] Test basename preservation
- [X] Test with various input extensions (mp4, mkv, wav, aac)
- [X] Achieve 95%+ coverage

**Dependencies**: T-002

**Files**:
- `tests/test_output_manager.py` (new)

---

### T-005: Update Audio Extractor to Use OutputManager
**Phase**: Foundation  
**Priority**: P0  
**Estimate**: 1.5 hours

**Description**: Modify AudioExtractor to accept output path from OutputManager.

**Acceptance Criteria**:
- [X] Update `AudioExtractor` to accept `output_path` parameter
- [X] Use `output_manager.get_audio_path()` in CLI
- [X] Ensure audio saved to outdir location from OutputManager
- [X] Log extracted audio location clearly
- [X] Update existing audio extraction tests
- [X] Test that video → wav to outdir works

**Dependencies**: T-002, T-003

**Files**:
- `src/mnemofy/audio.py` (modify)
- `src/mnemofy/cli.py` (modify)
- `tests/test_audio.py` (modify)

---

## Phase 2: Transcript Formatters (8-10 hours)

### T-006: Create Formatters Module Structure
**Phase**: Formatters  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Create `src/mnemofy/formatters.py` with TranscriptFormatter class.

**Acceptance Criteria**:
- [X] Create `src/mnemofy/formatters.py`
- [X] Define `TranscriptFormatter` class
- [X] Add module docstring explaining format purposes
- [X] Define segment type structure (dict with start, end, text)
- [X] Add class-level documentation

**Dependencies**: None

**Files**:
- `src/mnemofy/formatters.py` (new)

---

### T-007: Implement TXT Formatter
**Phase**: Formatters  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Implement TXT format: timestamped lines `[HH:MM:SS–HH:MM:SS] text`.

**Acceptance Criteria**:
- [X] Implement `to_txt(segments: list) -> str` static method
- [X] Format: `[HH:MM:SS–HH:MM:SS] text\\n` per segment
- [X] Handle timestamps correctly (seconds to HH:MM:SS)
- [X] Use en-dash (–) between timestamps
- [X] Handle edge cases: empty segments, 0 duration, >24 hours
- [X] Add comprehensive docstring with example
- [X] Write 10+ unit tests

**Dependencies**: T-006

**Files**:
- `src/mnemofy/formatters.py` (modify)
- `tests/test_formatters.py` (new)

---

### T-008: Implement SRT Formatter
**Phase**: Formatters  
**Priority**: P1  
**Estimate**: 3 hours

**Description**: Implement SRT (SubRip) format following official spec.

**Acceptance Criteria**:
- [X] Implement `to_srt(segments: list) -> str` static method
- [X] Format per spec: sequence number, timing line, text, blank line
- [X] Timing format: `HH:MM:SS,mmm --> HH:MM:SS,mmm` (millisecond precision)
- [X] Use comma for milliseconds (not period)
- [X] Sequential numbering starting at 1
- [X] Handle multi-line text in segments
- [X] Handle edge cases: overlapping segments, microsecond precision
- [X] Write 15+ unit tests
- [X] Validate output with srt parser library

**Dependencies**: T-006

**Files**:
- `src/mnemofy/formatters.py` (modify)
- `tests/test_formatters.py` (modify)

**Research Required**: Review SubRip format spec thoroughly

---

### T-009: Implement JSON Formatter
**Phase**: Formatters  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Implement JSON format with segment metadata.

**Acceptance Criteria**:
- [X] Implement `to_json(segments: list, metadata: dict) -> str` static method
- [X] JSON structure: `{"metadata": {...}, "segments": [...]}`
- [X] Metadata fields: engine, model, language, duration, timestamp, schema_version
- [X] Include `schema_version: '1.0'` for future compatibility
- [X] Segment fields: start, end, text, confidence (if available)
- [X] Valid JSON (parseable with json.loads)
- [X] Pretty-printed with indent=2
- [X] Handle special characters in text (escaping)
- [X] Write 10+ unit tests
- [X] Test JSON parsing roundtrip

**Dependencies**: T-006

**Files**:
- `src/mnemofy/formatters.py` (modify)
- `tests/test_formatters.py` (modify)

---

### T-010: Add Format Validation Utilities
**Phase**: Formatters  
**Priority**: P2  
**Estimate**: 1 hour

**Description**: Add utility functions to validate generated formats.

**Acceptance Criteria**:
- [X] Implement `validate_srt(content: str) -> bool`
- [X] Implement `validate_json(content: str) -> bool`
- [X] Check SRT sequence numbers, timing format
- [X] Check JSON parseability and structure
- [X] Return helpful error messages
- [X] Write 5+ validation tests

**Dependencies**: T-007, T-008, T-009

**Files**:
- `src/mnemofy/formatters.py` (modify)
- `tests/test_formatters.py` (modify)

---

### T-011: Write Comprehensive Formatter Tests
**Phase**: Formatters  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Ensure 90%+ coverage for all formatters.

**Acceptance Criteria**:
- [X] 30+ total tests across all formatters
- [X] Test TXT: basic, multi-segment, edge times, unicode text
- [X] Test SRT: basic, multi-line, timing precision, sequence numbering
- [X] Test JSON: basic, metadata fields, special characters, roundtrip
- [X] Test validation utilities
- [X] Run coverage report: 90%+ for formatters.py
- [X] All tests pass

**Dependencies**: T-007, T-008, T-009, T-010

**Files**:
- `tests/test_formatters.py` (modify)

---

### T-012: Validate SRT in Subtitle Editors
**Phase**: Formatters  
**Priority**: P2  
**Estimate**: 1 hour

**Description**: Manual validation of SRT format in real subtitle editors.

**Acceptance Criteria**:
- [X] Generate sample SRT with test data
- [X] Open in VLC Media Player → verify rendering
- [X] Open in Subtitle Edit → verify timing
- [X] Test with non-ASCII characters
- [X] Document any compatibility issues
- [X] Fix any issues found

**Dependencies**: T-008

---

## Phase 3: Enhanced Notes Generation (12-15 hours)

### T-013: Refactor NoteGenerator to StructuredNotesGenerator
**Phase**: Notes  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Restructure notes.py for new architecture.

**Acceptance Criteria**:
- [X] Rename `NoteGenerator` → `StructuredNotesGenerator`
- [X] Add `mode` parameter ("basic" or "llm")
- [X] Update `__init__` to accept mode
- [X] Refactor `generate()` method to route to mode-specific methods
- [X] Add `_generate_basic()` and `_generate_llm()` stubs
- [X] Update existing tests to use new class name
- [X] Maintain backward compatibility temporarily

**Dependencies**: None

**Files**:
- `src/mnemofy/notes.py` (major refactor)
- `tests/test_notes.py` (update)

---

### T-014: Implement Metadata Section Generator
**Phase**: Notes  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Generate metadata section with source file, duration, engine, model info.

**Acceptance Criteria**:
- [X] Implement `_generate_metadata(metadata: dict) -> str`
- [X] Include: date, source file, duration, engine, model, language
- [X] Format as Markdown with proper heading
- [X] Handle missing metadata fields gracefully
- [X] Write 5+ tests

**Dependencies**: T-013

**Files**:
- `src/mnemofy/notes.py` (modify)
- `tests/test_notes_enhanced.py` (new)

---

### T-015: Implement Topic Extraction
**Phase**: Notes  
**Priority**: P1  
**Estimate**: 2.5 hours

**Description**: Extract topics with time ranges from transcript.

**Acceptance Criteria**:
- [X] Implement `_extract_topics(segments: list) -> list[dict]`
- [X] Check minimum transcript length (30 seconds) before extraction
- [X] Detect topic changes (basic: time buckets + keyword shifts)
- [X] Return topics with start/end timestamps
- [X] Format: `- **[MM:SS–MM:SS]** Topic description`
- [X] Handle short transcripts (< 5 min)
- [X] Write 8+ tests for various transcript lengths

**Dependencies**: T-013

**Files**:
- `src/mnemofy/notes.py` (modify)
- `tests/test_notes_enhanced.py` (modify)

---

### T-016: Implement Decision Extraction
**Phase**: Notes  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Extract explicit decisions with timestamps.

**Acceptance Criteria**:
- [X] Implement `_extract_decisions(segments: list) -> list[dict]`
- [X] Detect decision keywords: "decided", "agreed", "will", "going to"
- [X] Return decisions with timestamps
- [X] Format: `- **[MM:SS]** Decision statement`
- [X] If no decisions found: "No explicit decisions found"
- [X] Write 6+ tests (with/without decisions)

**Dependencies**: T-013

**Files**:
- `src/mnemofy/notes.py` (modify)
- `tests/test_notes_enhanced.py` (modify)

---

### T-017: Implement Action Item Extraction
**Phase**: Notes  
**Priority**: P1  
**Estimate**: 2.5 hours

**Description**: Extract action items with owners and timestamps.

**Acceptance Criteria**:
- [X] Implement `_extract_action_items(segments: list) -> list[dict]`
- [X] Detect action keywords: "will", "need to", "should", "TODO"
- [X] Detect owners: @mentions, names followed by action verbs
- [X] Return: action text, owner (or "unknown"), timestamp
- [X] Format: `- **[MM:SS]** Action description (owner: @name or unknown)`
- [X] Write 8+ tests (various action patterns)

**Dependencies**: T-013

**Files**:
- `src/mnemofy/notes.py` (modify)
- `tests/test_notes_enhanced.py` (modify)

---

### T-018: Implement Concrete Mentions Extraction
**Phase**: Notes  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Extract names, URLs, numbers, projects with timestamps.

**Acceptance Criteria**:
- [X] Implement `_extract_mentions(segments: list) -> dict[str, list]`
- [X] Detect: names (capitalized words), URLs (http/https), emails, numbers (dates, amounts)
- [X] Return categorized: {"names": [...], "urls": [...], "dates": [...], "numbers": [...]}
- [X] Each mention includes timestamp
- [X] Format: `- Name (@timestamp)`, `- URL (@timestamp)`
- [X] Write 10+ tests (various mention types)

**Dependencies**: T-013

**Files**:
- `src/mnemofy/notes.py` (modify)
- `tests/test_notes_enhanced.py` (modify)

---

### T-019: Implement Risks/Open Questions Extraction
**Phase**: Notes  
**Priority**: P2  
**Estimate**: 1.5 hours

**Description**: Extract uncertainty markers and questions with timestamps.

**Acceptance Criteria**:
- [X] Implement `_extract_risks(segments: list) -> list[dict]`
- [X] Detect: question marks, "unclear", "not sure", "risk", "concern"
- [X] Return risks/questions with timestamps
- [X] Format: `- **[MM:SS]** Risk or question statement`
- [X] If none found: "No risks or open questions identified"
- [X] Write 5+ tests

**Dependencies**: T-013

**Files**:
- `src/mnemofy/notes.py` (modify)
- `tests/test_notes_enhanced.py` (modify)

---

### T-020: Add Transcript File Links Section
**Phase**: Notes  
**Priority**: P1  
**Estimate**: 0.5 hours

**Description**: Add links to transcript files at end of notes.

**Acceptance Criteria**:
- [X] Implement `_generate_transcript_links(paths: dict) -> str`
- [X] List all transcript files (TXT, SRT, JSON) with relative paths
- [X] Format as Markdown links
- [X] Section heading: "## Transcript Files"
- [X] Write 3+ tests

**Dependencies**: T-013

**Files**:
- `src/mnemofy/notes.py` (modify)
- `tests/test_notes_enhanced.py` (modify)

---

### T-021: Implement --notes basic Mode
**Phase**: Notes  
**Priority**: P1  
**Estimate**: 1.5 hours

**Description**: Complete deterministic basic notes generation.

**Acceptance Criteria**:
- [X] Implement `_generate_basic(segments, metadata)` fully
- [X] Call all extraction methods
- [X] Assemble all 7 sections in order
- [X] Ensure deterministic output (same input → same output)
- [X] No randomness, no external API calls
- [X] Write 5+ integration tests

**Dependencies**: T-014, T-015, T-016, T-017, T-018, T-019, T-020

**Files**:
- `src/mnemofy/notes.py` (modify)
- `tests/test_notes_enhanced.py` (modify)

---

### T-022: Stub --notes llm Mode
**Phase**: Notes  
**Priority**: P3  
**Estimate**: 1 hour

**Description**: Create stub for future LLM-enhanced notes.

**Acceptance Criteria**:
- [X] Implement `_generate_llm(segments, metadata)` stub
- [X] Raise NotImplementedError with message: "LLM mode coming in v0.9.0"
- [X] Document LLM requirements in docstring (API key, prompt template)
- [X] Add placeholder for anti-hallucination prompt
- [X] Write test that stub raises correct error

**Dependencies**: T-013

**Files**:
- `src/mnemofy/notes.py` (modify)
- `tests/test_notes_enhanced.py` (modify)

---

### T-023: Write Comprehensive Notes Tests
**Phase**: Notes  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Ensure 90%+ coverage for enhanced notes module.

**Acceptance Criteria**:
- [X] 25+ total tests for notes.py
- [X] Test each extraction method independently
- [X] Test basic mode integration
- [X] Test edge cases: empty transcript, very long transcript
- [X] Test timestamp citation in all sections
- [X] Test determinism (same input → same output)
- [X] Achieve 90%+ coverage
- [X] All tests pass

**Dependencies**: T-014-T-022

**Files**:
- `tests/test_notes_enhanced.py` (modify)

---

## Phase 4: CLI Integration (4-6 hours)

### T-024: Add --lang CLI Flag
**Phase**: CLI  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Add language specification flag.

**Acceptance Criteria**:
- [X] Add `--lang` option to transcribe command
- [X] Type: str, default: "auto"
- [X] Help text: "Transcription language (ISO 639-1 code: en, ru, es, etc.; default: auto)"
- [X] Pass language to Transcriber initialization
- [X] Include language in output metadata
- [X] Write 3+ tests

**Dependencies**: None

**Files**:
- `src/mnemofy/cli.py` (modify)
- `tests/test_cli_outputs.py` (new)

---

### T-025: Add --notes CLI Flag
**Phase**: CLI  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Add notes generation mode flag.

**Acceptance Criteria**:
- [X] Add `--notes` option to transcribe command
- [X] Type: str, choices: ["basic", "llm"], default: "basic"
- [X] Help text: "Notes generation mode (basic: deterministic, llm: AI-enhanced)"
- [X] Pass mode to StructuredNotesGenerator
- [X] Validate choice value
- [X] Write 3+ tests

**Dependencies**: T-013

**Files**:
- `src/mnemofy/cli.py` (modify)
- `tests/test_cli_outputs.py` (modify)

---

### T-026: Integrate OutputManager in CLI
**Phase**: CLI  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Use OutputManager for all file path management.

**Acceptance Criteria**:
- [X] Create OutputManager instance in transcribe command
- [X] Use get_audio_path() for audio extraction
- [X] Use get_transcript_paths() for transcript outputs
- [X] Use get_notes_path() for notes output
- [X] Create outdir if it doesn't exist
- [X] Log all output file paths
- [X] Write 5+ integration tests

**Dependencies**: T-002, T-003

**Files**:
- `src/mnemofy/cli.py` (modify)
- `tests/test_cli_outputs.py` (modify)

---

### T-027: Call All Formatters After Transcription
**Phase**: CLI  
**Priority**: P1  
**Estimate**: 1.5 hours

**Description**: Generate all three transcript formats.

**Acceptance Criteria**:
- [X] After transcription, call TranscriptFormatter.to_txt()
- [X] Call TranscriptFormatter.to_srt()
- [X] Call TranscriptFormatter.to_json()
- [X] Write each format to appropriate path
- [X] Collect metadata (model, language, duration, timestamp)
- [X] Handle write errors gracefully (best-effort: skip failed, complete others)
- [X] Log warnings for any failed formats
- [X] Write 5+ tests

**Dependencies**: T-007, T-008, T-009, T-026

**Files**:
- `src/mnemofy/cli.py` (modify)
- `tests/test_cli_outputs.py` (modify)

---

### T-028: Integrate Enhanced Notes Generator
**Phase**: CLI  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Generate structured notes with selected mode.

**Acceptance Criteria**:
- [X] Create StructuredNotesGenerator with mode from --notes flag
- [X] Pass transcript segments and metadata
- [X] Write notes to path from OutputManager
- [X] Handle generation errors gracefully
- [X] Log notes file location
- [X] Write 3+ tests

**Dependencies**: T-021, T-025, T-026

**Files**:
- `src/mnemofy/cli.py` (modify)
- `tests/test_cli_outputs.py` (modify)

---

### T-029: Add Format Summary Logging
**Phase**: CLI  
**Priority**: P2  
**Estimate**: 0.5 hours

**Description**: Log summary of all generated files.

**Acceptance Criteria**:
- [X] After pipeline completes, log summary:
  - Audio file path (if extracted)
  - Transcript files (TXT, SRT, JSON)
  - Notes file
- [X] Use rich formatting for readability
- [X] Include file sizes
- [X] Write 2+ tests

**Dependencies**: T-027, T-028

**Files**:
- `src/mnemofy/cli.py` (modify)

---

### T-030: Write CLI Integration Tests
**Phase**: CLI  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Test complete CLI with all new flags.

**Acceptance Criteria**:
- [X] Test --outdir with various paths
- [X] Test --lang with different languages
- [X] Test --notes basic vs llm (stub)
- [X] Test complete pipeline: video → audio + 4 outputs
- [X] Test complete pipeline: audio → 4 outputs (no extraction)
- [X] Test all output files exist and are valid
- [X] Test backward compatibility (no new flags = works)
- [X] 10+ integration tests total

**Dependencies**: T-024-T-029

**Files**:
- `tests/test_cli_outputs.py` (modify)

---

## Phase 5: Testing & Validation (6-8 hours)

### T-031: Achieve Coverage for OutputManager
**Phase**: Testing  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Ensure 90%+ coverage for output_manager.py.

**Acceptance Criteria**:
- [X] Run coverage report for output_manager.py
- [X] Add tests for uncovered edge cases
- [X] Test error handling (invalid paths, permissions)
- [X] Achieve 90%+ coverage
- [X] All tests pass

**Dependencies**: T-004

**Files**:
- `tests/test_output_manager.py` (modify)

---

### T-032: Achieve Coverage for Formatters
**Phase**: Testing  
**Priority**: P1  
**Estimate**: 1.5 hours

**Description**: Ensure 90%+ coverage for formatters.py.

**Acceptance Criteria**:
- [X] Run coverage report for formatters.py
- [X] Add tests for edge cases (empty segments, very long text)
- [X] Test SRT with extreme timestamps (>24 hours)
- [X] Test JSON with special characters
- [X] Achieve 90%+ coverage
- [X] All tests pass

**Dependencies**: T-011

**Files**:
- `tests/test_formatters.py` (modify)

---

### T-033: Achieve Coverage for Enhanced Notes
**Phase**: Testing  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Ensure 90%+ coverage for notes.py.

**Acceptance Criteria**:
- [X] Run coverage report for notes.py
- [X] Add tests for complex extraction scenarios
- [X] Test with real-world transcript samples
- [X] Test determinism rigorously
- [X] Achieve 90%+ coverage
- [X] All tests pass

**Dependencies**: T-023

**Files**:
- `tests/test_notes_enhanced.py` (modify)

---

### T-034: Write End-to-End Integration Tests
**Phase**: Testing  
**Priority**: P1  
**Estimate**: 2 hours

**Description**: Test complete pipeline with real media files.

**Acceptance Criteria**:
- [X] Create test fixtures: sample video (mp4), audio (wav)
- [X] Test: video input → 5 outputs (wav + txt + srt + json + md)
- [X] Test: audio input → 4 outputs (txt + srt + json + md)
- [X] Test: --outdir creates directory and writes files correctly
- [X] Test: all formats are valid (parse SRT, JSON)
- [X] Test: notes contain all 7 sections
- [X] 5+ end-to-end tests

**Dependencies**: T-030

**Files**:
- `tests/test_integration_pipeline.py` (new)

---

### T-035: Test with Real Video Files
**Phase**: Testing  
**Priority**: P2  
**Estimate**: 1 hour

**Description**: Manual testing with diverse video formats.

**Acceptance Criteria**:
- [X] Test with MP4 (H.264 + AAC)
- [X] Test with MKV (various codecs)
- [X] Test with MOV (QuickTime)
- [X] Verify audio extraction works for all
- [X] Verify all outputs generated correctly
- [X] Document any codec issues

**Dependencies**: T-034

---

### T-036: Validate SRT Files in Subtitle Editors
**Phase**: Testing  
**Priority**: P2  
**Estimate**: 1 hour

**Description**: Manual validation in real subtitle tools.

**Acceptance Criteria**:
- [X] Generate SRT from test transcript
- [X] Open in VLC Media Player → verify display
- [X] Open in Subtitle Edit → verify timing
- [X] Test with special characters (emoji, accented letters)
- [X] Document any compatibility issues
- [X] Fix issues if found

**Dependencies**: T-012, T-034

---

### T-037: Validate JSON Format
**Phase**: Testing  
**Priority**: P2  
**Estimate**: 0.5 hours

**Description**: Programmatic JSON validation.

**Acceptance Criteria**:
- [X] Parse generated JSON with json.loads()
- [X] Validate metadata fields present
- [X] Validate segments structure
- [X] Test with jq for querying
- [X] Verify special character escaping

**Dependencies**: T-034

---

### T-038: Test --outdir with Various Paths
**Phase**: Testing  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Test output directory handling.

**Acceptance Criteria**:
- [X] Test with absolute path
- [X] Test with relative path
- [X] Test with non-existent directory (should create)
- [X] Test with existing directory (should use)
- [X] Test with read-only directory (should error gracefully)
- [X] Test with ~ home directory expansion
- [X] Write 6+ tests

**Dependencies**: T-030

**Files**:
- `tests/test_cli_outputs.py` (modify)

---

### T-039: Test --lang with Non-English Audio
**Phase**: Testing  
**Priority**: P2  
**Estimate**: 1 hour

**Description**: Test language specification.

**Acceptance Criteria**:
- [X] Test with --lang ru (Russian sample)
- [X] Test with --lang es (Spanish sample)
- [X] Test with --lang auto (auto-detection)
- [X] Verify language passed to faster-whisper correctly
- [X] Verify language in output metadata
- [X] Write 3+ tests

**Dependencies**: T-024

**Files**:
- `tests/test_cli_outputs.py` (modify)

---

### T-040: Edge Case Testing
**Phase**: Testing  
**Priority**: P2  
**Estimate**: 1.5 hours

**Description**: Test unusual scenarios.

**Acceptance Criteria**:
- [X] Test with very short audio (< 5 seconds)
- [X] Test with very long audio (> 2 hours)
- [X] Test with silent audio (no speech)
- [X] Test with corrupted video file (should error gracefully)
- [X] Test with insufficient disk space (mock)
- [X] Test with special characters in filename
- [X] Document edge case behavior

**Dependencies**: T-034

**Files**:
- `tests/test_edge_cases.py` (new)

---

## Phase 6: Documentation (3-4 hours)

### T-041: Add "Output Files" Section to README
**Phase**: Documentation  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Document all generated output files.

**Acceptance Criteria**:
- [X] Add "Output Files" section to README
- [X] List all 4-5 output files (wav, txt, srt, json, md)
- [X] Explain purpose of each format
- [X] Show example naming: `meeting.transcript.txt`, etc.
- [X] Document .mnemofy.wav save location (next to input)
- [X] Show example file tree structure

**Dependencies**: None

**Files**:
- `README.md` (modify)

---

### T-042: Document New CLI Flags
**Phase**: Documentation  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Add documentation for --outdir, --lang, --notes flags.

**Acceptance Criteria**:
- [X] Document --outdir with examples
- [X] Document --lang with supported language codes
- [X] Document --notes basic vs llm (stub)
- [X] Provide 3-5 usage examples combining flags
- [X] Update CLI help text examples

**Dependencies**: None

**Files**:
- `README.md` (modify)

---

### T-043: Provide Format Examples
**Phase**: Documentation  
**Priority**: P2  
**Estimate**: 1 hour

**Description**: Show example outputs for each format.

**Acceptance Criteria**:
- [X] Create examples/ directory
- [X] Add sample transcript.txt (5-10 lines)
- [X] Add sample transcript.srt (SRT format)
- [X] Add sample transcript.json (JSON structure)
- [X] Add sample notes.md (all 7 sections)
- [X] Reference examples in README

**Dependencies**: T-041

**Files**:
- `examples/sample.transcript.txt` (new)
- `examples/sample.transcript.srt` (new)
- `examples/sample.transcript.json` (new)
- `examples/sample.notes.md` (new)
- `README.md` (modify)

---

### T-044: Add Troubleshooting for Audio Extraction
**Phase**: Documentation  
**Priority**: P2  
**Estimate**: 0.5 hours

**Description**: Document common audio extraction issues.

**Acceptance Criteria**:
- [X] Add troubleshooting section for audio extraction
- [X] Document: ffmpeg not found
- [X] Document: unsupported codec
- [X] Document: corrupted video file
- [X] Provide solutions for each issue
- [X] Link to ffmpeg installation guide

**Dependencies**: None

**Files**:
- `README.md` (modify)

---

### T-045: Update CHANGELOG for v0.8.0
**Phase**: Documentation  
**Priority**: P1  
**Estimate**: 0.5 hours

**Description**: Document all changes in CHANGELOG.

**Acceptance Criteria**:
- [X] Add v0.8.0 section to CHANGELOG.md
- [X] List new features: multi-format output, structured notes, --outdir
- [X] Document new CLI flags
- [X] Note: no breaking changes
- [X] Include upgrade instructions

**Dependencies**: None

**Files**:
- `CHANGELOG.md` (modify)

---

### T-046: Add Docstrings to All New Code
**Phase**: Documentation  
**Priority**: P1  
**Estimate**: 1 hour

**Description**: Ensure comprehensive inline documentation.

**Acceptance Criteria**:
- [X] All public functions have docstrings
- [X] All classes have docstrings
- [X] Type hints on all function signatures
- [X] Complex algorithms have inline comments
- [X] Examples in docstrings for key functions

**Dependencies**: All implementation tasks

**Files**:
- All source files (review and enhance)

---

### T-047: Create Examples Directory
**Phase**: Documentation  
**Priority**: P3  
**Estimate**: 0.5 hours

**Description**: Set up examples/ with sample outputs.

**Acceptance Criteria**:
- [X] Create examples/ directory
- [X] Add README explaining samples
- [X] Include sample video/audio (small, public domain)
- [X] Include corresponding outputs
- [X] Reference in main README

**Dependencies**: T-043

**Files**:
- `examples/README.md` (new)
- `examples/` (various sample files)

---

## Phase 7: Release (2-3 hours)

### T-048: Bump Version to 0.8.0
**Phase**: Release  
**Priority**: P1  
**Estimate**: 0.5 hours

**Description**: Update version in pyproject.toml.

**Acceptance Criteria**:
- [X] Update version: 0.7.0 → 0.8.0
- [X] Verify no new dependencies needed
- [X] Commit version bump with message: "Bump version to 0.8.0"

**Dependencies**: All previous tasks

**Files**:
- `pyproject.toml` (modify)

---

### T-049: Final Integration Test Run
**Phase**: Release  
**Priority**: P1  
**Estimate**: 0.5 hours

**Description**: Run complete test suite one final time.

**Acceptance Criteria**:
- [X] Run `pytest tests/ -v --cov=src/mnemofy`
- [X] All tests pass
- [X] Coverage ≥ 85% overall
- [X] No test warnings
- [X] Document final coverage numbers

**Dependencies**: T-048

---

### T-050: Test Installation from Source
**Phase**: Release  
**Priority**: P1  
**Estimate**: 0.5 hours

**Description**: Verify package installs correctly.

**Acceptance Criteria**:
- [ ] Create fresh virtualenv
- [ ] Run `pip install -e .`
- [ ] Run `mnemofy transcribe --help` → verify new flags shown
- [ ] Test basic transcription with all outputs
- [ ] No import errors

**Dependencies**: T-048

---

### T-051: Build Distribution
**Phase**: Release  
**Priority**: P1  
**Estimate**: 0.5 hours

**Description**: Build wheel and sdist.

**Acceptance Criteria**:
- [ ] Run `python -m build`
- [ ] Verify dist/ contains .whl and .tar.gz
- [ ] Check wheel contents (files included correctly)
- [ ] Test installation from built wheel

**Dependencies**: T-050

---

### T-052: Upload to PyPI
**Phase**: Release  
**Priority**: P1  
**Estimate**: 0.5 hours

**Description**: Publish to PyPI.

**Acceptance Criteria**:
- [ ] Run `twine check dist/*`
- [ ] Upload: `twine upload dist/*`
- [ ] Verify package on PyPI: https://pypi.org/project/mnemofy/
- [ ] Test installation: `pip install mnemofy==0.8.0`

**Dependencies**: T-051

---

### T-053: Tag v0.8.0 Release
**Phase**: Release  
**Priority**: P1  
**Estimate**: 0.25 hours

**Description**: Create git tag for release.

**Acceptance Criteria**:
- [ ] Create tag: `git tag v0.8.0`
- [ ] Add tag message with release summary
- [ ] Verify tag created: `git tag -l`

**Dependencies**: T-052

---

### T-054: Push to Remote
**Phase**: Release  
**Priority**: P1  
**Estimate**: 0.25 hours

**Description**: Push code and tag to remote.

**Acceptance Criteria**:
- [ ] Push branch: `git push origin 002-enhanced-output-formats`
- [ ] Push tag: `git push origin v0.8.0`
- [ ] Merge to main (if ready)
- [ ] Verify on GitHub/remote

**Dependencies**: T-053

---

## Summary

**Total Tasks**: 54  
**Estimated Time**: 40-50 hours

**Task Distribution**:
- Phase 1 (Foundation): 5 tasks, 6-8 hours
- Phase 2 (Formatters): 7 tasks, 8-10 hours
- Phase 3 (Notes): 11 tasks, 12-15 hours
- Phase 4 (CLI): 7 tasks, 4-6 hours
- Phase 5 (Testing): 10 tasks, 6-8 hours
- Phase 6 (Documentation): 7 tasks, 3-4 hours
- Phase 7 (Release): 7 tasks, 2-3 hours

**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 7 (Phase 6 can parallelize)

**Target Completion**: v0.8.0 release in 5-7 weeks
