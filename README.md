# mnemofy

![mnemofy Logo](https://raw.githubusercontent.com/tiroq/mnemofy/main/assets/mnemofy.png)

**mnemofy** extracts audio from media files, transcribes speech using OpenAI Whisper, and produces structured meeting notes with topics, decisions, action items, and mentions with timestamps.

## Features

- 🎵 **Audio Extraction**: Automatically extracts audio from video files using ffmpeg
- 🎤 **Speech Transcription**: Fast local transcription using Faster Whisper (no API keys needed)
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

### Advanced Options

```bash
# Specify output file
mnemofy transcribe meeting.mp4 -o notes/meeting_summary.md

# Use a different Whisper model (tiny, base, small, medium, large)
# Larger models are more accurate but slower
mnemofy transcribe meeting.mp4 -m small

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

mnemofy uses Faster Whisper for efficient local transcription. All model sizes are supported:

| Model  | Parameters | Speed      | Accuracy | Memory  |
|--------|-----------|------------|----------|---------|  
| tiny   | 39M       | Fastest    | Good     | ~1 GB   |
| base   | 74M       | Fast       | Better   | ~1 GB   |
| small  | 244M      | Medium     | Great    | ~2 GB   |
| medium | 769M      | Slow       | Excellent| ~5 GB   |
| large  | 1550M     | Slowest    | Best     | ~10 GB  |

The default `base` model offers a good balance of speed and accuracy. Use `tiny` for quick tests or `medium`/`large` for maximum accuracy.

## Requirements

- Python 3.9+
- ffmpeg
- Dependencies (automatically installed):
  - typer
  - faster-whisper
  - rich
  - pydantic

## License

MIT License - see LICENSE file for details.
