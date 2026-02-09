"""Speech transcription module using faster-whisper."""

from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel


class Transcriber:
    """Transcribe audio using faster-whisper."""

    def __init__(self, model_name: str = "base") -> None:
        """
        Initialize the transcriber.

        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model: WhisperModel | None = None

    def _load_model(self) -> None:
        """Load the Whisper model if not already loaded."""
        if self.model is None:
            # Use CPU with int8 for efficiency
            self.model = WhisperModel(self.model_name, device="cpu", compute_type="int8")

    def transcribe(self, audio_file: Path) -> dict[str, Any]:
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
            segments, info = self.model.transcribe(
                str(audio_file),
                word_timestamps=True,
            )
            
            # Convert faster-whisper format to openai-whisper compatible format
            result: dict[str, Any] = {
                "text": "",
                "segments": [],
                "language": info.language,
            }
            
            for segment in segments:
                result["text"] += segment.text
                result["segments"].append({
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": [
                        {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                        }
                        for word in (segment.words or [])
                    ] if segment.words else [],
                })
            
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to transcribe audio: {e}") from e

    def get_segments(self, transcription: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract segments from transcription result.

        Args:
            transcription: Result from transcribe()

        Returns:
            List of segment dictionaries with text, start, and end times
        """
        segments: list[dict[str, Any]] = transcription.get("segments", [])
        return segments

    def get_full_text(self, transcription: dict[str, Any]) -> str:
        """
        Get full transcribed text.

        Args:
            transcription: Result from transcribe()

        Returns:
            Complete transcribed text
        """
        text: str = transcription.get("text", "")
        return text.strip()
