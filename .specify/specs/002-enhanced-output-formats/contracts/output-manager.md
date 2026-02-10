# API Contract: OutputManager

**Feature**: 002-enhanced-output-formats  
**Phase**: 1 (Design - API Contracts)  
**Module**: `src/mnemofy/output_manager.py`

---

## Class: OutputManager

Centralized path management for all output files.

### Purpose
Handle output directory logic, filename generation, and path validation. Single source of truth for where all artifacts (audio, transcripts, notes) are saved.

### Interface

```python
from pathlib import Path
from typing import Optional, Dict

class OutputManager:
    """Manage output paths for transcription artifacts."""
    
    def __init__(
        self,
        input_path: str | Path,
        outdir: Optional[str | Path] = None
    ) -> None:
        """
        Initialize OutputManager.
        
        Args:
            input_path: Path to input video or audio file
            outdir: Output directory for transcripts and notes
                   (default: same directory as input_path)
        
        Raises:
            FileNotFoundError: If input_path does not exist
            PermissionError: If outdir is not writable (after creation attempt)
            ValueError: If outdir cannot be created or input_path is invalid
        
        Examples:
            # Using default outdir (input directory)
            manager = OutputManager("video.mp4")
            
            # Using custom outdir
            manager = OutputManager("video.mp4", outdir="/transcripts")
            
            # With Path objects
            manager = OutputManager(
                Path.home() / "videos" / "meeting.mp4",
                outdir=Path.home() / "transcripts"
            )
        """
        ...
    
    def get_audio_path(self) -> Path:
        """
        Get path for extracted audio file.
        
        Returns:
            Path object: <outdir>/<basename>.mnemofy.wav
        
        Notes:
            - Audio is saved to outdir (respects --outdir flag)
            - Normalized to 16kHz mono WAV format
            - Overwrites existing file if present
        
        Examples:
            manager = OutputManager("meeting.mp4", outdir="/out")
            path = manager.get_audio_path()
            # Returns: Path('/out/meeting.mnemofy.wav')
            
            manager = OutputManager("meeting.mp4")  # default outdir
            path = manager.get_audio_path()
            # Returns: Path('/path/to/meeting.mnemofy.wav')
        """
        ...
    
    def get_transcript_paths(self) -> Dict[str, Path]:
        """
        Get paths for all transcript formats.
        
        Returns:
            Dict with keys: 'txt', 'srt', 'json'
            Example: {
                'txt': Path('/out/meeting.transcript.txt'),
                'srt': Path('/out/meeting.transcript.srt'),
                'json': Path('/out/meeting.transcript.json')
            }
        
        Notes:
            - All transcripts saved to outdir
            - Basenames match input file (preserving original name)
            - Format suffixes: .transcript.txt, .transcript.srt, .transcript.json
        
        Examples:
            manager = OutputManager("video.mp4", outdir="/out")
            paths = manager.get_transcript_paths()
            
            # Use individual paths:
            txt_file = paths['txt']
            srt_file = paths['srt']
            json_file = paths['json']
        """
        ...
    
    def get_notes_path(self) -> Path:
        """
        Get path for structured notes file.
        
        Returns:
            Path object: <outdir>/<basename>.notes.md
        
        Notes:
            - Notes file saved to outdir
            - Markdown format (.notes.md)
            - Only generated if transcript >= 30 seconds
        
        Examples:
            manager = OutputManager("meeting.mp4", outdir="/out")
            path = manager.get_notes_path()
            # Returns: Path('/out/meeting.notes.md')
        """
        ...
    
    @property
    def outdir(self) -> Path:
        """Get the resolved output directory (Path object)."""
        ...
    
    @property
    def basename(self) -> str:
        """Get input file basename without extension."""
        ...
    
    @property
    def input_path(self) -> Path:
        """Get input path (as Path object)."""
        ...
```

### Path Resolution Logic

```
Input: "/home/user/videos/meeting.mp4" with outdir=None
    ↓
Default outdir = input parent = "/home/user/videos"
    ↓
Validate outdir exists (create if needed)
    ↓
Generate paths using outdir + basename
    ↓
Examples:
  get_audio_path()        → /home/user/videos/meeting.mnemofy.wav
  get_transcript_paths()  → {
                              'txt': /home/user/videos/meeting.transcript.txt,
                              'srt': /home/user/videos/meeting.transcript.srt,
                              'json': /home/user/videos/meeting.transcript.json
                            }
  get_notes_path()        → /home/user/videos/meeting.notes.md


Input: "/home/user/videos/meeting.mp4" with outdir="/output"
    ↓
Validate outdir="/output" (create if needed)
    ↓
Generate paths using /output + "meeting"
    ↓
Examples:
  get_audio_path()        → /output/meeting.mnemofy.wav
  get_transcript_paths()  → {
                              'txt': /output/meeting.transcript.txt,
                              'srt': /output/meeting.transcript.srt,
                              'json': /output/meeting.transcript.json
                            }
  get_notes_path()        → /output/meeting.notes.md
```

### Validation Requirements

✅ **On __init__**:
- [ ] input_path must exist and be readable
- [ ] input_path must be absolute or be resolved to absolute
- [ ] outdir (if provided) must be:
  - Writable (or creatable with permissions)
  - Owned by current user (on Unix systems)
  - Not on read-only filesystem
- [ ] Raise FileNotFoundError if input missing
- [ ] Raise PermissionError if outdir not writable
- [ ] Raise ValueError for invalid paths

✅ **Path Safety**:
- [ ] Use pathlib.Path exclusively (no string concatenation)
- [ ] Handle relative paths (resolve to absolute)
- [ ] Support ~/expansion (home directory)
- [ ] Preserve input basename in all outputs
- [ ] No path traversal vulnerabilities (../.. removal)

### Error Handling

```python
# Example: FileNotFoundError
try:
    manager = OutputManager("nonexistent.mp4")
except FileNotFoundError:
    print("Input file not found")

# Example: PermissionError
try:
    manager = OutputManager("video.mp4", outdir="/root/out")  # no write permission
except PermissionError:
    print("Cannot write to output directory")

# Example: ValueError (invalid input)
try:
    manager = OutputManager("")  # empty path
except ValueError:
    print("Invalid input path")
```

### Usage in CLI

```python
from mnemofy.output_manager import OutputManager
from click import Path as ClickPath
import click

@click.command()
@click.argument('input', type=ClickPath(exists=True))
@click.option('--outdir', type=ClickPath(), default=None, 
              help="Output directory (default: same as input)")
def transcribe(input: str, outdir: Optional[str]):
    """Transcribe audio/video file."""
    
    # Create manager (validates paths)
    try:
        manager = OutputManager(input, outdir=outdir)
    except (FileNotFoundError, PermissionError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    
    # Use paths
    audio_path = manager.get_audio_path()
    transcript_paths = manager.get_transcript_paths()
    notes_path = manager.get_notes_path()
    
    # ... rest of transcription logic
```

### Testing Acceptance Criteria

- [ ] Test with default outdir (uses input parent)
- [ ] Test with custom absolute outdir
- [ ] Test with custom relative outdir
- [ ] Test with non-existent outdir (should create)
- [ ] Test with various input extensions (mp4, mkv, wav, aac)
- [ ] Test with spaces in filenames
- [ ] Test with special characters in filenames
- [ ] Test input file not found (FileNotFoundError)
- [ ] Test outdir not writable (PermissionError)
- [ ] Test with ~/expansion in outdir
- [ ] Test path resolution (relative → absolute)
- [ ] Test basename preservation across all paths
- [ ] Achieve 95%+ code coverage

### Implementation Notes

**Dependencies**:
- `pathlib.Path` (stdlib)
- `os.access()` for permission checks (stdlib)
- `tempfile.gettempdir()` for temporary files if needed (stdlib)

**No external dependencies required**.

**Key Implementation Details**:
1. Store resolved paths during __init__ (not compute every time)
2. Use pathlib.Path for all path operations
3. Validate outdir exists after initialization
4. Preserve input filename (handle .mp4, .mkv, .wav differences)
5. Use .expanduser() and .resolve() for robust path handling

---

**Status**: ✅ **CONTRACT DEFINED**

Implementation ready: `src/mnemofy/output_manager.py`

