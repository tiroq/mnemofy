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

- **Tiny** (1.5 GB): Fastest, suitable for low-RAM systems
- **Base** (2.9 GB): Good balance of speed and accuracy
- **Small** (5 GB): Better accuracy, requires 8GB+ RAM
- **Medium** (11 GB): High accuracy, requires 16GB+ RAM  
- **Large-v3** (20 GB): Best accuracy, requires 32GB+ RAM with GPU

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
# Specify output file
mnemofy transcribe meeting.mp4 -o notes/meeting_summary.md

# Set a custom title for the notes
mnemofy transcribe meeting.mp4 -t "Team Sprint Planning"

# Keep the extracted audio file
mnemofy transcribe video.mkv --keep-audio
```

### Get Help

```bash
# Show all options
mnemofy transcribe --help

# Show version
mnemofy version
```

## Example Output

Given an audio file with meeting content, mnemofy generates structured Markdown like:

```markdown
# Meeting Notes

## Topics Discussed

- **[00:32]** Let's talk about the new feature requirements
- **[05:12]** Now let's discuss the timeline

## Decisions Made

- **[03:45]** We've decided to use Python for the backend
- **[08:20]** The consensus is to launch in Q2

## Action Items

- **[10:15]** John needs to create the API documentation (@john)
- **[12:30]** Sarah will follow up with the design team (@sarah)

## Mentions

- @john: 10:15
- @sarah: 12:30

## Full Transcript

**[00:00]** Welcome everyone to today's meeting...
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
   - **macOS (Metal)**: Should just work on Apple Silicon/Intel
   - **AMD (ROCm)**: Check `rocm` installation

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

## License

MIT License - see LICENSE file for details.
