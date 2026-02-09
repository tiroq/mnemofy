"""Tests for the audio extraction module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mnemofy.audio import AudioExtractor


@pytest.fixture
def extractor() -> AudioExtractor:
    """Create an AudioExtractor instance."""
    with patch("subprocess.run"):
        return AudioExtractor()


def test_supported_formats(extractor: AudioExtractor) -> None:
    """Test that supported formats are recognized."""
    assert extractor.is_supported(Path("test.mp3"))
    assert extractor.is_supported(Path("test.wav"))
    assert extractor.is_supported(Path("test.aac"))
    assert extractor.is_supported(Path("test.mp4"))
    assert extractor.is_supported(Path("test.mkv"))
    assert not extractor.is_supported(Path("test.txt"))
    assert not extractor.is_supported(Path("test.avi"))


def test_unsupported_format_raises_error(extractor: AudioExtractor) -> None:
    """Test that unsupported formats raise ValueError."""
    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
        with pytest.raises(ValueError, match="Unsupported file format"):
            extractor.extract_audio(Path(tmp.name))


def test_missing_file_raises_error(extractor: AudioExtractor) -> None:
    """Test that missing files raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        extractor.extract_audio(Path("/nonexistent/file.mp3"))


@patch("subprocess.run")
def test_wav_file_returned_directly(
    mock_run: MagicMock, extractor: AudioExtractor
) -> None:
    """Test that WAV files are returned directly when no output specified."""
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        wav_path = Path(tmp.name)
        result = extractor.extract_audio(wav_path)
        assert result == wav_path
        # Should not call ffmpeg
        mock_run.assert_not_called()
