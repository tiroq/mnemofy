# Phase 0 & 1 Task Execution Plan

**Feature**: 002-enhanced-output-formats  
**Branch**: `002-enhanced-output-formats` (Created ✓)  
**Status**: Ready to execute Phase 0 Research  
**Reference**: [IMPL_PLAN.md](./IMPL_PLAN.md)

---

## Phase 0: Research & Analysis (1-2 hours)

### R-001: SRT Format Specification Deep-Dive
**Objective**: Master SubRip format to ensure 100% compatibility

**Tasks**:
- [ ] Read official SubRip format specification
- [ ] Document timing format requirements (millisecond precision with comma)
- [ ] Identify edge cases: overlapping segments, long duration (>24h), special characters
- [ ] Test SRT samples in 3 editors: VLC, Subtitle Edit, default media player
- [ ] Document: valid vs invalid timing formats, character escaping rules
- [ ] Expected Output: Section in `research.md` with SRT specification summary

**Estimated**: 25 minutes
**Owner**: Implementation lead
**Files to Review**:
- Existing SRT samples (if any in test fixtures)
- Python srt library documentation (if using existing parser)

---

### R-002: Python File Path Management Best Practices
**Objective**: Establish consistent, cross-platform path handling

**Tasks**:
- [ ] Review `pathlib.Path` vs string-based path handling (decide on standard)
- [ ] Document path construction patterns for output files
- [ ] Test path handling on macOS (dev machine) - absolute, relative, symlinks
- [ ] Document cross-platform considerations (Windows drive letters, separators)
- [ ] Create path pattern template: how to construct `<outdir>/<basename>.format`
- [ ] Expected Output: Section in `research.md` with path handling guidelines

**Estimated**: 20 minutes
**Owner**: Implementation lead
**Decision Point**: Will all paths use `pathlib.Path` consistently?

---

### R-003: JSON Schema Versioning Patterns
**Objective**: Design schema version strategy for future compatibility

**Tasks**:
- [ ] Research semantic versioning for JSON schemas (e.g., "1.0", "2.0")
- [ ] Review industry standards (JSON Schema spec, semantic versioning)
- [ ] Decide: Major.Minor.Patch (1.0.0) or just Major.Minor (1.0)?
- [ ] Document migration strategy: how consumers handle new versions
- [ ] Plan fields: schema_version, transcription_engine_version, mnemofy_version
- [ ] Expected Output: Section in `research.md` with JSON versioning strategy

**Estimated**: 20 minutes
**Owner**: Design lead
**Decision Point**: Schema version format (pick: "1.0" or "1.0.0")?

---

### R-004: FFmpeg Audio Extraction Optimization
**Objective**: Verify ffmpeg strategy for efficient video → audio conversion

**Tasks**:
- [ ] Test ffmpeg command: `ffmpeg -i input.mp4 -q:a 0 -map a output.wav`
- [ ] Measure extraction time on sample video (30 sec, 1 hour, 4 hour)
- [ ] Verify output: 16kHz mono WAV format correct
- [ ] Document: supported input formats (mp4, mkv, mov, webm)
- [ ] Test edge cases: corrupted headers, exotic codecs (VP9, HEVC)
- [ ] Document fallback strategy when extraction fails
- [ ] Expected Output: Section in `research.md` with ffmpeg strategy

**Estimated**: 20 minutes
**Owner**: Audio engineer (or implementation lead)
**Dependency**: Verify ffmpeg already present in development environment

---

### R-005: Timestamp Precision & Handling
**Objective**: Resolve how to represent timestamps (float vs string)

**Tasks**:
- [ ] Document: faster-whisper returns timestamps as floats (seconds)
- [ ] Decide: Convert to strings (HH:MM:SS,mmm) early or late in pipeline?
- [ ] Determine: What precision to preserve? (microseconds →  milliseconds in SRT)
- [ ] Research: Rounding strategy (banker's rounding vs round-half-up)
- [ ] Document: Timestamp handling in each format (TXT, SRT, JSON)
- [ ] Expected Output: Section in `research.md` with timestamp handling strategy

**Estimated**: 20 minutes
**Owner**: Implementation lead
**Decision Point**: Early vs late string conversion?

---

### R-006: Error Recovery Patterns for Partial Failures
**Objective**: Design best-effort error handling approach

**Tasks**:
- [ ] Document: Which errors are recoverable? (write permission, format error, memory)
- [ ] Decide: Log to file, stderr, both?
- [ ] Define partial success: which files justify continuing vs aborting?
- [ ] Research: Python exception hierarchy for clarity
- [ ] Document: User-facing error messages for each failure scenario
- [ ] Expected Output: Section in `research.md` with error handling pattern

**Estimated**: 20 minutes
**Owner**: Error handling SME
**Decision Point**: What constitutes "best effort" success?

---

### R-007: Format Validation Testing Strategy
**Objective**: Plan how to validate TXT, SRT, JSON formats

**Tasks**:
- [ ] Identify existing test fixtures or create minimal samples
- [ ] Research: SRT parser libraries (srt, subtitle-parsers, etc.)
- [ ] Decide: Use external parser or implement validation?
- [ ] Plan: JSON schema validation (jsonschema library)
- [ ] Document: Acceptance criteria for each format (what makes valid SRT?)
- [ ] Expected Output: Section in `research.md` with validation testing approach

**Estimated**: 20 minutes
**Owner**: QA lead
**Decision Point**: Which libraries to use for validation?

---

## Phase 0 Output: research.md

Create a comprehensive research document addressing all unknowns:

```markdown
# Research Notes: Enhanced Output Formats

## 1. SRT Format Specification
[SRT deep-dive findings: timing precision, edge cases, compatibility notes]

## 2. Python File Path Management
[Pathlib strategy, cross-platform handling, pattern templates]

## 3. JSON Schema Versioning
[Schema version format, migration strategy, field planning]

## 4. FFmpeg Audio Extraction
[Extraction strategy, supported formats, edge case handling]

## 5. Timestamp Precision & Handling
[Float to string conversion strategy, rounding approach]

## 6. Error Recovery Patterns
[Partial failure handling, logging strategy, user-facing errors]

## 7. Format Validation Testing
[Validation strategy, libraries to use, acceptance criteria]

## Decisions Made
- Audio extraction: ffmpeg with settings [...]
- Path handling: pathlib.Path throughout
- JSON schema version: "1.0" format
- Error handling: best-effort with detailed logging
- Validation: [libraries chosen]

## Open Questions
[If any remain after research]
```

**Estimated Time for All Research**: 2 hours total (all 7 items)

**Gate**: Phase 0 complete when `research.md` is written with all decisions documented.

---

## Phase 1: Foundation & Contracts (2-3 hours)

### D-001: Data Model Definition
**Objective**: Define all data structures used in Feature 002

**Deliverable**: `data-model.md` (3-4 pages)

**Tasks**:
- [ ] Define Segment class/dict structure:
  ```python
  Segment = {
    "start_time": float,        # seconds
    "end_time": float,          # seconds
    "text": str,
    "confidence": float | None  # optional
  }
  ```
- [ ] Define Metadata structure:
  ```python
  Metadata = {
    "engine": str,              # "faster-whisper"
    "model": str,               # "base", "small", etc.
    "language": str,            # "en", "es", etc.
    "duration": float,          # seconds
    "timestamp": str,           # ISO 8601
    "schema_version": str       # "1.0"
  }
  ```
- [ ] Define NotesSection structure (7 sections)
- [ ] Define OutputPaths structure (audio, transcripts, notes locations)
- [ ] Document: Type hints for all structures
- [ ] Add: Examples for each structure

**Estimated**: 45 minutes

---

### D-002: OutputManager API Contract
**Objective**: Lock down OutputManager interface before coding

**Deliverable**: `contracts/output-manager.md`

**Tasks**:
- [ ] Define `OutputManager.__init__(input_path, outdir=None)`
- [ ] Define `get_audio_path() -> Path`
- [ ] Define `get_transcript_paths() -> dict[str, Path]`  (txt, srt, json)
- [ ] Define `get_notes_path() -> Path`
- [ ] Define error handling (invalid paths, permission issues)
- [ ] Document: Path resolution logic (relative vs absolute, default to input parent)
- [ ] Add: Usage examples

**Estimated**: 20 minutes

---

### D-003: TranscriptFormatter API Contract
**Objective**: Lock down formatter interface before coding

**Deliverable**: `contracts/formatters.md`

**Tasks**:
- [ ] Define `to_txt(segments: list[Segment]) -> str`
- [ ] Define `to_srt(segments: list[Segment]) -> str`
- [ ] Define `to_json(segments: list[Segment], metadata: Metadata) -> str`
- [ ] Document: Input validation for each formatter
- [ ] Document: Error handling (malformed segments, missing fields)
- [ ] Document: Output format specifications (examples for each)
- [ ] Add: Edge case handling (empty segments, >24h duration, special chars)

**Estimated**: 20 minutes

---

### D-004: StructuredNotesGenerator API Contract
**Objective**: Define notes generation interface

**Deliverable**: `contracts/notes-generator.md`

**Tasks**:
- [ ] Define `StructuredNotesGenerator.__init__(mode="basic")`
- [ ] Define `generate(segments: list[Segment], metadata: Metadata) -> str`
- [ ] Document: 7 required sections and their structure
- [ ] Document: Minimum 30-second transcript length check
- [ ] Document: Deterministic basic mode (no LLM, no hallucination)
- [ ] Document: Timestamp citation requirements
- [ ] Add: Example output showing all 7 sections

**Estimated**: 20 minutes

---

### D-005: CLI Flag Contracts
**Objective**: Define new command-line interface

**Deliverable**: `contracts/cli-flags.md`

**Tasks**:
- [ ] Document `--outdir PATH` flag
  - Type, default, validation
  - Example: `mnemofy transcribe video.mp4 --outdir /output`
- [ ] Document `--lang LANG` flag
  - Type, default, supported languages
  - Example: `mnemofy transcribe audio.mp3 --lang es`
- [ ] Document `--notes MODE` flag
  - Type: "basic" or "llm"
  - Default: "basic"
  - Example: `mnemofy transcribe video.mp4 --notes basic`
- [ ] Document: Backward compatibility (all flags optional)
- [ ] Document: Flag combinations (all can be mixed)
- [ ] Add: Complete usage examples

**Estimated**: 20 minutes

---

### D-006: Quick Start Developer Guide
**Objective**: Enable developers to understand and test Feature 002

**Deliverable**: `quickstart.md` (3-5 pages)

**Tasks**:
- [ ] Create example: Transform video → extract audio + 4 output formats
- [ ] Show TXT format example (with timestamps)
- [ ] Show SRT format example (with millisecond precision)
- [ ] Show JSON format example (with metadata + schema_version)
- [ ] Show Markdown notes example (all 7 sections)
- [ ] Document: How to run integration test
- [ ] Document: How to validate outputs (SRT parser, JSON validation)
- [ ] Provide: Test data file or reference where to get samples

**Estimated**: 30 minutes

---

### D-007: Update Agent Context
**Objective**: Ensure AI assistant has implementation guidance

**Deliverable**: Update `.specify/memory/` files

**Tasks**:
- [ ] Review existing `agent-context-copilot.md` (or create if missing)
- [ ] Add section: OutputManager pattern (path management strategy)
- [ ] Add section: Formatter pattern (multi-format from single source)
- [ ] Add section: JSON schema versioning (1.0 → future proofing)
- [ ] Add section: Python pathlib usage (cross-platform paths)
- [ ] Add section: Best-effort error handling (recover gracefully)
- [ ] Document: Feature 001 compatibility constraints

**Estimated**: 20 minutes

---

## Phase 1 Output Checklist

```
✓ data-model.md (Segment, Metadata, NotesSection structures)
✓ contracts/output-manager.md (OutputManager interface)
✓ contracts/formatters.md (TXT, SRT, JSON formatters)
✓ contracts/notes-generator.md (StructuredNotesGenerator interface)
✓ contracts/cli-flags.md (--outdir, --lang, --notes)
✓ quickstart.md (Examples, test guide)
✓ Agent context updated
```

**Estimated Time for All Design**: 2.5 hours total

**Gate**: Phase 1 complete when all contracts are defined and examples work.

---

## Handoff to Phase 2

Once Phase 0 & 1 are complete:

1. **Implementation starts** with tasks.md T-001 to T-054
2. **Code generation** based on contracts
3. **Testing** using examples from quickstart.md
4. **Validation** against contracts defined in Phase 1

### Phase 2 Task Breakdown (54 tasks)
- **T-001 to T-005**: Output Manager implementation (Phase 2a)
- **T-006 to T-012**: Transcript Formatters (Phase 2a)
- **T-013 to T-023**: Enhanced Notes Generator (Phase 2b)
- **T-024 to T-030**: CLI Integration (Phase 2c)
- **T-031 to T-040**: Testing & Validation (Phase 2c)
- **T-041 to T-054**: Documentation & Release (Phase 2d)

See [tasks.md](./tasks.md) for complete task breakdown.

---

## Execution Timeline

### Today (2026-02-10)
- [ ] Complete Phase 0 research tasks (R-001 to R-007)
- [ ] Write `research.md`
- [ ] Re-evaluate constitution checks

### Tomorrow (2026-02-11)
- [ ] Complete Phase 1 design tasks (D-001 to D-007)
- [ ] Write all contracts and data model docs
- [ ] Create quickstart examples
- [ ] Update agent context

### This Week (2026-02-12+)
- [ ] Begin Phase 2 implementation (T-001, T-002, etc.)
- [ ] Implement OutputManager
- [ ] Implement Formatters
- [ ] Create integration tests

---

## Success Criteria for Phase 0 & 1

**Phase 0 Complete When**:
- [ ] `research.md` written with all 7 research sections
- [ ] All NEEDS CLARIFICATION resolved
- [ ] Team consensus on key decisions (SRT, JSON versioning, error handling)
- [ ] Constitution check re-evaluated and passed

**Phase 1 Complete When**:
- [ ] All 5 contracts written (data model + 4 API contracts)
- [ ] `quickstart.md` with runnable examples
- [ ] Agent context updated with patterns
- [ ] Developers can implement from Phase 2 tasks independently

---

## Progress Tracking

```markdown
## Phase 0: Research (Target: 2 hours)
- [ ] R-001: SRT Format Specification (25 min)
- [ ] R-002: Python File Path Management (20 min)
- [ ] R-003: JSON Schema Versioning (20 min)
- [ ] R-004: FFmpeg Audio Extraction (20 min)
- [ ] R-005: Timestamp Precision (20 min)
- [ ] R-006: Error Recovery Patterns (20 min)
- [ ] R-007: Format Validation Testing (20 min)
- [ ] Write research.md (15 min)

## Phase 1: Design (Target: 2.5 hours)
- [ ] D-001: Data Model (45 min)
- [ ] D-002: OutputManager Contract (20 min)
- [ ] D-003: Formatter Contract (20 min)
- [ ] D-004: NotesGenerator Contract (20 min)
- [ ] D-005: CLI Flags Contract (20 min)
- [ ] D-006: Quickstart Guide (30 min)
- [ ] D-007: Agent Context Update (20 min)
- [ ] Final review & validation (15 min)

Total Planned: 4.5 hours
```

---

**Reference**: [Implementation Plan (IMPL_PLAN.md)](./IMPL_PLAN.md) | [Specification (spec.md)](./spec.md) | [Tasks (tasks.md)](./tasks.md)

