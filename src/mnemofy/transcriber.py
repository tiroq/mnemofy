"""Speech transcription module using OpenAI Whisper."""

import warnings
from pathlib import Path
from typing import Any, Dict, List

import whisper


class Transcriber:
    """Transcribe audio using OpenAI Whisper."""

    def __init__(self, model_name: str = "base") -> None:
        """
        Initialize the transcriber.

        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model: Any = None

    def _load_model(self) -> None:
        """Load the Whisper model if not already loaded."""
        if self.model is None:
            # Suppress FP16 warning on CPU
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.model = whisper.load_model(self.model_name)

    def transcribe(self, audio_file: Path) -> Dict[str, Any]:
        """
        Transcribe audio file.

        Args:
            audio_file: Path to audio file (WAV format recommended)

        Returns:
            Dictionary containing transcription results with segments

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        self._load_model()

        try:
            # Transcribe with word-level timestamps
            result = self.model.transcribe(
                str(audio_file),
                word_timestamps=True,
                verbose=False,
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to transcribe audio: {e}") from e

    def get_segments(self, transcription: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract segments from transcription result.

        Args:
            transcription: Result from transcribe()

        Returns:
            List of segment dictionaries with text, start, and end times
        """
        return transcription.get("segments", [])

    def get_full_text(self, transcription: Dict[str, Any]) -> str:
        """
        Get full transcribed text.

        Args:
            transcription: Result from transcribe()

        Returns:
            Complete transcribed text
        """
        return transcription.get("text", "").strip()
