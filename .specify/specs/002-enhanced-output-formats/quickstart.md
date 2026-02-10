# Quick Start: Enhanced Output Formats

**Feature**: 002-enhanced-output-formats  
**Phase**: 1 (Design - Developer Quickstart)  

---

## Overview

This guide enables developers to understand, implement, and test Feature 002. It assumes familiarity with Python, pytest, and the existing mnemofy codebase.

---

## Project Structure

```
src/mnemofy/
├── __init__.py
├── audio.py                 # ENHANCE: Video audio extraction
├── transcriber.py           # Existing
├── cli.py                   # UPDATE: Add --outdir, --lang, --notes flags
├── notes.py                 # REFACTOR: StructuredNotesGenerator
├── formatters.py            # NEW: TranscriptFormatter
├── output_manager.py        # NEW: OutputManager
└── resources.py             # Existing

tests/
├── test_output_manager.py   # NEW: ~40 tests
├── test_formatters.py       # NEW: ~60 tests
├── test_notes_enhanced.py   # NEW: ~40 tests
├── test_audio_extract.py    # UPDATE: Add video tests
├── test_cli_outputs.py      # NEW: ~15 integration tests
└── test_transcriber.py      # Existing (touch if needed)

.specify/specs/002-enhanced-output-formats/
├── research.md              # Phase 0: ✓ Complete
├── data-model.md            # Phase 1: ✓ Complete
└── contracts/
    ├── output-manager.md    # Phase 1: ✓ Complete
    ├── formatters.md        # Phase 1: ✓ Complete
    ├── notes-generator.md   # Phase 1: ✓ Complete
    └── cli-flags.md         # Phase 1: ✓ Complete
```

---

## 1. OutputManager: Path Management

### Purpose
Centralize output path generation for all artifacts.

### Key Files
- **Contract**: `.specify/specs/002-enhanced-output-formats/contracts/output-manager.md`
- **Implementation**: `src/mnemofy/output_manager.py`
- **Tests**: `tests/test_output_manager.py`

### Implementation Tasks (5 tasks, ~6 hours)

**T-001: Create module**
```python
# src/mnemofy/output_manager.py

from pathlib import Path
from typing import Optional, Dict

class OutputManager:
    def __init__(self, input_path: str | Path, outdir: Optional[str | Path] = None):
        # Validate input_path exists
        # Create outdir if needed
        # Store resolved Path objects
        pass
    
    def get_audio_path(self) -> Path:
        # Return: <outdir>/<basename>.mnemofy.wav
        pass
    
    def get_transcript_paths(self) -> Dict[str, Path]:
        # Return: {'txt': ..., 'srt': ..., 'json': ...}
        pass
    
    def get_notes_path(self) -> Path:
        # Return: <outdir>/<basename>.notes.md
        pass
```

**T-002: Test (40+ tests)**
```python
# tests/test_output_manager.py

def test_default_outdir():
    manager = OutputManager("video.mp4")
    assert manager.get_audio_path().parent == Path(".")

def test_custom_outdir():
    manager = OutputManager("video.mp4", outdir="/out")
    assert manager.get_audio_path().parent == Path("/out")

def test_creates_outdir():
    manager = OutputManager("video.mp4", outdir="/tmp/test_outdir")
    assert manager.outdir.exists()

def test_invalid_input():
    with pytest.raises(FileNotFoundError):
        OutputManager("nonexistent.mp4")

# ... 35+ more tests for edge cases
```

---

## 2. TranscriptFormatter: Multi-Format Output

### Purpose
Convert transcript segments to TXT, SRT, JSON formats.

### Key Files
- **Contract**: `.specify/specs/002-enhanced-output-formats/contracts/formatters.md`
- **Implementation**: `src/mnemofy/formatters.py`
- **Tests**: `tests/test_formatters.py`

### Implementation Tasks (7 tasks, ~8 hours)

**T-006: Create module structure**
```python
# src/mnemofy/formatters.py

class TranscriptFormatter:
    @staticmethod
    def to_txt(segments: list[dict]) -> str:
        # Format: [HH:MM:SS–HH:MM:SS] text
        pass
    
    @staticmethod
    def to_srt(segments: list[dict]) -> str:
        # SubRip format: sequence, HH:MM:SS,mmm timing, text
        pass
    
    @staticmethod
    def to_json(segments: list[dict], metadata: dict) -> str:
        # JSON with schema_version, metadata, segments
        pass
```

**T-007–T-009: Implement formatters**

Example TXT output:
```
[00:00:01–00:00:05] This is the first segment
[00:00:05–00:00:10] This is the second segment
```

Example SRT output:
```
1
00:00:01,000 --> 00:00:05,000
This is the first segment

2
00:00:05,000 --> 00:00:10,000
This is the second segment
```

Example JSON output:
```json
{
  "schema_version": "1.0",
  "metadata": {
    "engine": "faster-whisper",
    "model": "base",
    "language": "en",
    "duration": 95.5
  },
  "segments": [
    {"start": 1.0, "end": 5.0, "text": "First segment", "confidence": 0.95},
    {"start": 5.0, "end": 10.0, "text": "Second segment", "confidence": 0.92}
  ]
}
```

**T-010–T-012: Test (60+ tests)**
```python
# tests/test_formatters.py

def test_txt_format():
    segments = [
        {'start': 1.0, 'end': 5.0, 'text': 'Hello'},
        {'start': 5.0, 'end': 10.0, 'text': 'World'},
    ]
    txt = TranscriptFormatter.to_txt(segments)
    assert '[00:00:01–00:00:05] Hello' in txt
    assert '[00:00:05–00:00:10] World' in txt

def test_srt_format():
    srt = TranscriptFormatter.to_srt(segments)
    lines = srt.split('\n')
    assert '1' in lines[0]  # Sequence
    assert '00:00:01,000 --> 00:00:05,000' in srt

def test_json_format():
    metadata = {
        'engine': 'faster-whisper',
        'model': 'base',
        'language': 'en',
        'duration': 10.0,
        'schema_version': '1.0'
    }
    json_str = TranscriptFormatter.to_json(segments, metadata)
    data = json.loads(json_str)
    assert data['schema_version'] == '1.0'
    assert len(data['segments']) == 2

# Validate against SRT parser
import srt
def test_srt_valid_parser():
    srt_str = TranscriptFormatter.to_srt(segments)
    subtitles = list(srt.parse(srt_str))
    assert len(subtitles) == 2
    assert subtitles[0].start == timedelta(seconds=1)
```

---

## 3. StructuredNotesGenerator: Meeting Notes

### Purpose
Extract structured 7-section Markdown notes from transcripts.

### Key Files
- **Contract**: `.specify/specs/002-enhanced-output-formats/contracts/notes-generator.md`
- **Implementation**: `src/mnemofy/notes.py` (REFACTOR)
- **Tests**: `tests/test_notes_enhanced.py`

### Implementation Tasks (11 tasks, ~12 hours)

**T-013: Refactor NoteGenerator**
```python
# src/mnemofy/notes.py

class StructuredNotesGenerator:
    def __init__(self, mode: str = "basic"):
        if mode not in ["basic", "llm"]:
            raise ValueError(f"Unknown mode: {mode}")
        self.mode = mode
    
    def generate(self, segments: list[dict], metadata: dict) -> str:
        # Check: total duration >= 30 seconds
        total_duration = segments[-1]['end'] if segments else 0
        if total_duration < 30:
            raise ValueError(f"Transcript too short ({total_duration}s < 30s)")
        
        # Build markdown with 7 sections
        # Return as string
        pass
```

**T-014–T-020: Implement 7 sections**

Example output:
```markdown
# Meeting Notes: meeting.mp4

**Date**: 2026-02-10  
**Source**: meeting.mp4 (2m 5s)  
**Language**: English (en)  
**Engine**: faster-whisper (base)  
**Generated**: 2026-02-10T14:30:45Z

## Topics

- **[00:00–00:30]** Opening remarks
- **[00:30–01:15]** Q1 planning
- **[01:15–02:05]** Budget discussion

## Decisions

- **[00:45]** Approved Q1 budget: $2.5M
- **[01:20]** Postponed mobile rewrite to Q3

## Action Items

- **[01:10]** John: Complete RFP by Feb 15
- **[01:35]** Sarah: Review architecture docs

## Concrete Mentions

### Names
- John Smith [00:45]
- Sarah Johnson [01:10]

### Numbers & Metrics
- Q1 budget: $2.5M [00:45]
- Timeline: 6-week sprint [01:20]

### URLs & References
- https://github.com/team/roadmap [01:15]

## Risks & Open Questions

### Risks
- Budget allocation may be insufficient

### Open Questions
- When will marketing finalize budget?

## Transcript Files

- **Full Transcript (TXT)**: meeting.transcript.txt
- **Subtitle Format (SRT)**: meeting.transcript.srt
- **Structured Data (JSON)**: meeting.transcript.json
- **Audio (WAV)**: meeting.mnemofy.wav
```

**T-021–T-023: Test (40+ tests)**
```python
# tests/test_notes_enhanced.py

def test_minimum_duration():
    # 30 seconds = boundary (should pass)
    segments = [{'start': 0, 'end': 30, 'text': 'content'}]
    metadata = {...}
    gen = StructuredNotesGenerator()
    notes = gen.generate(segments, metadata)
    assert '## Topics' in notes

def test_too_short():
    # 10 seconds < minimum (should fail)
    segments = [{'start': 0, 'end': 10, 'text': 'short'}]
    gen = StructuredNotesGenerator()
    with pytest.raises(ValueError):
        gen.generate(segments, metadata)

def test_all_sections_present():
    notes = gen.generate(long_segments, metadata)
    required_sections = [
        '# Meeting Notes',
        '## Topics',
        '## Decisions',
        '## Action Items',
        '## Concrete Mentions',
        '## Risks & Open Questions',
        '## Transcript Files'
    ]
    for section in required_sections:
        assert section in notes

def test_metadata_section():
    notes = gen.generate(segments, metadata)
    assert 'Date' in notes
    assert 'Language' in notes
    assert 'Engine' in notes

def test_no_hallucination():
    # Deterministic: same input → same output
    notes1 = gen.generate(segments, metadata)
    notes2 = gen.generate(segments, metadata)
    assert notes1 == notes2

def test_decision_extraction():
    segments_with_decisions = [
        {'start': 0, 'end': 5, 'text': 'We decided to approve the budget'},
        {'start': 5, 'end': 10, 'text': 'The timeline is Q1'}
    ]
    notes = gen.generate(segments_with_decisions, metadata)
    assert 'Decisions' in notes
    assert 'budget' in notes.lower()
```

---

## 4. CLI Integration

### Purpose
Add new flags (--outdir, --lang, --notes) to transcribe command.

### Key Files
- **Contract**: `.specify/specs/002-enhanced-output-formats/contracts/cli-flags.md`
- **Implementation**: `src/mnemofy/cli.py` (UPDATE)
- **Tests**: `tests/test_cli_outputs.py`

### Implementation Tasks (7 tasks, ~6 hours)

**T-024: Add CLI options**
```python
# src/mnemofy/cli.py

@click.command()
@click.argument('input', type=click.Path(exists=True))
@click.option('--outdir', type=click.Path(...), help='Output directory')
@click.option('--lang', type=str, help='Language code (e.g., en, es)')
@click.option('--notes', type=click.Choice(['basic', 'llm']), default='basic')
def transcribe(input: str, outdir: Optional[str], lang: Optional[str], notes: str):
    # Integrate OutputManager, formatters, notes generator
    # Generate all outputs
    # Log to stdout
    pass
```

**T-025–T-030: Integration + testing (15+ tests)**
```python
# tests/test_cli_outputs.py

def test_basic_transcribe():
    result = runner.invoke(transcribe, ['meeting.mp4'])
    assert result.exit_code == 0
    assert 'Generated files' in result.output

def test_outdir_flag():
    result = runner.invoke(transcribe, ['meeting.mp4', '--outdir', '/tmp/out'])
    assert result.exit_code == 0
    assert Path('/tmp/out').exists()

def test_lang_flag():
    result = runner.invoke(transcribe, ['meeting.mp4', '--lang', 'es'])
    assert result.exit_code == 0

def test_notes_flag():
    result = runner.invoke(transcribe, ['meeting.mp4', '--notes', 'basic'])
    assert result.exit_code == 0
    assert 'meeting.notes.md' in result.output

def test_all_flags_combined():
    result = runner.invoke(transcribe, [
        'meeting.mp4',
        '--outdir', '/tmp/out',
        '--lang', 'en',
        '--notes', 'basic'
    ])
    assert result.exit_code == 0

def test_llm_mode_not_available():
    result = runner.invoke(transcribe, ['meeting.mp4', '--notes', 'llm'])
    assert 'LLM mode not available' in result.output or result.exit_code != 0
```

---

## Test Data & Fixtures

Create minimal test fixtures:

```
tests/fixtures/
├── sample_30s.wav           # 30-second audio (generated)
├── sample_10s.wav           # 10-second audio (too short)
├── expected_30s.txt         # Expected TXT output
├── expected_30s.srt         # Expected SRT output
├── expected_30s.json        # Expected JSON output
└── expected_30s.notes.md    # Expected notes.md
```

Generate fixtures programmatically:
```python
# tests/conftest.py

@pytest.fixture(scope="session")
def sample_30s_audio(tmp_path_factory):
    """Generate 30-second test audio."""
    import scipy.io.wavfile as wavfile
    import numpy as np
    
    # 30 seconds of silence at 16kHz
    sample_rate = 16000
    duration_seconds = 30
    samples = np.zeros(sample_rate * duration_seconds, dtype=np.int16)
    
    path = tmp_path_factory.mktemp("fixtures") / "sample_30s.wav"
    wavfile.write(path, sample_rate, samples)
    return path
```

---

## Integration Test Workflow

End-to-end test (simplified):

```python
def test_end_to_end():
    """Full pipeline: input → audio extraction → transcription → all outputs."""
    # Setup
    input_file = Path("tests/fixtures/sample_video.mp4")
    outdir = Path("/tmp/test_output")
    
    # Run transcription
    runner = CliRunner()
    result = runner.invoke(transcribe, [
        str(input_file),
        '--outdir', str(outdir),
        '--lang', 'en',
        '--notes', 'basic'
    ])
    
    # Verify all outputs exist
    assert result.exit_code == 0
    assert (outdir / "sample_video.mnemofy.wav").exists()
    assert (outdir / "sample_video.transcript.txt").exists()
    assert (outdir / "sample_video.transcript.srt").exists()
    assert (outdir / "sample_video.transcript.json").exists()
    assert (outdir / "sample_video.notes.md").exists()
    
    # Verify format correctness
    import srt
    srt_content = (outdir / "sample_video.transcript.srt").read_text()
    subtitles = list(srt.parse(srt_content))
    assert len(subtitles) > 0
    
    # Verify JSON
    json_content = json.loads((outdir / "sample_video.transcript.json").read_text())
    assert json_content['schema_version'] == '1.0'
    
    # Verify notes has all sections
    notes_content = (outdir / "sample_video.notes.md").read_text()
    assert '## Topics' in notes_content
    assert '## Decisions' in notes_content
```

---

## Coverage Goals

```
src/mnemofy/output_manager.py      95%+
src/mnemofy/formatters.py          95%+
src/mnemofy/notes.py               90%+ (refactored)
src/mnemofy/cli.py                 85%+
src/mnemofy/audio.py               85%+ (updated)

Overall: 90%+
```

Run coverage:
```bash
pytest tests/ --cov=src/mnemofy --cov-report=html
# Opens htmlcov/index.html
```

---

## Development Checklist

### Phase 2a: Output Manager + Formatters
- [ ] `src/mnemofy/output_manager.py` (95%+ coverage)
- [ ] `src/mnemofy/formatters.py` (95%+ coverage)
- [ ] `tests/test_output_manager.py` (40+ tests passing)
- [ ] `tests/test_formatters.py` (60+ tests passing)
- [ ] SRT output validates in srt parser
- [ ] JSON output validates with jsonschema

### Phase 2b: Notes Generator
- [ ] `src/mnemofy/notes.py` refactored (90%+ coverage)
- [ ] `tests/test_notes_enhanced.py` (40+ tests passing)
- [ ] 30-second minimum enforced
- [ ] All 7 sections present
- [ ] No Feature 001 test regressions

### Phase 2c: CLI Integration + Testing
- [ ] `src/mnemofy/cli.py` updated (85%+ coverage)
- [ ] `src/mnemofy/audio.py` enhanced (video extraction)
- [ ] `tests/test_cli_outputs.py` (15+ integration tests passing)
- [ ] E2E test passing (video → all outputs)
- [ ] Overall coverage 90%+

### Phase 2d: Documentation + Release
- [ ] README updated with new features
- [ ] CHANGELOG v0.8.0 complete
- [ ] All docstrings written (100%)
- [ ] CLI help text accurate
- [ ] Ready for PyPI upload

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# By module
pytest tests/test_output_manager.py -v
pytest tests/test_formatters.py -v
pytest tests/test_notes_enhanced.py -v
pytest tests/test_cli_outputs.py -v

# With coverage
pytest tests/ --cov=src/mnemofy --cov-report=term-missing

# To 90%+ coverage
pytest tests/ --cov=src/mnemofy --cov-fail-under=90
```

---

## Reference Documentation

- **Research**: [research.md](./research.md)
- **Data Model**: [data-model.md](./data-model.md)
- **OutputManager Contract**: [contracts/output-manager.md](./contracts/output-manager.md)
- **Formatters Contract**: [contracts/formatters.md](./contracts/formatters.md)
- **Notes Generator Contract**: [contracts/notes-generator.md](./contracts/notes-generator.md)
- **CLI Flags Contract**: [contracts/cli-flags.md](./contracts/cli-flags.md)
- **Task Breakdown**: [tasks.md](./tasks.md)
- **Implementation Plan**: [IMPL_PLAN.md](./IMPL_PLAN.md)

---

**Status**: ✅ **PHASE 1 DESIGN COMPLETE**

Ready to proceed to **Phase 2: Implementation** - All contracts, data models, and examples defined.

