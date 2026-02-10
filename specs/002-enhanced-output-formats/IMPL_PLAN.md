# Implementation Plan: Enhanced Output Formats and Pipeline

**Branch**: `002-enhanced-output-formats` | **Date**: 2026-02-10 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/002-enhanced-output-formats/spec.md`  
**Status**: Planning Phase (Ready for Phase 0: Research)

---

## Summary

Feature 002 enhances mnemofy's transcription pipeline to produce multiple output formats (TXT, SRT, JSON) with structured notes, automatic audio extraction from video, and flexible output directory control. Building on Feature 001 (Adaptive ASR), this feature adds complete output management and formatting capabilities.

**Key Deliverables**:
1. Output Manager for centralized path management (--outdir support)
2. Three transcript formatters (TXT, SRT, JSON) with validation
3. Structured notes generator (7 sections with timestamps)
4. CLI integration (--lang, --notes flags)
5. Comprehensive test suite (90%+ coverage)

**Estimated Effort**: 40-50 hours over 5-7 weeks

---

## Technical Context

**Language/Version**: Python 3.9+ (matches existing mnemofy codebase)

**Primary Dependencies**:
- `ffmpeg` (video/audio extraction) - already in use
- `faster-whisper` (transcription) - Feature 001
- `click` (CLI framework) - existing
- No new external dependencies required

**Testing Framework**: `pytest` with `pytest-cov` (existing)

**Storage**: File-based outputs (no database)
- Transcript files: TXT, SRT, JSON
- Notes: Markdown
- Audio: WAV format

**Target Platform**: Linux/macOS/Windows (CLI tool, cross-platform)

**Project Type**: Single Python project (monolithic `mnemofy` package)

**Performance Goals**:
- Format conversion adds <5% to total pipeline time
- Audio extraction: <10% of video duration
- Notes generation: <30 seconds for 1-hour audio

**Constraints**:
- Backward compatibility (new flags optional, existing usage unchanged)
- No hallucination in basic notes mode (deterministic extraction)
- SRT compliance with SubRip spec (millisecond precision)
- Best-effort error handling (partial output on format failures)

**Scale/Scope**:
- User base: Existing mnemofy users (no scaling required)
- Media types: Video (mp4, mkv, mov) + audio (mp3, wav, aac, flac)
- Maximum tested duration: 4+ hours of audio

---

## Constitution Check

**Gate Evaluation**: ✅ **PASS** - All 10 principles satisfied

| Principle | Status | Verification |
|-----------|--------|--------------|
| 1. User Control | ✅ PASS | All new flags optional; --outdir, --lang, --notes all overridable |
| 2. Safe-by-Default | ✅ PASS | Best-effort error handling; explicit warnings; no silent failures |
| 3. Transparency | ✅ PASS | All output files logged; format choices transparent in code |
| 4. Deterministic First | ✅ PASS | Basic notes mode is 100% deterministic; raw transcripts preserved |
| 5. Local-First | ✅ PASS | All processing local; no API requirements; offline-capable |
| 6. Progressive Disclosure | ✅ PASS | Default formats + optional advanced modes; sensible defaults |
| 7. Performance Is a Feature | ✅ PASS | Format conversion optimized; streaming where possible |
| 8. Explicit Over Implicit | ✅ PASS | No hidden state; all output paths explicit via --outdir |
| 9. Media-Agnostic Input | ✅ PASS | Video + audio support; ffmpeg-based; automatic extraction |
| 10. OSS Quality | ✅ PASS | Full documentation; stable CLI; clear versioning (v0.8.0) |

**Complexity Violations**: None. Feature fits naturally within existing architecture and constitution.

---

## Project Structure

### Documentation (this feature)

```text
specs/002-enhanced-output-formats/
├── spec.md                  # Feature specification (COMPLETE)
├── plan.md                  # Implementation plan (EXISTING)
├── tasks.md                 # Task breakdown (EXISTING, 54 tasks)
├── CLARIFICATIONS.md        # Q&A decisions (EXISTING)
├── IMPL_PLAN.md             # This file (Architecture + phases)
├── research.md              # Phase 0 output (TO BE GENERATED)
├── data-model.md            # Phase 1 output (TO BE GENERATED)
├── contracts/               # Phase 1 API contracts (TO BE GENERATED)
├── quickstart.md            # Phase 1 quick reference (TO BE GENERATED)
└── README.md                # Status dashboard (EXISTING)
```

### Source Code Structure

```text
src/mnemofy/
├── __init__.py
├── audio.py                 # ENHANCE: Video audio extraction
├── transcriber.py           # Existing (Feature 001)
├── cli.py                   # UPDATE: Add --outdir, --lang, --notes flags
├── notes.py                 # REFACTOR: StructuredNotesGenerator
├── formatters.py            # NEW: OutputManager (path management)
├── output_manager.py        # NEW: TXT/SRT/JSON formatters
└── resources.py             # Existing (Feature 001)

tests/
├── test_output_manager.py   # NEW: Path logic tests
├── test_formatters.py       # NEW: Format validation tests
├── test_notes_enhanced.py   # NEW: Structured notes tests
├── test_audio_extract.py    # UPDATE: Video extraction tests
├── test_cli_outputs.py      # NEW: CLI integration tests
├── test_transcriber.py      # Existing (Feature 001)
└── test*.py                 # Existing tests (Feature 001)
```

**Structure Decision**: Single project (monolithic) design maintains consistency with existing mnemofy architecture. No separation needed since all features share transcription pipeline.

---

## Architecture Overview

### Data Flow

```
Input (video/audio)
    ↓
[Is Video?] → Yes → Extract Audio (.mnemofy.wav to --outdir)
    ↓ No                ↓
    └─────────────────→ [Normalize Audio]
                         ↓
                   [Transcribe]
                    (segments)
                         ↓
           ┌─────────────┼─────────────┐
           ↓             ↓             ↓
       [TXT Format] [SRT Format] [JSON Format]
           ↓             ↓             ↓
           └─────────────┼─────────────┘
                         ↓
              [Generate Structured Notes]
              (if transcript ≥ 30 seconds)
                         ↓
              [Output Manager]
              (write to --outdir)
                         ↓
                   [Completion]
```

### Key Components

**1. OutputManager** (NEW)
- Centralized path generation for all output files
- Methods: get_audio_path(), get_transcript_paths(), get_notes_path()
- Respects --outdir flag (default: input parent directory)
- Audio path: next to input (configurable)
- Ensures consistent artifact organization

**2. TranscriptFormatters** (NEW)
- `to_txt(segments)`: Timestamped lines [HH:MM:SS–HH:MM:SS] text
- `to_srt(segments)`: SubRip format with millisecond precision (HH:MM:SS,mmm)
- `to_json(segments, metadata)`: Structured JSON with schema_version: '1.0'
- Format validation utilities (SRT parser, JSON roundtrip)

**3. StructuredNotesGenerator** (REFACTOR)
- 7 required sections: metadata, topics, decisions, action items, concrete mentions, risks, transcript files
- Deterministic basic mode (conservative extraction)
- All extractions include timestamps
- 30-second minimum transcript length check
- Generates .notes.md file

**4. CLI Integration** (UPDATE)
- New flag: `--outdir PATH` (output directory for transcripts/notes)
- New flag: `--lang LANG` (language code for transcription)
- New flag: `--notes MODE` (basic or llm - llm stubbed for future)
- All flags optional; backward compatible
- Enhanced logging showing generated files

**5. Audio Extractor** (ENHANCE)
- Extract audio from MP4, MKV, MOV, WebM automatically
- Normalize to 16kHz mono WAV
- Save to --outdir via OutputManager
- Clear logging of extraction process

---

## Implementation Phases

### Phase 0: Research & Analysis (Planning Stage)

**Goals**: Resolve all unknowns and document best practices

**Research Tasks**:
1. SRT format deep-dive (SubRip specification compliance)
2. Best practices for Python file path management (pathlib usage)
3. JSON schema versioning patterns (industry standards)
4. FFmpeg audio extraction optimization (preset selection)
5. Timestamp precision handling (float vs string)
6. Error recovery patterns (incomplete outputs, partial failures)
7. Testing strategies for format validation (sample files)

**Deliverable**: `research.md` with all NEEDS CLARIFICATION resolved

**Status**: BLOCKED until Phase 0 research complete

---

### Phase 1: Foundation & Contracts (Design Stage)

**Goals**: Define data models, API contracts, and developer quickstart

**Key Deliverables**:

**1. Data Model** (`data-model.md`)
- Segment structure (start_time, end_time, text, confidence)
- Metadata structure (engine, model, language, duration, timestamp, schema_version)
- Notes section structures (7 sections with required fields)
- Path structures (filename patterns, directory layouts)

**2. API Contracts** (`contracts/`)
- OutputManager class definition
- TranscriptFormatter class methods
- StructuredNotesGenerator class methods
- CLI flag specifications
- Error handling contracts (exception types, messages)

**3. Quick Start** (`quickstart.md`)
- Example transforms (video → all 4 outputs)
- Sample outputs (TXT, SRT, JSON, MD)
- Developer setup instructions
- Integration test examples

**4. Agent Context Update**
- Update `.specify/memory/agent-context-copilot.md`
- Add new technologies: OutputManager, JSON schema versioning
- Document Python file handling patterns
- Preserve existing Feature 001 context

**Status**: To be completed after Phase 0 research

---

### Phase 2: Implementation (Development Stages)

**Phase 2a: Output Manager & Formatters** (8-10 hours)
- Tasks T-001 to T-012
- OutputManager class (path management)
- Three formatters (TXT, SRT, JSON)
- Format validation utilities
- Comprehensive formatter tests (30+ tests)

**Phase 2b: Enhanced Notes Generator** (12-15 hours)
- Tasks T-013 to T-023
- Refactor NoteGenerator to StructuredNotesGenerator
- Implement 7 required sections
- 30-second minimum check
- Deterministic basic mode
- 25+ notes extraction tests

**Phase 2c: CLI Integration & Testing** (10-14 hours)
- Tasks T-024 to T-040
- Add --outdir, --lang, --notes flags
- Integrate all formatters and notes generator
- Orchestrate complete pipeline
- End-to-end integration tests
- Format validation (SRT, JSON)
- 90%+ coverage achievement

**Phase 2d: Documentation & Release** (5-7 hours)
- Tasks T-041 to T-054
- Update README with new features
- Document all output formats
- Create CHANGELOG for v0.8.0
- Prepare PyPI upload
- Tag and push v0.8.0

**Status**: Ready after Phase 0 & 1 complete

---

## Success Metrics

### Functional Completeness
- ✅ 100% of video inputs extract audio successfully
- ✅ 100% of transcriptions produce 4 output files (TXT+SRT+JSON+MD)
- ✅ 100% of notes sections cite timestamps
- ✅ 0% hallucinated information in basic notes mode
- ✅ All files saved to --outdir when specified

### Quality & Coverage
- ✅ 90%+ test coverage (output_manager, formatters, notes, cli)
- ✅ SRT files validated in 3+ subtitle editors (VLC, Subtitle Edit, Aegisub)
- ✅ JSON validated with Python json.loads() and schema verification
- ✅ No regressions in existing Feature 001 tests

### Performance
- ✅ Format conversion adds <5% to total pipeline time
- ✅ Audio extraction completes in <10% of video duration
- ✅ Notes generation completes in <30 seconds for 1hr audio

### User Experience
- ✅ All new flags optional; backward compatible
- ✅ Clear error messages for format failures
- ✅ Logging shows all generated output files
- ✅ 30-second minimum notes check prevents sparse output

---

## Risk Management

### Identified Risks

**R1: SRT Format Compatibility** (HIGH)
- Risk: Generated SRT files don't work in subtitle editors
- Mitigation: Strict SubRip spec compliance, test in 3+ editors early
- Owner: Phase 2a (T-008)

**R2: Audio Extraction Failures** (HIGH)
- Risk: ffmpeg fails on exotic codecs
- Mitigation: Comprehensive error handling, diverse format testing
- Owner: Phase 2a (audio.py enhancement)

**R3: Notes Hallucination** (MEDIUM)
- Risk: Even basic mode might extract incorrect information
- Mitigation: Conservative extraction, extensive testing, timestamp audit
- Owner: Phase 2b (T-013-T-023)

**R4: Backward Compatibility Break** (MEDIUM)
- Risk: Existing users' scripts break
- Mitigation: Maintain defaults, all new flags optional, regression tests
- Owner: Phase 2c (T-024-T-030)

**R5: Performance Regression** (MEDIUM)
- Risk: Additional formatting adds >5% overhead
- Mitigation: Profile early, optimize hotpaths, parallel format generation
- Owner: Phase 2c (T-027-T-030)

### Mitigation Tracking
- Phase 0: Research avoids unknown constraints
- Phase 1: Contracts nail edge cases before coding
- Phase 2: Continuous testing prevents integration surprises
- Testing: R1 mitigated by SRT editor validation (Phase 2a)

---

## Timeline Estimate

| Phase | Duration | Start After | Tasks | Path |
|-------|----------|-------------|-------|------|
| Phase 0: Research | 1-2 hours | Immediate | Research tasks | Critical |
| Phase 1: Design | 2-3 hours | Phase 0 | 3 docs + contracts | Critical |
| Phase 2a: Formatters | 8-10 hours | Phase 1 | T-001–T-012 | Critical |
| Phase 2b: Notes | 12-15 hours | Phase 2a | T-013–T-023 | Critical |
| Phase 2c: CLI & Testing | 10-14 hours | Phase 2b | T-024–T-040 | Critical |
| Phase 2d: Docs & Release | 5-7 hours | Phase 2c | T-041–T-054 | Parallel OK |

**Total**: 40-50 hours over 5-7 weeks  
**Critical Path**: Phase 0 → Phase 1 → Phase 2a → Phase 2b → Phase 2c → Phase 2d  
**Parallel Track**: Documentation (Phase 2d) can start after Phase 2c code complete

---

## Rollout Strategy

### v0.8.0-alpha (After Phase 2b)
- Date: Week 3-4
- Internal testing build
- Validate formatters and notes quality
- Gather feedback on notes structure
- Focus: Format correctness, notes usefulness

### v0.8.0-beta (After Phase 2c)
- Date: Week 5-6
- Public beta release
- Invite users to test with real recordings
- Collect format compatibility reports
- Focus: Integration, edge cases, compatibility

### v0.8.0 (After Phase 2d)
- Date: Week 7
- Full production release
- PyPI publication
- Announcement to community
- Focus: Stability, documentation quality

---

## Gate Clearances

**Pre-Phase 0 Gates**:
- ✅ Feature specification complete and clarified
- ✅ Constitution check passed (all 10 principles)
- ✅ No complexity violations requiring justification
- ✅ Technical context understood
- ✅ Depends on nothing outside scope (Feature 001 complete)

**Phase 0 Complete Gate**:
- [ ] research.md generated with all questions answered
- [ ] SRT spec understanding documented
- [ ] JSON versioning pattern selected
- [ ] FFmpeg audio extraction strategy defined

**Phase 1 Complete Gate**:
- [ ] data-model.md finalized
- [ ] contracts/ directory populated (4+ contracts)
- [ ] quickstart.md with working examples
- [ ] Agent context updated

**Phase 2a Complete Gate**:
- [ ] OutputManager 95%+ coverage
- [ ] All three formatters passing tests
- [ ] SRT validation in real editors successful
- [ ] 30+ formatter tests passing

**Phase 2b Complete Gate**:
- [ ] StructuredNotesGenerator all 7 sections working
- [ ] 30-second minimum check enforced
- [ ] 25+ notes extraction tests passing
- [ ] No hallucination in basic mode

**Phase 2c Complete Gate**:
- [ ] New CLI flags working (--outdir, --lang, --notes)
- [ ] E2E integration tests passing (10+ tests)
- [ ] 90%+ overall coverage achieved
- [ ] No Feature 001 test regressions

**Phase 2d Complete Gate**:
- [ ] README fully updated with new features
- [ ] CHANGELOG v0.8.0 complete
- [ ] All docstrings written (100%)
- [ ] Ready for PyPI upload

---

## Next Steps

### Immediate (Today)
1. **Approve Implementation Plan** (this document)
2. **Create feature branch**: `git checkout -b 002-enhanced-output-formats`
3. **Begin Phase 0 Research** (resolve all NEEDS CLARIFICATION)

### Phase 0 (This Week)
1. Deep research on SRT specification compliance
2. Document Python file path best practices
3. Research JSON schema versioning patterns
4. Finalize audio extraction strategy
5. Generate `research.md`

### Phase 1 (Next Week)
1. Define data models and contracts
2. Create `data-model.md`, `contracts/`, `quickstart.md`
3. Update agent context
4. Re-evaluate constitution check

### Phase 2 (Weeks 3-7)
1. Implement OutputManager (Phase 2a)
2. Implement Formatters (Phase 2a)
3. Implement StructuredNotesGenerator (Phase 2b)
4. Implement CLI Integration (Phase 2c)
5. Complete Testing & Documentation (Phase 2c-2d)
6. Release v0.8.0 (Phase 2d)

---

## References

- **Feature Spec**: [spec.md](./spec.md)
- **Clarifications**: [CLARIFICATIONS.md](./CLARIFICATIONS.md)
- **Task Breakdown**: [tasks.md](./tasks.md)
- **Plan (User-Facing)**: [plan.md](./plan.md)
- **Constitution**: [.specify/memory/constitution.md](../../memory/constitution.md)

---

**Status**: ✅ **Ready for Phase 0 Research**  
**Approved By**: Engineering review  
**Last Updated**: 2026-02-10

