# API Contract: CLI Flags

**Feature**: 002-enhanced-output-formats  
**Phase**: 1 (Design - API Contracts)  
**Module**: `src/mnemofy/cli.py` (UPDATE)

---

## New CLI Flags

Three new optional flags for the `transcribe` command.

### Overview

```bash
# Existing usage (still works, backward compatible)
mnemofy transcribe input.mp4
mnemofy transcribe input.mp4 --lang es

# New feature: output directory control
mnemofy transcribe input.mp4 --outdir /transcripts

# New feature: structured notes generation
mnemofy transcribe input.mp4 --notes basic

# New feature: language specification
mnemofy transcribe input.mp4 --lang en

# Combined: all new flags
mnemofy transcribe input.mp4 --outdir /transcripts --lang en --notes basic
```

---

## Flag: --outdir

**Name**: `--outdir`  
**Type**: Path (directory)  
**Default**: None (input file's directory)  
**Short Option**: None (click recommendation for new major features)  
**Required**: No  
**Repeatable**: No  
**Values**: Valid directory path (relative or absolute)

### Definition

```python
import click
from pathlib import Path

@click.option(
    '--outdir',
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True
    ),
    default=None,
    help='Output directory for transcript and notes files (default: same as input file)'
)
def transcribe(outdir: Optional[str]):
    """Transcribe audio/video file."""
    if outdir:
        outdir = Path(outdir).resolve()
    ...
```

### Behavior

- **Default behavior** (no flag): Output files saved in same directory as input
  ```bash
  $ mnemofy transcribe /home/user/videos/meeting.mp4
  # Creates:
  # /home/user/videos/meeting.mnemofy.wav
  # /home/user/videos/meeting.transcript.txt
  # /home/user/videos/meeting.transcript.srt
  # /home/user/videos/meeting.transcript.json
  # /home/user/videos/meeting.notes.md
  ```

- **With --outdir flag**: All outputs go to specified directory
  ```bash
  $ mnemofy transcribe /home/user/videos/meeting.mp4 --outdir /transcripts
  # Creates:
  # /transcripts/meeting.mnemofy.wav
  # /transcripts/meeting.transcript.txt
  # /transcripts/meeting.transcript.srt
  # /transcripts/meeting.transcript.json
  # /transcripts/meeting.notes.md
  ```

- **Relative paths**: Resolved relative to current working directory
  ```bash
  $ cd /home/user
  $ mnemofy transcribe videos/meeting.mp4 --outdir output
  # Creates files in: /home/user/output/
  ```

- **Home directory expansion**: ~ works
  ```bash
  $ mnemofy transcribe input.mp4 --outdir ~/transcripts
  # Expands to: /home/username/transcripts
  ```

### Validation

✅ **Path Validation**:
- [ ] Directory must be writable (or creatable)
- [ ] Directory created automatically if it doesn't exist
- [ ] Reject if path is a file (not directory)
- [ ] Reject if no write permission (after creation attempt)

✅ **Error Messages**:
```
Error: --outdir must be a directory
Error: --outdir is not writable
Error: Cannot create --outdir (permission denied)
```

### Examples

```bash
# Basic usage
mnemofy transcribe meeting.mp4 --outdir /tmp/transcripts

# Relative path
mnemofy transcribe meeting.mp4 --outdir ./output

# Home directory
mnemofy transcribe meeting.mp4 --outdir ~/transcripts

# Absolute path
mnemofy transcribe meeting.mp4 --outdir /mnt/shared/transcripts

# With other flags
mnemofy transcribe meeting.mp4 --outdir /out --lang en --notes basic
```

---

## Flag: --lang

**Name**: `--lang`  
**Type**: String (language code)  
**Default**: None (auto-detect)  
**Short Option**: None  
**Required**: No  
**Repeatable**: No  
**Values**: ISO 639-1 language codes (e.g., "en", "es", "fr", "de", "zh")

### Definition

```python
@click.option(
    '--lang',
    type=str,
    default=None,
    help='Language code for transcription (e.g., en, es, fr). Auto-detect if not specified.'
)
def transcribe(lang: Optional[str]):
    """Transcribe audio/video file."""
    if lang:
        if lang not in SUPPORTED_LANGUAGES:
            raise click.BadParameter(f"Language '{lang}' not supported")
    ...
```

### Behavior

- **Default behavior** (no flag): Language auto-detection
  ```bash
  $ mnemofy transcribe meeting.mp4
  # faster-whisper auto-detects language from audio
  # Note in metadata: "language_detected": true
  ```

- **With --lang flag**: Use specified language
  ```bash
  $ mnemofy transcribe meeting_spanish.mp3 --lang es
  # Uses Spanish (es) for transcription
  # Faster and more accurate for known language
  # Note in metadata: "language": "es", "language_detected": false
  ```

### Supported Languages

ISO 639-1 codes:
```
af, am, ar, as, az, be, bg, bn, bo, br, bs, ca, cs, cy, da, de, el, en, es, 
et, fa, fi, fo, fr, gl, gu, ha, haw, he, hi, hr, ht, hu, hy, id, is, it, ja, 
jv, ka, kk, km, kn, ko, lao, la, lb, ln, lo, lt, lv, mk, ml, mn, mr, ms, mt, 
my, ne, nl, nn, no, oc, pa, pl, ps, pt, ro, ru, sa, sd, si, sk, sl, sm, sn, 
so, sq, sr, su, sv, sw, ta, te, tg, th, tl, tr, tt, tw, uk, ur, uz, vi, yi, 
yo, zh
```

### Validation

✅ **Language Validation**:
- [ ] Check language code is valid ISO 639-1
- [ ] Case-insensitive (convert "EN" → "en")
- [ ] Reject if language not supported
- [ ] Show available languages on error

✅ **Error Messages**:
```
Error: Language 'xx' not supported
Error: Use --lang with valid ISO 639-1 code (e.g., en, es, fr)
Available languages: af, am, ar, ... (list top 10)
```

### Examples

```bash
# English transcription
mnemofy transcribe meeting.mp4 --lang en

# Spanish
mnemofy transcribe reunion.mp4 --lang es

# French
mnemofy transcribe reunion.mp3 --lang fr

# With other flags
mnemofy transcribe meeting.mp4 --lang en --outdir /out --notes basic
```

---

## Flag: --notes

**Name**: `--notes`  
**Type**: Choice ("basic" or "llm")  
**Default**: "basic"  
**Short Option**: None  
**Required**: No  
**Repeatable**: No  
**Values**: "basic" (deterministic) or "llm" (LLM-enhanced, future)

### Definition

```python
@click.option(
    '--notes',
    type=click.Choice(['basic', 'llm'], case_sensitive=False),
    default='basic',
    help='Notes generation mode (basic=deterministic, llm=future). Default: basic'
)
def transcribe(notes: str):
    """Transcribe audio/video file."""
    notes_mode = notes.lower()  # Handle case variations
    ...
```

### Behavior

- **Default behavior** (no flag or --notes basic): Deterministic notes
  ```bash
  $ mnemofy transcribe meeting.mp4
  $ # OR
  $ mnemofy transcribe meeting.mp4 --notes basic
  
  # Generates meeting.notes.md with:
  # - Topics (extracted from time segments)
  # - Decisions (keyword matching for "decided", "agreed")
  # - Action items (keyword matching for "will", "going to")
  # - Concrete mentions (names, numbers, URLs)
  # - Risks & Questions (conditional statements, questions)
  # - Transcript links (references to all output files)
  # - NO hallucination or inference beyond transcript
  ```

- **With --notes llm**: LLM-enhanced notes (Future)
  ```bash
  $ mnemofy transcribe meeting.mp4 --notes llm
  # ERROR: LLM mode not yet implemented (v0.8.0)
  # Error: LLM mode is not available in v0.8.0 (coming in v0.9.0)
  ```

### Mode Specifications

#### basic Mode (Enabled in v0.8.0)
- ✅ Deterministic (100% reproducible output)
- ✅ No external dependencies
- ✅ Conservative extraction (no speculation)
- ✅ All items cite timestamps
- ✅ Works on CPU
- ✅ Fast (< 30 seconds for 4-hour audio)

**Extraction Rules**:
- Topics: Time-bucket analysis + keyword detection
- Decisions: Keyword matching ("decided", "agreed", "approved", "will")
- Action items: Name detection + task extraction
- Concrete mentions: Regex for names, numbers, URLs
- Risks: Conditional keywords ("might", "could", "risk")
- Questions: Sentences ending with "?"

#### llm Mode (Stub in v0.8.0, Future in v0.9.0)
```python
if notes_mode == 'llm':
    print("Warning: LLM mode not available in v0.8.0")
    print("         Coming in v0.9.0 release")
    raise click.BadParameter("LLM mode not yet implemented")
```

### Validation

✅ **Mode Validation**:
- [ ] Accept "basic" (default)
- [ ] Accept "llm" but raise NotImplementedError
- [ ] Case-insensitive ("BASIC", "Basic" → "basic")
- [ ] Reject unknown modes

✅ **Error Messages**:
```
Error: Invalid notes mode 'xxx'
Error: LLM mode not available in v0.8.0 (coming in v0.9.0)
Error: Use --notes basic (deterministic) or --notes llm (future)
```

### Transcript Length Check

- **30-second minimum**: Notes only generated if transcript ≥ 30 seconds
  ```bash
  $ mnemofy transcribe 5second_clip.mp4 --notes basic
  # Output: Skipping notes generation (transcript 5s < 30s minimum)
  # Still generates: audio, TXT, SRT, JSON transcripts
  ```

- **Exactly 30 seconds**: Boundary included (generates notes)
  ```bash
  $ mnemofy transcribe 30second_clip.mp4 --notes basic
  # Generates notes.md
  ```

### Examples

```bash
# Default: basic mode
mnemofy transcribe meeting.mp4

# Explicit basic mode
mnemofy transcribe meeting.mp4 --notes basic

# Request LLM (will fail with helpful error in v0.8.0)
mnemofy transcribe meeting.mp4 --notes llm
# Error: LLM mode not available in v0.8.0

# Combined with other flags
mnemofy transcribe meeting.mp4 --notes basic --outdir /out --lang en
```

---

## Modified transcribe Command Signature

```python
@click.command()
@click.argument('input', type=click.Path(exists=True))
@click.option(
    '--outdir',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default=None,
    help='Output directory (default: input directory)'
)
@click.option(
    '--lang',
    type=str,
    default=None,
    help='Language code (en, es, fr, etc). Auto-detect if not specified'
)
@click.option(
    '--notes',
    type=click.Choice(['basic', 'llm'], case_sensitive=False),
    default='basic',
    help='Notes mode: basic (deterministic) or llm (future). Default: basic'
)
def transcribe(
    input: str,
    outdir: Optional[str],
    lang: Optional[str],
    notes: str
) -> None:
    """
    Transcribe audio or video file to multiple formats.
    
    INPUT: Path to audio (WAV, MP3, FLAC) or video (MP4, MKV, MOV) file
    
    Examples:
        mnemofy transcribe meeting.mp4
        mnemofy transcribe audio.mp3 --lang es
        mnemofy transcribe video.mkv --outdir /transcripts --notes basic
    """
    ...
```

---

## Backward Compatibility

✅ **All new flags optional**:
- Existing scripts continue to work
- Default behavior unchanged (output in input directory)
- No breaking changes to CLI

```bash
# Old usage (v0.7.0) - STILL WORKS in v0.8.0
mnemofy transcribe meeting.mp4
mnemofy transcribe audio.mp3 --lang en

# New usage (v0.8.0)
mnemofy transcribe meeting.mp4 --outdir /transcripts --notes basic
```

---

## User Messaging

### Success Message

```
✓ Transcription complete

Generated files:
  - Audio: /transcripts/meeting.mnemofy.wav (45 MB)
  - Transcript (TXT): /transcripts/meeting.transcript.txt (125 KB)
  - Transcript (SRT): /transcripts/meeting.transcript.srt (89 KB)
  - Transcript (JSON): /transcripts/meeting.transcript.json (156 KB)
  - Notes: /transcripts/meeting.notes.md (12 KB)

Total: 225 MB in 45 seconds
```

### Partial Success (One formatter failed)

```
⚠ Transcription complete (with warnings)

Generated files:
  - Audio: /transcripts/meeting.mnemofy.wav
  - Transcript (TXT): /transcripts/meeting.transcript.txt
  - Transcript (SRT): /transcripts/meeting.transcript.srt
  - Transcript (JSON): /transcripts/meeting.transcript.json
  - Notes: /transcripts/meeting.notes.md

Warnings:
  - SRT generation failed (timing precision issue) - output converted to TXT only

See details above (marked with ⚠)
```

### Skipped Notes (< 30 seconds)

```
✓ Transcription complete

Generated files:
  - Audio: /transcripts/clip.mnemofy.wav
  - Transcript (TXT): /transcripts/clip.transcript.txt
  - Transcript (SRT): /transcripts/clip.transcript.srt
  - Transcript (JSON): /transcripts/clip.transcript.json

Notes skipped: Transcript too short (12s < 30s minimum)
```

---

**Status**: ✅ **CONTRACT DEFINED**

Implementation ready: Update `src/mnemofy/cli.py`

