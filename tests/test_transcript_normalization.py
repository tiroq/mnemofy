"""Tests for transcript normalization and repair functionality."""

import pytest
from unittest.mock import AsyncMock

from mnemofy.transcriber import (
    Transcriber,
    TranscriptChange,
    NormalizationResult,
)


class TestStutterReduction:
    """Test stutter reduction functionality."""
    
    def test_reduce_simple_stutter(self):
        """Test reducing simple repeated words."""
        transcriber = Transcriber()
        
        text = "I I I think we should do this"
        result = transcriber._reduce_stutters(text)
        
        assert result == "I think we should do this"
    
    def test_reduce_multiple_stutters(self):
        """Test reducing multiple stutters in same text."""
        transcriber = Transcriber()
        
        text = "the the project is is going well"
        result = transcriber._reduce_stutters(text)
        
        assert result == "the project is going well"
    
    def test_preserve_intentional_repetition(self):
        """Test that intentional repetition in different contexts is preserved."""
        transcriber = Transcriber()
        
        text = "I said I would do it"  # Two "I"s in different contexts
        result = transcriber._reduce_stutters(text)
        
        # Should preserve when words aren't adjacent
        assert "I" in result
    
    def test_case_insensitive_stutter(self):
        """Test stutter reduction is case insensitive."""
        transcriber = Transcriber()
        
        text = "We we We need to discuss"
        result = transcriber._reduce_stutters(text)
        
        assert result == "We need to discuss"


class TestFillerRemoval:
    """Test filler word filtering functionality."""
    
    def test_remove_um_uh(self):
        """Test removing um and uh fillers."""
        transcriber = Transcriber()
        
        text = "um I think uh we should proceed"
        result = transcriber._filter_fillers(text)
        
        assert "um" not in result.lower()
        assert "uh" not in result.lower()
        assert "think" in result
        assert "proceed" in result
    
    def test_remove_you_know(self):
        """Test removing 'you know' filler phrase."""
        transcriber = Transcriber()
        
        text = "this is, you know, a good idea"
        result = transcriber._filter_fillers(text)
        
        assert "you know" not in result.lower()
        assert "good idea" in result
    
    def test_preserve_like_as_verb(self):
        """Test that 'like' as a verb is preserved."""
        transcriber = Transcriber()
        
        text = "I like this approach"
        result = transcriber._filter_fillers(text)
        
        # Should preserve "like" when used as verb
        assert "like" in result.lower()
    
    def test_clean_extra_spaces(self):
        """Test that extra spaces are cleaned up after filler removal."""
        transcriber = Transcriber()
        
        text = "um   we should   uh  proceed"
        result = transcriber._filter_fillers(text)
        
        # Should not have multiple consecutive spaces
        assert "  " not in result


class TestSentenceStitching:
    """Test sentence stitching across short pauses."""
    
    def test_stitch_short_pause(self):
        """Test stitching segments with pause ≤500ms."""
        transcriber = Transcriber()
        
        segments = [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "Hello everyone",
                "words": [],
            },
            {
                "id": 1,
                "start": 2.3,  # 300ms pause
                "end": 4.0,
                "text": "welcome to the meeting",
                "words": [],
            },
        ]
        
        stitched, changes = transcriber._stitch_sentences(segments)
        
        assert len(stitched) == 1
        assert "Hello everyone" in stitched[0]["text"]
        assert "welcome to the meeting" in stitched[0]["text"]
        assert len(changes) == 1
        assert "300ms" in changes[0].reason or "0.3" in changes[0].reason
    
    def test_no_stitch_long_pause(self):
        """Test that segments with pause >500ms are not stitched."""
        transcriber = Transcriber()
        
        segments = [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "First sentence",
                "words": [],
            },
            {
                "id": 1,
                "start": 3.0,  # 1000ms pause
                "end": 5.0,
                "text": "Second sentence",
                "words": [],
            },
        ]
        
        stitched, changes = transcriber._stitch_sentences(segments)
        
        assert len(stitched) == 2
        assert stitched[0]["text"] == "First sentence"
        assert stitched[1]["text"] == "Second sentence"
    
    def test_preserve_timestamps(self):
        """Test that timestamps are preserved correctly when stitching."""
        transcriber = Transcriber()
        
        segments = [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "Part one",
                "words": [],
            },
            {
                "id": 1,
                "start": 2.3,
                "end": 4.0,
                "text": "part two",
                "words": [],
            },
        ]
        
        stitched, _ = transcriber._stitch_sentences(segments)
        
        assert len(stitched) == 1
        assert stitched[0]["start"] == 0.0
        assert stitched[0]["end"] == 4.0


class TestNumberDateNormalization:
    """Test number and date normalization."""
    
    def test_normalize_month_day(self):
        """Test normalizing 'month day' patterns."""
        transcriber = Transcriber()
        
        text = "the deadline is march three"
        result = transcriber._normalize_numbers_dates(text)
        
        assert "March 3" in result
    
    def test_normalize_numbers_with_context(self):
        """Test normalizing numbers in specific contexts."""
        transcriber = Transcriber()
        
        text = "meet at five pm"
        result = transcriber._normalize_numbers_dates(text)
        
        assert "5 pm" in result or "5 PM" in result.lower()
    
    def test_preserve_ambiguous_numbers(self):
        """Test that ambiguous number words are not changed."""
        transcriber = Transcriber()
        
        text = "one of the options"
        result = transcriber._normalize_numbers_dates(text)
        
        # Should not normalize "one" in this context
        # (conservative approach)
        assert "one" in result.lower()


class TestFullNormalization:
    """Test complete normalization workflow."""
    
    def test_normalize_transcript_default(self):
        """Test normalizing transcript with default options."""
        transcriber = Transcriber()
        
        transcription = {
            "text": "I I I think we should meet march three at five pm",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "I I I think we should meet march three at five pm",
                    "words": [],
                },
            ],
            "language": "en",
        }
        
        result = transcriber.normalize_transcript(transcription)
        
        assert isinstance(result, NormalizationResult)
        assert len(result.changes) > 0
        # Should reduce stutter
        assert result.transcription["segments"][0]["text"].count("I") < 3
    
    def test_normalize_with_filler_removal(self):
        """Test normalization with filler removal enabled."""
        transcriber = Transcriber()
        
        transcription = {
            "text": "um I think uh we should proceed",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 3.0,
                    "text": "um I think uh we should proceed",
                    "words": [],
                },
            ],
            "language": "en",
        }
        
        result = transcriber.normalize_transcript(
            transcription,
            remove_fillers=True,
        )
        
        normalized_text = result.transcription["segments"][0]["text"]
        assert "um" not in normalized_text.lower()
        assert "uh" not in normalized_text.lower()
    
    def test_changes_log_structure(self):
        """Test that changes log has correct structure."""
        transcriber = Transcriber()
        
        transcription = {
            "text": "I I I think we should do this",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 3.0,
                    "text": "I I I think we should do this",
                    "words": [],
                },
            ],
            "language": "en",
        }
        
        result = transcriber.normalize_transcript(transcription)
        
        assert len(result.changes) > 0
        
        for change in result.changes:
            assert isinstance(change, TranscriptChange)
            assert hasattr(change, "segment_id")
            assert hasattr(change, "timestamp")
            assert hasattr(change, "before")
            assert hasattr(change, "after")
            assert hasattr(change, "reason")
            assert change.change_type == "normalization"
    
    def test_timestamp_format(self):
        """Test that timestamps are formatted correctly."""
        transcriber = Transcriber()
        
        formatted = transcriber._format_timestamp(65.5, 125.3)
        
        # Should be in MM:SS-MM:SS format
        assert "-" in formatted
        parts = formatted.split("-")
        assert len(parts) == 2
        assert ":" in parts[0]
        assert ":" in parts[1]


class TestLLMRepair:
    """Test LLM-based transcript repair."""
    
    @pytest.mark.asyncio
    async def test_repair_transcript_basic(self):
        """Test basic transcript repair with mocked LLM."""
        transcriber = Transcriber()
        
        transcription = {
            "text": "the quick brown focks jumped",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 3.0,
                    "text": "the quick brown focks jumped",
                    "words": [],
                },
            ],
            "language": "en",
        }
        
        # Mock LLM engine
        mock_llm = AsyncMock()
        mock_llm.repair_transcript = AsyncMock(
            return_value={
                "repaired_text": "the quick brown fox jumped",
                "changes": [
                    {
                        "timestamp": "00:00-00:03",
                        "before": "focks",
                        "after": "fox",
                        "reason": "ASR error: corrected misspelling",
                    }
                ],
            }
        )
        
        result = await transcriber.repair_transcript(transcription, mock_llm)
        
        assert isinstance(result, NormalizationResult)
        assert result.transcription["text"] == "the quick brown fox jumped"
        assert len(result.changes) > 0
        assert result.changes[0].change_type == "repair"
    
    @pytest.mark.asyncio
    async def test_repair_prompt_format(self):
        """Test that repair prompt is formatted correctly."""
        transcriber = Transcriber()
        
        transcript_text = "test transcript with errors"
        prompt = transcriber._build_repair_prompt(transcript_text)
        
        assert "test transcript with errors" in prompt
        assert "fix" in prompt.lower() or "repair" in prompt.lower()
        assert "preserve" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_repair_failure_handling(self):
        """Test handling of LLM repair failures."""
        transcriber = Transcriber()
        
        transcription = {
            "text": "test text",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.0,
                    "text": "test text",
                    "words": [],
                },
            ],
            "language": "en",
        }
        
        # Mock LLM engine that raises error
        mock_llm = AsyncMock()
        mock_llm.repair_transcript = AsyncMock(
            side_effect=RuntimeError("LLM connection failed")
        )
        
        with pytest.raises(RuntimeError, match="Failed to repair transcript"):
            await transcriber.repair_transcript(transcription, mock_llm)
    
    @pytest.mark.asyncio
    async def test_repair_preserves_timestamps(self):
        """Test that repair preserves segment timestamps."""
        transcriber = Transcriber()
        
        transcription = {
            "text": "original text",
            "segments": [
                {
                    "id": 0,
                    "start": 10.5,
                    "end": 15.7,
                    "text": "original text",
                    "words": [],
                },
            ],
            "language": "en",
        }
        
        mock_llm = AsyncMock()
        mock_llm.repair_transcript = AsyncMock(
            return_value="repaired text"
        )
        
        result = await transcriber.repair_transcript(transcription, mock_llm)
        
        # Timestamps should be preserved
        assert result.transcription["segments"][0]["start"] == 10.5
        assert result.transcription["segments"][0]["end"] == 15.7


class TestTimestampFormatting:
    """Test timestamp formatting utility."""
    
    def test_format_simple_timestamp(self):
        """Test formatting simple timestamps."""
        transcriber = Transcriber()
        
        result = transcriber._format_timestamp(0.0, 30.0)
        assert result == "00:00-00:30"
    
    def test_format_minutes_seconds(self):
        """Test formatting with minutes and seconds."""
        transcriber = Transcriber()
        
        result = transcriber._format_timestamp(125.0, 187.0)
        assert result == "02:05-03:07"
    
    def test_format_with_fractional_seconds(self):
        """Test formatting handles fractional seconds."""
        transcriber = Transcriber()
        
        result = transcriber._format_timestamp(65.7, 125.3)
        # Should round down to whole seconds
        assert result == "01:05-02:05"
