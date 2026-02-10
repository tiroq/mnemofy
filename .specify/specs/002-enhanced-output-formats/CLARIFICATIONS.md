# Specification Clarifications

**Feature**: 002-enhanced-output-formats  
**Date**: 2025-01-26  
**Status**: Complete (5/5 questions answered)

---

## Summary

This document records the clarification decisions made during specification review. All decisions have been integrated into [spec.md](./spec.md), [plan.md](./plan.md), [tasks.md](./tasks.md), and [README.md](./README.md).

---

## Clarification Session

### Q1: Audio File Location

**Question**: Where should `.mnemofy.wav` be saved when `--outdir` is specified?

**Options Considered**:
- A: Next to original video (ignores --outdir for audio only)
- B: In --outdir like other outputs (keeps all artifacts together)
- C: User chooses via separate --audiodir flag

**Decision**: **B** - In --outdir like other outputs

**Rationale**: Keeps all artifacts together in one location for easier management and cleanup.

**Impact**:
- **spec.md**: Updated US-001, file naming example
- **plan.md**: Updated data flow diagram, Phase 1 description
- **tasks.md**: Updated T-002, T-004, T-005 acceptance criteria
- **README.md**: Updated "Audio Extraction" section

---

### Q2: Format Failure Handling

**Question**: If one output format fails to generate, what should mnemofy do?

**Options Considered**:
- A: Abort entire operation (fail-fast approach)
- B: Skip failed format, complete others (log warning) - best effort
- C: Retry failed format once, then skip if still failing

**Decision**: **B** - Skip failed format, complete others (best effort)

**Rationale**: Ensures partial output rather than complete failure. Users get maximum possible output even if one formatter has a bug.

**Impact**:
- **spec.md**: Updated US-004, non-functional requirements (resilience)
- **plan.md**: Added to clarifications summary
- **tasks.md**: Updated T-027 error handling requirements
- **README.md**: Added "Error Handling" section

---

### Q3: Minimum Transcript Length for Notes

**Question**: What minimum transcript length should trigger structured notes extraction?

**Options Considered**:
- A: No minimum (generate notes for any length)
- B: 30 seconds minimum (skip notes for very short clips)
- C: 2 minutes minimum (meaningful conversation only)

**Decision**: **B** - 30 seconds minimum

**Rationale**: Very short clips (<30s) lack sufficient context for meaningful structured notes. Avoids generating sparse/useless notes files.

**Impact**:
- **spec.md**: Updated US-003 with minimum viable notes requirement
- **plan.md**: Added to clarifications summary
- **tasks.md**: Updated T-015 to include 30-second check
- **README.md**: Updated "Notes Philosophy" section

---

### Q4: SRT Timing Precision

**Question**: What timing precision should SRT format use?

**Options Considered**:
- A: Milliseconds (HH:MM:SS,mmm) - standard SubRip specification
- B: Centiseconds (HH:MM:SS.cc) - simpler, less precise
- C: Microseconds (HH:MM:SS.mmmmmm) - maximum precision

**Decision**: **A** - Milliseconds (HH:MM:SS,mmm)

**Rationale**: Standard SubRip specification compliance ensures compatibility with all subtitle editors and players.

**Impact**:
- **spec.md**: Updated US-002 SRT format specification
- **plan.md**: Updated T-008 task description
- **tasks.md**: Updated T-008 acceptance criteria

---

### Q5: JSON Schema Versioning

**Question**: Should JSON output include a schema version field for future compatibility?

**Options Considered**:
- A: No version field (keep JSON simple)
- B: Include `'schema_version': '1.0'` field for future compatibility
- C: Use semantic versioning tied to mnemofy version

**Decision**: **B** - Include `'schema_version': '1.0'` field

**Rationale**: Enables future format evolution while maintaining backward compatibility tracking. Minimal overhead for significant long-term benefit.

**Impact**:
- **spec.md**: Updated US-002 JSON format specification
- **plan.md**: Added to clarifications summary
- **tasks.md**: Updated T-009 to include schema_version field

---

## Coverage Analysis

### Taxonomy Assessment

| Category | Status | Notes |
|----------|--------|-------|
| **Functional Scope & Behavior** | ✅ Resolved | Audio location, format failures clarified |
| **Domain & Data Model** | ✅ Clear | Output files, formats well-defined |
| **Interaction & UX Flow** | ✅ Resolved | Error handling, minimum notes length |
| **Non-Functional Quality** | ✅ Resolved | Resilience (best-effort), timing precision |
| **Integration & External** | ✅ Clear | ffmpeg, faster-whisper documented |
| **Edge Cases & Failure** | ✅ Resolved | Format failures, short transcripts |
| **Constraints & Tradeoffs** | ✅ Clear | Backward compatibility maintained |
| **Terminology & Consistency** | ✅ Clear | Consistent use of outdir, formats |
| **Completion Signals** | ✅ Clear | Acceptance criteria well-defined |
| **Misc / Placeholders** | ✅ Clear | No unresolved TODOs |

**Overall Status**: All critical ambiguities resolved. Specification ready for planning and implementation.

---

## Next Steps

✅ **Specification complete** - All clarifications applied  
✅ **Documents updated** - spec.md, plan.md, tasks.md, README.md  
⏳ **Ready for planning** - Proceed to `/speckit.plan` (or directly to implementation)  
⏳ **Branch creation** - Create `002-enhanced-output-formats` branch  

---

## Implementation Notes

**Key Design Decisions Locked**:
1. **Artifact Centralization**: All outputs (audio, transcripts, notes) save to --outdir
2. **Resilient Processing**: Best-effort approach for format generation
3. **Quality Thresholds**: 30-second minimum for structured notes
4. **Standards Compliance**: SRT format follows SubRip spec precisely
5. **Future-Proofing**: JSON includes schema versioning

**Risk Mitigation Applied**:
- Format failures won't crash entire pipeline (best-effort)
- Short clips won't generate useless notes files (30s minimum)
- SRT files guaranteed compatible with standard tools (millisecond precision)
- JSON format evolution supported (schema_version field)

**Testing Focus Areas** (derived from clarifications):
- OutputManager paths validation (all files to outdir)
- Format error handling (skip failed, complete others)
- Notes generation threshold (30-second check)
- SRT timing precision (millisecond accuracy)
- JSON schema_version field presence
