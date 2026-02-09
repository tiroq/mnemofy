"""Tests for the transcriber module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mnemofy.transcriber import Transcriber


@pytest.fixture
def transcriber() -> Transcriber:
    """Create a Transcriber instance."""
    return Transcriber(model_name="tiny")


@patch("whisper.load_model")
def test_model_loading(mock_load: MagicMock, transcriber: Transcriber) -> None:
    """Test that the model is loaded on first transcription."""
    mock_load.return_value = MagicMock()
    transcriber._load_model()
    mock_load.assert_called_once_with("tiny")


def test_missing_file_raises_error(transcriber: Transcriber) -> None:
    """Test that missing files raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        transcriber.transcribe(Path("/nonexistent/file.wav"))


def test_get_segments() -> None:
    """Test extracting segments from transcription."""
    transcriber = Transcriber()
    transcription = {
        "text": "Hello world",
        "segments": [
            {"text": "Hello", "start": 0.0, "end": 1.0},
            {"text": "world", "start": 1.0, "end": 2.0},
        ],
    }

    segments = transcriber.get_segments(transcription)
    assert len(segments) == 2
    assert segments[0]["text"] == "Hello"
    assert segments[1]["text"] == "world"


def test_get_full_text() -> None:
    """Test extracting full text from transcription."""
    transcriber = Transcriber()
    transcription = {
        "text": "  Hello world  ",
        "segments": [],
    }

    text = transcriber.get_full_text(transcription)
    assert text == "Hello world"
