# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
