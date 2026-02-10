# Feature 002: Enhanced Output Formats and Pipeline

**Status**: Specification Complete  
**Target**: v0.8.0  
**Effort**: 40-50 hours (5-7 weeks)

## Quick Links

- **[Feature Specification](./spec.md)** - Complete requirements and user stories
- **[Implementation Plan](./plan.md)** - Architecture and phase breakdown  
- **[Task Breakdown](./tasks.md)** - 54 detailed tasks with acceptance criteria

## Overview

This feature implements comprehensive output management for mnemofy, transforming it from a basic transcription tool into a complete meeting documentation pipeline.

### What's New

**Multi-Format Transcripts**:
- `.transcript.txt` - Timestamped plain text
- `.transcript.srt` - Industry-standard subtitles
- `.transcript.json` - Machine-parseable with metadata

**Structured Meeting Notes**:
- 7 required sections with timestamp citations
- Topics, decisions, action items extraction
- Concrete mentions (names, URLs, dates)
- Risks and open questions tracking

**Enhanced Workflow**:
- Automatic audio extraction from video (saved next to input)
- Output directory control (`--outdir`)
- Language specification (`--lang`)
- Notes generation modes (`--notes basic|llm`)

## Implementation Status

| Phase | Progress | Status |
|-------|----------|--------|
| Phase 1: Output Manager | 0/5 tasks | ⏳ Not Started |
| Phase 2: Formatters | 0/7 tasks | ⏳ Not Started |
| Phase 3: Notes Generator | 0/11 tasks | ⏳ Not Started |
| Phase 4: CLI Integration | 0/7 tasks | ⏳ Not Started |
| Phase 5: Testing | 0/10 tasks | ⏳ Not Started |
| Phase 6: Documentation | 0/7 tasks | ⏳ Not Started |
| Phase 7: Release | 0/7 tasks | ⏳ Not Started |

**Overall**: 0/54 tasks complete (0%)

## Getting Started

1. **Review the specification**: Read [spec.md](./spec.md) for complete requirements
2. **Check implementation plan**: See [plan.md](./plan.md) for architecture details
3. **Browse tasks**: Review [tasks.md](./tasks.md) for task-level breakdown
4. **Create feature branch**: `git checkout -b 002-enhanced-output-formats`
5. **Begin Phase 1**: Start with OutputManager implementation

## Key Technical Decisions

**Audio Extraction**: 
- Save `.mnemofy.wav` to --outdir with other outputs (default: current dir)
- Keeps all artifacts together in one location

**Format Consistency**:
- All three transcript formats use identical segment boundaries
- Guarantees timing consistency across TXT/SRT/JSON

**Notes Philosophy**:
- Basic mode: 100% deterministic, zero hallucination
- All extracted items MUST cite timestamps
- If uncertain, mark as "unclear" with timestamp
- Minimum 30 seconds of transcript required for structured notes extraction

**Error Handling**:
- Best-effort approach: if one format fails, complete others
- Log warnings for failed formats, continue processing
- Ensures partial output rather than complete failure

**Backward Compatibility**:
- All new flags are optional
- Existing CLI usage continues to work
- No breaking changes to API

## Dependencies

**Feature Prerequisites**:
- ✅ Feature 001 (Adaptive ASR Model Selection) complete
- ✅ ffmpeg available on system
- ✅ faster-whisper integration working

**External Requirements**:
- ffmpeg for audio extraction
- No new Python dependencies needed

## Success Criteria

- ✅ 100% of video inputs extract audio to `.mnemofy.wav`
- ✅ 100% of transcriptions produce 4 formats (TXT+SRT+JSON+MD)
- ✅ 100% of notes sections cite timestamps
- ✅ 90%+ test coverage across new modules
- ✅ SRT files validated in subtitle editors
- ✅ Backward compatible with existing usage

## Timeline

```
Week 1-2: Phases 1-2 (Foundation + Formatters)
Week 3-4: Phase 3 (Enhanced Notes)
Week 5: Phases 4-5 (CLI Integration + Testing)
Week 6-7: Phases 6-7 (Documentation + Release)
```

**Estimated Completion**: 5-7 weeks from start

## Contact

For questions or clarifications, see the main specification documents or create an issue.

---

**Next Step**: Create feature branch and start Phase 1 (OutputManager)
