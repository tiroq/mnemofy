"""Audio extraction module using ffmpeg."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class AudioExtractor:
    """Extract audio from media files using ffmpeg."""

    SUPPORTED_FORMATS = {".aac", ".mp3", ".wav", ".mkv", ".mp4"}

    def __init__(self) -> None:
        """Initialize the audio extractor."""
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> None:
        """Check if ffmpeg is available."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(
                "ffmpeg is not installed or not available in PATH. "
                "Please install ffmpeg to use mnemofy."
            ) from e

    def is_supported(self, file_path: Path) -> bool:
        """Check if the file format is supported."""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS

    def extract_audio(
        self, input_file: Path, output_file: Optional[Path] = None
    ) -> Path:
        """
        Extract audio from media file.

        Args:
            input_file: Path to input media file
            output_file: Optional path for output audio file. If None, creates temp file.
                        Parent directory will be created if it doesn't exist.

        Returns:
            Path to extracted audio file (WAV format)

        Raises:
            ValueError: If file format is not supported
            RuntimeError: If audio extraction fails
            FileNotFoundError: If input file not found
        """
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        if not self.is_supported(input_file):
            raise ValueError(
                f"Unsupported file format: {input_file.suffix}. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_FORMATS))}"
            )

        # For pure audio files, check if we need conversion
        if input_file.suffix.lower() == ".wav":
            # Already in WAV format - can use directly
            if output_file is None:
                return input_file
            # Copy if output path specified
            import shutil

            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_file, output_file)
            return output_file

        # Create output file if not specified
        if output_file is None:
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False, prefix="mnemofy_"
            )
            output_file = Path(temp_file.name)
            temp_file.close()
        else:
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)

        # Extract audio using ffmpeg
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    str(input_file),
                    "-vn",  # No video
                    "-acodec",
                    "pcm_s16le",  # PCM 16-bit little-endian
                    "-ar",
                    "16000",  # 16kHz sample rate (good for speech)
                    "-ac",
                    "1",  # Mono
                    "-y",  # Overwrite output file
                    str(output_file),
                ],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to extract audio from {input_file}: {e.stderr.decode()}"
            ) from e

        return output_file
