# mnemofy

![mnemofy Logo](https://raw.githubusercontent.com/tiroq/mnemofy/main/assets/mnemofy.png)

**mnemofy** extracts audio from media files, transcribes speech using faster-whisper, and produces structured meeting notes with topics, decisions, action items, and mentions with timestamps.

## Features

- 🎵 **Audio Extraction**: Automatically extracts audio from video files using ffmpeg
- 🎤 **Speech Transcription**: Fast local transcription using faster-whisper (no API keys needed)
- 📝 **Structured Notes**: Generates Markdown notes with:
  - Topics discussed with timestamps
  - Decisions made with timestamps
  - Action items with timestamps and @mentions
  - Full transcript with timestamps
- 🎯 **Supported Formats**: aac, mp3, wav, mkv, mp4
- 🚀 **Production Ready**: Clean modular architecture, type hints, error handling

## Installation

### Prerequisites

1. **Python 3.9+** is required
2. **ffmpeg** must be installed:
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

### Install mnemofy

```bash
# Clone the repository
git clone https://github.com/tiroq/mnemofy.git
cd mnemofy

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Usage

### Basic Usage

Transcribe an audio or video file:

```bash
mnemofy transcribe meeting.mp4
```

This will create `meeting_notes.md` in the same directory.

### Automatic Model Selection

mnemofy **automatically detects your system resources** (CPU, RAM, GPU) and selects the best Whisper model that fits in your available memory:

- **Tiny** (1.0 GB): Fastest, suitable for low-RAM systems
- **Base** (1.5 GB): Good balance of speed and accuracy
- **Small** (2.5 GB): Better accuracy, requires 8GB+ RAM
- **Medium** (5.0 GB): High accuracy, requires 16GB+ RAM  
- **Large-v3** (10.0 GB): Best accuracy, requires 32GB+ RAM with GPU

**Default behavior** (recommended):
```bash
mnemofy transcribe meeting.mp4
# ✓ Detects your system (RAM, GPU, CPU)
# ✓ Shows interactive menu (if in terminal)
# ✓ You select desired model with ↑↓ arrow keys
# ✓ Falls back to auto-selection on headless systems
```

**Skip auto-detection** with explicit model:
```bash
mnemofy transcribe meeting.mp4 --model tiny
# ✓ Uses tiny model directly (no detection/menu)
```

**Headless mode** (CI/automated environments):
```bash
mnemofy transcribe meeting.mp4 --auto
# ✓ Detects resources
# ✓ Auto-selects best model
# ✓ No interactive menu (suitable for cron, CI/CD)
```

**CPU-only mode** (disable GPU):
```bash
mnemofy transcribe meeting.mp4 --no-gpu
# ✓ Forces CPU-based transcription
# ✓ Useful if GPU causes issues
```

**View available models**:
```bash
mnemofy transcribe --list-models
# Shows model comparison table with your system specs
```

### Advanced Options

```bash
# Specify output directory for all files
mnemofy transcribe meeting.mp4 --outdir outputs/

# Specify output file for notes only
mnemofy transcribe meeting.mp4 -o notes/meeting_summary.md

# Set a custom title for the notes
mnemofy transcribe meeting.mp4 -t "Team Sprint Planning"

# Specify transcription language (ISO 639-1 code)
mnemofy transcribe meeting.mp4 --lang es  # Spanish
mnemofy transcribe meeting.mp4 --lang fr  # French

# Choose notes generation mode
mnemofy transcribe meeting.mp4 --notes basic  # Deterministic extraction (default)
# mnemofy transcribe meeting.mp4 --notes llm  # AI-enhanced (coming in v0.9.0)

# Keep the extracted audio file
mnemofy transcribe video.mkv --keep-audio
```

## Output Files

mnemofy generates **4 output files** from each transcription:

```
meeting.mp4  (input)
├── meeting.transcript.txt   # Timestamped plain text
├── meeting.transcript.srt   # SubRip subtitle format  
├── meeting.transcript.json  # Structured JSON with metadata
└── meeting.notes.md         # Structured meeting notes
```

### File Descriptions

1. **`.transcript.txt`** - Timestamped text transcript
   - Format: `[HH:MM:SS–HH:MM:SS] text`
   - Best for: Reading, searching, printing
   
2. **`.transcript.srt`** - SubRip subtitle file
   - Format: Standard SRT (sequence number, timing, text)
   - Best for: Video subtitles in VLC, subtitle editors
   
3. **`.transcript.json`** - Structured JSON
   - Contains: Metadata (engine, model, language) + segments
   - Best for: Programmatic access, data analysis
   
4. **`.notes.md`** - Structured meeting notes
   - Sections: Metadata, Topics, Decisions, Actions, Mentions, Risks, File Links
   - Best for: Quick review, sharing with team

### Output Location

By default, files are created in the **same directory as the input file**:

```bash
mnemofy transcribe ~/Videos/meeting.mp4
# Creates: ~/Videos/meeting.transcript.{txt,srt,json}
#          ~/Videos/meeting.notes.md
```

Use `--outdir` to specify a different location:

```bash
mnemofy transcribe meeting.mp4 --outdir ./transcripts/
# Creates: ./transcripts/meeting.transcript.{txt,srt,json}
#          ./transcripts/meeting.notes.md
```

### Get Help

```bash
# Show all options
mnemofy transcribe --help

# Show version
mnemofy version
```

## Example Output

Given an audio file with meeting content, mnemofy generates structured Markdown (`.notes.md`) like:

```markdown
# Meeting Notes: meeting

**Date**: 2026-02-10
**Source**: meeting.mp4 (45m 30s)
**Language**: en
**Engine**: faster-whisper (base)
**Generated**: 2026-02-10T15:30:00Z

## Topics

- **[05:00–10:00]** Discussion about project roadmap and milestones
- **[15:30–20:15]** Review of last sprint deliverables
- **[30:00–35:45]** Planning for upcoming feature releases

## Decisions

- **[08:30]** We decided to use Python for the backend
- **[18:45]** Agreed to launch the MVP in Q2
- **[32:10]** Approved budget increase for infrastructure

## Action Items

- **[10:15]** John needs to create the API documentation
- **[22:30]** Sarah will follow up with the design team
- **[40:00]** Team should review security audit by Friday

## Concrete Mentions

### Names
- John (10:15, 12:30)
- Sarah (22:30, 25:00)

### Numbers  
- Q2 (18:45)
- $50,000 (32:10)

### URLs
- https://github.com/project/repo (15:00)

## Risks & Open Questions

### Open Questions
- How should we handle database migrations? **[25:30]**
- What's the timeline for QA testing? **[38:00]**

### Risks
- Potential delay due to third-party API integration **[28:15]**

## Transcript Files

- Full Transcript (TXT): meeting.transcript.txt
- Subtitle Format (SRT): meeting.transcript.srt 
- Structured Data (JSON): meeting.transcript.json
- Audio (WAV): meeting.mnemofy.wav
```

## Architecture

mnemofy follows a clean, modular architecture:

```
mnemofy/
├── src/mnemofy/
│   ├── __init__.py       # Package initialization
│   ├── audio.py          # Audio extraction using ffmpeg
│   ├── transcriber.py    # Speech transcription using Whisper
│   ├── notes.py          # Structured note generation
│   └── cli.py            # Command-line interface with Typer
├── tests/                # Test suite
├── pyproject.toml        # Modern Python packaging (PEP 621)
└── README.md
```

## Development

### Running Tests

```bash
pytest
```

### Linting and Type Checking

```bash
# Run ruff for linting
ruff check src/

# Run mypy for type checking
mypy src/
```

## Whisper Models

mnemofy supports all Whisper model sizes:

| Model  | Parameters | Speed      | Accuracy |
|--------|-----------|------------|----------|
| tiny   | 39M       | Fastest    | Good     |
| base   | 74M       | Fast       | Better   |
| small  | 244M      | Medium     | Great    |
| medium | 769M      | Slow       | Excellent|
| large  | 1550M     | Slowest    | Best     |

The default `base` model offers a good balance of speed and accuracy. Use `tiny` for quick tests or `medium`/`large` for maximum accuracy.

## Requirements

- Python 3.9-3.13 (Python 3.14+ not yet supported by dependencies)
- ffmpeg
- Dependencies (automatically installed):
  - typer
  - faster-whisper
  - rich
  - pydantic

## Troubleshooting

### Model Selection Issues

#### "No Whisper model fits in available RAM"

This means even the smallest model (tiny, 1.5 GB) requires more memory than available.

**Solutions**:
1. Close other applications to free memory
2. Use explicit tiny model: `mnemofy transcribe file.mp4 --model tiny`
3. Process shorter audio files
4. Upgrade system RAM
5. Use a machine with more RAM (cloud VM option)

#### CPU/GPU Not Detected

If model selection falls back to "base" when you expect GPU acceleration:

1. Check GPU availability:
   ```bash
   mnemofy transcribe --list-models
   # Look for "VRAM" row - should show your GPU memory if available
   ```

2. Verify GPU drivers (NVIDIA/Metal/ROCm) are installed:
   - **NVIDIA**: `nvidia-smi` should work
   - **macOS (Metal)**: Currently supported on macOS with Apple Silicon (ARM64); Intel Macs will fall back to CPU
   - **AMD (ROCm)**: Not yet implemented (planned for future release)

3. Force CPU mode if GPU causes issues:
   ```bash
   mnemofy transcribe file.mp4 --no-gpu
   ```

#### Interactive Menu Not Showing

If you expect the interactive menu but it skips to auto-selection:

- Menu requires a terminal (TTY), not suitable for pipes/redirects
- Use `--auto` explicitly for headless environments
- In CI/cron: model selection works automatically with `--auto`

### OpenMP Library Conflict (macOS)

If you encounter an error about `libiomp5.dylib already initialized`, set this environment variable:

```bash
export KMP_DUPLICATE_LIB_OK=TRUE
mnemofy transcribe your_file.mp4
```

Or run it inline:

```bash
KMP_DUPLICATE_LIB_OK=TRUE mnemofy transcribe your_file.mp4
```

This is a known issue with multiple OpenMP runtimes being linked (common with ctranslate2/faster-whisper).

### Audio Extraction Issues

#### ffmpeg Not Found

If you see `ffmpeg: command not found`:

**Solution**: Install ffmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg
```

Verify installation:
```bash
ffmpeg -version
```

#### Unsupported Video Codec

If audio extraction fails with codec errors:

1. Check if the video file is corrupted:
   ```bash
   ffplay your_video.mp4  # Should play without errors
   ```

2. Try converting to a standard format first:
   ```bash
   ffmpeg -i input.mkv -c:v libx264 -c:a aac output.mp4
   mnemofy transcribe output.mp4
   ```

3. Check container format is supported (mp4, mkv, mov, avi, webm)

#### Extracted Audio Quality Issues

If transcription accuracy is poor, the audio extraction might have issues:

- Verify audio channel: mnemofy extracts the first audio track
- For multi-audio files, extract specific track manually:
  ```bash
  ffmpeg -i video.mkv -map 0:a:1 audio.wav  # Extract 2nd audio track
  mnemofy transcribe audio.wav
  ```

## License

MIT License - see LICENSE file for details.
