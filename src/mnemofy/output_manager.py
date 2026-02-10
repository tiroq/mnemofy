"""Output path management for transcription artifacts.

This module provides OutputManager for centralized path generation
and validation for all output files (audio, transcripts, notes).
"""

from pathlib import Path
from typing import Optional, Dict
import os


class OutputManager:
    """Manage output paths for transcription artifacts.
    
    Centralized source of truth for where all artifacts (audio, transcripts, notes)
    are saved. Handles path validation, creation, and generation.
    
    Examples:
        # Default outdir (input file's directory)
        manager = OutputManager("video.mp4")
        audio = manager.get_audio_path()  # video.mnemofy.wav
        
        # Custom outdir
        manager = OutputManager("video.mp4", outdir="/transcripts")
        paths = manager.get_transcript_paths()  # /transcripts/*.transcript.*
    """
    
    def __init__(
        self,
        input_path: str | Path,
        outdir: Optional[str | Path] = None
    ) -> None:
        """Initialize OutputManager.
        
        Args:
            input_path: Path to input video or audio file.
            outdir: Output directory for transcripts and notes.
                   Defaults to input file's directory if not specified.
        
        Raises:
            FileNotFoundError: If input_path does not exist.
            PermissionError: If outdir is not writable (after creation attempt).
            ValueError: If input_path is invalid or outdir cannot be created.
        
        Examples:
            manager = OutputManager("video.mp4")
            manager = OutputManager("video.mp4", outdir="/transcripts")
            manager = OutputManager(Path.home() / "videos" / "meeting.mp4", outdir="/out")
        """
        # Validate and resolve input path
        input_path = Path(input_path).expanduser().resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        self._input_path = input_path
        self._basename = input_path.stem  # filename without extension
        
        # Resolve output directory
        if outdir is None:
            # Default: same directory as input
            self._outdir = input_path.parent
        else:
            outdir_path = Path(outdir).expanduser().resolve()
            self._outdir = outdir_path
        
        # Validate and create outdir if needed
        self._validate_outdir()
    
    def _validate_outdir(self) -> None:
        """Validate output directory is writable.
        
        Creates directory if it doesn't exist.
        
        Raises:
            PermissionError: If outdir is not writable.
            ValueError: If outdir is a file (not directory).
        """
        if self._outdir.exists():
            # Check it's a directory
            if not self._outdir.is_dir():
                raise ValueError(f"Output path exists but is not a directory: {self._outdir}")
            
            # Check write permission
            if not os.access(self._outdir, os.W_OK):
                raise PermissionError(f"Output directory is not writable: {self._outdir}")
        else:
            # Try to create directory
            try:
                self._outdir.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise PermissionError(f"Cannot create output directory: {self._outdir}") from e
            except OSError as e:
                raise ValueError(f"Cannot create output directory: {self._outdir}") from e
    
    def get_audio_path(self) -> Path:
        """Get path for extracted audio file.
        
        Returns:
            Path: <outdir>/<basename>.mnemofy.wav
        
        Notes:
            Audio is saved to outdir (respects --outdir flag in CLI).
            Normalized to 16kHz mono WAV format.
        
        Examples:
            manager = OutputManager("meeting.mp4", outdir="/out")
            path = manager.get_audio_path()
            # Returns: Path('/out/meeting.mnemofy.wav')
        """
        return self._outdir / f"{self._basename}.mnemofy.wav"
    
    def get_transcript_paths(self) -> Dict[str, Path]:
        """Get paths for all transcript formats.
        
        Returns:
            Dict with keys 'txt', 'srt', 'json' mapping to Path objects.
            
            Example:
                {
                    'txt': Path('/out/meeting.transcript.txt'),
                    'srt': Path('/out/meeting.transcript.srt'),
                    'json': Path('/out/meeting.transcript.json')
                }
        
        Notes:
            All transcripts saved to outdir.
            Basenames preserve original input filename.
        """
        return {
            'txt': self._outdir / f"{self._basename}.transcript.txt",
            'srt': self._outdir / f"{self._basename}.transcript.srt",
            'json': self._outdir / f"{self._basename}.transcript.json",
        }
    
    def get_notes_path(self) -> Path:
        """Get path for structured notes file.
        
        Returns:
            Path: <outdir>/<basename>.notes.md
        
        Notes:
            Notes file saved to outdir.
            Markdown format (.notes.md).
            Only generated if transcript >= 30 seconds.
        
        Examples:
            manager = OutputManager("meeting.mp4", outdir="/out")
            path = manager.get_notes_path()
            # Returns: Path('/out/meeting.notes.md')
        """
        return self._outdir / f"{self._basename}.notes.md"
    
    @property
    def outdir(self) -> Path:
        """Get the resolved output directory (Path object).
        
        Returns:
            Path: Absolute path to output directory.
        """
        return self._outdir
    
    @property
    def basename(self) -> str:
        """Get input file basename without extension.
        
        Returns:
            str: Filename without extension (e.g., "meeting").
        
        Examples:
            manager = OutputManager("/path/meeting.mp4")
            manager.basename  # "meeting"
        """
        return self._basename
    
    @property
    def input_path(self) -> Path:
        """Get input path as Path object.
        
        Returns:
            Path: Absolute path to input file.
        """
        return self._input_path
