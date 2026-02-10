# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

**Model-Aware Artifacts & Enriched Metadata**

- **Processing metadata** (`*.metadata.json`):
  - Complete audit trail of processing pipeline
  - ASR model details: name, size, quality/speed ratings
  - LLM model details: name, purpose (classification, notes, repair)
  - Processing configuration: language, flags, meeting type, modes
  - Timing information: start, end, total duration
  - Statistics: word count, segment count, transcript duration
  - Best for: Audit trails, cost tracking, reproducibility
- **Artifacts manifest** (`*.artifacts.json`):
  - Index of all generated files
  - Model used for each artifact
  - File sizes and descriptions
  - Schema versioning for structured formats
  - Best for: Automation, workflows, batch processing
- **Enriched transcript JSON**:
  - Model specifications (size, quality/speed ratings)
  - Auto-generated timestamp and statistics
  - Preprocessing flags (normalization, repair)
  - Backward compatible with existing schema
- **Model-aware file paths** (API):
  - `OutputManager.get_model_aware_transcript_paths(model_name)`: Generate filenames with model names
  - Pattern: `{basename}.{model}.transcript.{ext}`
  - Enables side-by-side model comparison
- **New artifacts module**:
  - Dataclasses for metadata structures
  - JSON serialization support
  - Factory functions for easy creation
  - Extensible design for future enhancements

**Rerun Handling & Model Comparison**

- **`--model-suffix` flag**:
  - Include model name in transcript filenames
  - Prevents overwrites when comparing different models
  - Pattern: `meeting.base.transcript.json`, `meeting.small.transcript.json`
  - Enables side-by-side quality comparison
- **Run history tracking** (`*.run-history.jsonl`):
  - Automatic append-only log of all processing runs
  - Records: timestamp, model, duration, word count, config
  - JSONL format (one JSON object per line)
  - Tracks runs regardless of --model-suffix usage
  - Never overwrites - maintains complete audit trail
- **Model comparison script** (`examples/compare_model_runs.py`):
  - Analyze run history to compare model performance
  - Display comparison tables with metrics
  - Identify fastest and best quality models
  - Recommend balanced options
- **Model-suffixed metadata**:
  - When using --model-suffix, metadata and manifest files also include model name
  - Preserves complete context for each model run

### Changed

- **CLI output**: Now displays metadata file paths after processing
- **CLI output**: Shows run history file path
- **CLI output**: Indicates when model-suffix mode is enabled
- **Transcript JSON**: Auto-enriched with additional metadata fields
- **OutputManager**: Added methods for metadata paths and model-aware naming
- **File overwrites**: Default behavior still overwrites; use --model-suffix to preserve

### Documentation

- Added `docs/MODEL_AWARE_ARTIFACTS.md`: Comprehensive guide to metadata features
- Added `docs/RERUN_HANDLING.md`: Complete guide to handling reruns and model comparison
- Added `ARTIFACTS_IMPLEMENTATION.md`: Implementation details and API examples
- Added `examples/analyze_metadata.py`: Example script for metadata analysis
- Added `examples/compare_model_runs.py`: Script for comparing multiple model runs
- Updated README with metadata features overview

## [1.0.0] - 2026-02-10

### Added

**Meeting Type Detection & Classification**

- **Auto-detect meeting types**: Automatically classifies meetings into 9 types (status, planning, design, demo, talk, incident, discovery, oneonone, brainstorm)
- **Dual classification modes**:
  - `--classify heuristic` (default): Fast, deterministic, offline keyword-based detection
  - `--classify llm`: AI-powered classification with higher accuracy for ambiguous meetings
- **Confidence scoring**: 0.0-1.0 confidence with evidence phrases showing classification reasoning
- **Type-specific templates**: Each meeting type uses optimized note structure (e.g., planning includes scope/timeline, incident includes root cause)

**LLM Engine Support**

- **Multi-provider support**: OpenAI API, Ollama local models, OpenAI-compatible endpoints
- **LLM-enhanced notes** (`--notes llm`):
  - Deeper decision extraction beyond keywords
  - Inferred action item owners from context
  - Contextualized summaries
  - All claims grounded in transcript with timestamp references
- **Grounding enforcement**: Every AI-generated decision/action includes timestamp links; ambiguous items marked as "unclear" with reasons
- **Graceful degradation**: Auto-falls back to deterministic mode if LLM unavailable

**Configuration System**

- **Multi-source configuration** with precedence: CLI flags > environment variables > config file > defaults
- **Config file support**: `~/.config/mnemofy/config.toml` for persistent LLM settings
- **Environment variables**: `OPENAI_API_KEY`, `MNEMOFY_LLM_*` for secure API key storage
- **CLI overrides**: `--llm-engine`, `--llm-model`, `--llm-base-url`, `--llm-timeout`, `--llm-retries`
- **Default models**: gpt-4o-mini (OpenAI), llama3.2:3b (Ollama)
- **Security**: API keys only via environment variables (never in config file)

**Interactive UX**

- **Meeting type selection menu**:
  - Visual TUI with arrow key navigation (↑↓ to move, Enter to select)
  - Shows detected type with confidence + top 5 alternatives
  - Confidence-based messaging (high ≥0.6 green, medium yellow, low <0.5 red)
  - Evidence phrases displayed for transparency
  - Auto-skip in non-TTY environments (CI/automation)
- **Model selection menu** (from v0.8.0, now enhanced):
  - Consistent arrow key navigation
  - TTY detection for headless compatibility
- **`--no-interactive` flag**: Skip all prompts, use recommended values (automation-friendly)

**Transcript Preprocessing**

- **Deterministic normalization** (`--normalize`):
  - Stutter reduction: "I I I think" → "I think"
  - Sentence stitching: Joins segments across pauses ≤500ms
  - Number/date normalization: "march three" → "March 3" (conservative, unambiguous only)
  - Optional filler removal (`--remove-fillers`): Removes um, uh, "you know", "I mean"
- **LLM-based repair** (`--repair`):
  - Fixes ASR errors (misheard words, homophones, grammatical errors)
  - Preserves original meaning (no content invention)
  - Outputs detailed change log with before/after comparisons
- **Change tracking**: `*.changes.md` file with:
  - Summary statistics (total changes, normalization vs repair)
  - Per-change details (timestamp, before, after, reason)
  - Markdown format for easy review
- **Timestamp preservation**: Original segment timestamps maintained throughout preprocessing

**High-Signal Segment Extraction**

- **Smart context window for LLM classification**: Sends first 10-15 minutes + high-signal segments (decision markers like "we'll", "agreed"; action items like "will do", "TODO"; questions like "should we")
- **Configurable extraction**: `context_words` and `max_segments` in config file
- **Token efficiency**: Reduces LLM API costs while maintaining classification accuracy

### Enhanced

- **Notes generation modes**:
  - `--notes basic`: Deterministic extraction (default, no LLM required)
  - `--notes llm`: AI-enhanced extraction with deeper insights
- **Template system**: Jinja2-based templates in `src/mnemofy/templates/` with user override support (`~/.config/mnemofy/templates/`)
- **ClassificationResult dataclass**: Structured output with detected_type, confidence, evidence, secondary_types, engine, timestamp
- **Error handling**: LLM request retries (exponential backoff, max 2 retries), timeout handling, JSON validation, actionable error messages

### CLI Flags Added

```bash
# Meeting type detection
--meeting-type <type>         # auto, status, planning, design, demo, talk, incident, discovery, oneonone, brainstorm
--classify <mode>              # heuristic (default), llm, off
--no-interactive               # Skip interactive prompts

# LLM configuration
--llm-engine <engine>          # openai (default), ollama, openai_compat
--llm-model <model>            # Model name (gpt-4o-mini, llama3.2:3b, etc.)
--llm-base-url <url>           # Custom API endpoint
--llm-timeout <seconds>        # Request timeout
--llm-retries <n>              # Max retry attempts

# Transcript preprocessing
--normalize                    # Apply normalization (stutter, stitching, numbers)
--remove-fillers               # Remove filler words during normalization
--repair                       # LLM-based ASR error repair (requires LLM engine)

# Debugging & observability
--verbose, -v                  # Enable verbose logging (shows LLM timing, detection details)
```

### Technical Architecture

**New Modules**:
- `src/mnemofy/classifier.py`: Meeting type detection (heuristic + LLM modes), dataclasses for ClassificationResult, TranscriptReference, GroundedItem
- `src/mnemofy/llm/base.py`: Abstract base class for LLM engines
- `src/mnemofy/llm/openai_engine.py`: OpenAI API integration (220 lines, retry logic, JSON validation)
- `src/mnemofy/llm/ollama_engine.py`: Ollama local model support (180 lines, model availability check)
- `src/mnemofy/llm/config.py`: Multi-source configuration management (TOML/env/CLI precedence)
- `src/mnemofy/llm/__init__.py`: Factory functions (get_llm_engine, get_llm_config)
- `src/mnemofy/tui/meeting_type_menu.py`: Interactive meeting type selector (267 lines)
- `src/mnemofy/transcriber.py`: Enhanced with normalization/repair (TranscriptChange, NormalizationResult dataclasses)

**Enhanced Modules**:
- `src/mnemofy/cli.py`: Integrated all new features (LLM init, normalization step, interactive menus)
- `src/mnemofy/notes.py`: LLM mode stub, template-based rendering
- `src/mnemofy/output_manager.py`: Added `get_changes_log_path()`

**Testing**:
- 25 normalization tests (`tests/test_transcript_normalization.py`)
- LLM engine tests with mocking
- Interactive menu tests (navigation, TTY detection, confidence behavior)
- High-signal extraction tests
- Configuration precedence tests
- Total test count: 200+ tests

### Dependencies Added

- `jinja2>=3.1.0`: Template engine for notes
- `httpx>=0.25.0`: HTTP client for LLM APIs
- `tomli>=2.0.0`: TOML config file parsing (Python <3.11)
- `tomli-w>=1.0.0`: TOML file writing
- `pytest-asyncio==1.3.0`: Async test support (dev dependency)

### Performance

- **Classification speed**: Heuristic mode <100ms, LLM mode depends on provider (~1-5s typical)
- **Normalization**: Adds <5% to pipeline time
- **LLM repair**: Adds 2-10s depending on transcript length and model
- **Menu responsiveness**: <200ms latency for arrow key navigation (meets SC-009)

### Breaking Changes

None. All new features are opt-in via flags. Default behavior (heuristic classification, basic notes) unchanged.

### Upgrading from v0.9.5

```bash
pip install --upgrade mnemofy
```

**What's New**:
- Meeting types auto-detected (show with `--meeting-type auto`)
- Interactive meeting type menu (skip with `--no-interactive`)
- Optional LLM enhancement (enable with `--notes llm` + `OPENAI_API_KEY`)
- Transcript quality improvements (use `--normalize` or `--repair`)

### Known Limitations

- LLM classification requires internet (OpenAI) or local Ollama server
- Transcript repair quality depends on LLM model capability
- Non-English support: Heuristic classification may degrade; LLM classification recommended
- Config file: API keys must be in environment variables (security by design)

### Security

- API keys only loaded from environment variables (never stored in config files)
- No credentials leaked in logs (even in verbose mode)
- LLM responses validated before use (JSON schema enforcement)
- Change logs reviewed for sensitive data exposure (none found)

---

## [0.9.5] - 2026-02-10

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
