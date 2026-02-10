# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2026-02-10

### Added

- **Multiple Output Formats**: Generate 4 files from each transcription
  - `.transcript.txt`: Timestamped plain text format `[HH:MM:SS–HH:MM:SS] text`
  - `.transcript.srt`: SubRip subtitle format for video players
  - `.transcript.json`: Structured JSON with metadata and segments
  - `.notes.md`: Enhanced structured meeting notes (7 sections)

- **Enhanced Meeting Notes** with 7 comprehensive sections:
  - **Metadata**: Date, source, language, engine, model, duration, timestamp
  - **Topics**: Time-bucketed topic extraction with time ranges
  - **Decisions**: Keyword-based decision identification with timestamps
  - **Action Items**: Action extraction with timestamps
  - **Concrete Mentions**: Names, numbers, URLs, dates with timestamps
  - **Risks & Open Questions**: Risk keywords and questions
  - **Transcript Files**: Links to all generated output files

- **New CLI Flags**:
  - `--outdir <path>`: Specify output directory for all files (default: same as input)
  - `--lang <code>`: Specify transcription language (ISO 639-1: en, es, fr, etc.)
  - `--notes <mode>`: Notes generation mode (`basic` or `llm` - LLM mode coming in v0.9.0)

- **Output Manager**: Centralized path management for all output files
  - Consistent naming: `<basename>.transcript.{txt,srt,json}`, `<basename>.notes.md`
  - Directory creation if `--outdir` doesn't exist
  - Validation for write permissions

### Changed

- **Notes Generation**: Refactored to `StructuredNotesGenerator` with mode support
  - `basic` mode: Deterministic, keyword-based extraction (current default)
  - `llm` mode: AI-enhanced extraction (stubbed for v0.9.0)
  - Minimum transcript duration: 30 seconds required for notes
  - Timestamps in notes use MM:SS format for readability

- **Transcript Format Changes**:
  - TXT format uses HH:MM:SS timestamps (includes hours)
  - SRT format follows SubRip spec with millisecond precision
  - JSON includes schema version "1.0" for future compatibility

- **CLI Output**: Enhanced console output showing all generated files with paths

### Fixed

- Deprecation warnings: Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)`
- Error handling for empty segments and invalid metadata

### Technical Details

- **Architecture**:
  - `output_manager.py`: Path generation and directory management
  - `formatters.py`: TXT/SRT/JSON export with format validation
  - `notes.py`: Enhanced extraction with 7-section structure
  - `cli.py`: Integration of all formatters and file output

- **Testing**:
  - 170+ total tests (48 OutputManager, 67 Formatters, 36 Notes, 19 Integration)
  - 100% coverage on OutputManager and Formatters
  - 91% coverage on Notes module
  - End-to-end integration tests for complete pipeline
  - Edge case testing for long transcripts (>1hr), unicode, special characters

- **File Naming Conventions**:
  - Audio: `<basename>.mnemofy.wav`
  - Transcripts: `<basename>.transcript.{txt,srt,json}`
  - Notes: `<basename>.notes.md`

### Dependencies

- No new dependencies required
- All features use existing dependencies

### Upgrading

To upgrade from v0.7.0 to v0.8.0:

```bash
pip install --upgrade mnemofy
```

**Breaking Changes**: None. New features are opt-in via flags. Default behavior unchanged.

**What's New in Your Workflow**:
- Automatically get 4 output files instead of 1
- Use `--outdir` to organize outputs in a specific directory
- Specify `--lang` for non-English audio
- Enhanced notes with more sections (Topics, Decisions, Actions, Risks, Mentions)

### Known Limitations

- LLM-enhanced notes mode (`--notes llm`) is stubbed (coming in v0.9.0)
- SRT validation tested manually in VLC/Subtitle Edit (automated validation pending)
- Notes require minimum 30 seconds of transcript (raises ValueError if shorter)

---

## [0.7.0] - 2026-02-10

### Added

- **Adaptive ASR Model Selection**: Intelligent model selection based on system resources
  - Automatic CPU/RAM/GPU detection (CUDA, Metal)
  - Resource-aware model recommendation with 85% RAM safety margin
  - Interactive model selection menu in terminal environments
  - Headless mode for CI/automated deployments
  
- **New CLI Flags**:
  - `--auto`: Skip interactive menu, auto-select best model (headless mode)
  - `--no-gpu`: Force CPU-only transcription
  - `--list-models`: Display model comparison table with system specs
  
- **Interactive Terminal Menu**:
  - Arrow key navigation for model selection
  - Real-time resource compatibility feedback
  - Performance impact warnings for risky selections
  - Graceful fallback for non-interactive environments

- **Model Comparison Table**: `--list-models` displays models with:
  - Speed/quality ratings
  - RAM and VRAM requirements
  - Compatibility status (✓ Compatible, ⚠ Risky, ✗ Incompatible)
  
- **Comprehensive Testing**:
  - 115+ unit tests covering all resource detection paths
  - GPU detection tests for CUDA and Metal
  - Model filtering and recommendation algorithm tests
  - Interactive menu navigation and rendering tests
  - Integration tests for all CLI flag combinations

### Changed

- `--model` flag behavior:
  - Now optional (was required with default "base")
  - If provided, skips resource detection (explicit override)
  - If omitted, triggers auto-detection with interactive menu (in TTY)
  
- Updated `README.md` with extensive model selection documentation
- Added troubleshooting section for model selection issues
- Improved error messages for resource constraints

### Dependencies

- **Added**: `psutil>=5.9.0` for system resource detection
- **Added**: `readchar>=4.1.0` for keyboard input in interactive menu

### Technical Details

- **GPU Support**:
  - CUDA: Uses `nvidia-smi` for VRAM detection
  - Metal (macOS): Unified memory model, no separate VRAM tracking
  - ROCm (AMD): Not yet implemented (planned for future release)
  
- **Memory Requirements**:
  - Conservative estimates include model weights + inference overhead
  - 85% RAM safety margin to prevent OOM
  - Fallback model: "base" (1.5 GB) for undetected systems
  
- **Architecture**:
  - `resources.py`: Cross-platform system detection
  - `model_selector.py`: Filtering, recommendation, comparison table
  - `tui/model_menu.py`: Interactive menu with keyboard navigation
  - `cli.py`: Orchestration with proper precedence logic

## [0.6.2] - Previous Release

- Initial structured notes generation
- Transcription with faster-whisper
- Audio extraction from video files
- Topic extraction, decision tracking, action items with timestamps

---

**For upgrade instructions**, see [Upgrading](#upgrading).

### Upgrading

To upgrade from v0.6.2 to v0.7.0:

```bash
pip install --upgrade mnemofy
```

New CLI flags are optional and backwards compatible. Existing scripts will automatically benefit from adaptive model selection.

### Known Limitations

- ROCm VRAM detection is basic (uses system utilities)
- Metal GPU unified memory not separately reported
- Interactive menu requires terminal TTY (not available in pipes/redirects)
- Complex audio (high background noise) still benefits from larger models despite resource constraints
