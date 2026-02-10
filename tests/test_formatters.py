"""Tests for TranscriptFormatter and helper functions."""

import json
import pytest
from mnemofy.formatters import (
    TranscriptFormatter,
    seconds_to_hms,
    validate_segment,
)


# ============================================================================
# Tests for seconds_to_hms helper function
# ============================================================================

class TestSecondsToHms:
    """Test seconds_to_hms time conversion helper."""
    
    def test_basic_conversion_txt(self):
        """Test basic seconds to TXT format conversion."""
        assert seconds_to_hms(0, format="txt") == "00:00:00"
        assert seconds_to_hms(1, format="txt") == "00:00:01"
        assert seconds_to_hms(60, format="txt") == "00:01:00"
        assert seconds_to_hms(3600, format="txt") == "01:00:00"
    
    def test_basic_conversion_srt(self):
        """Test basic seconds to SRT format conversion."""
        assert seconds_to_hms(0, format="srt") == "00:00:00,000"
        assert seconds_to_hms(1, format="srt") == "00:00:01,000"
        assert seconds_to_hms(60, format="srt") == "00:01:00,000"
        assert seconds_to_hms(3600, format="srt") == "01:00:00,000"
    
    def test_milliseconds_handling(self):
        """Test milliseconds precision in SRT format."""
        assert seconds_to_hms(1.123, format="srt") == "00:00:01,123"
        assert seconds_to_hms(1.5, format="srt") == "00:00:01,500"
        assert seconds_to_hms(1.999, format="srt") == "00:00:01,999"
        assert seconds_to_hms(1.001, format="srt") == "00:00:01,001"
    
    def test_txt_ignores_subseconds(self):
        """Test that TXT format ignores subseconds."""
        assert seconds_to_hms(1.999, format="txt") == "00:00:01"
        assert seconds_to_hms(1.123, format="txt") == "00:00:01"
    
    def test_combined_units(self):
        """Test conversion with multiple time units."""
        # 1 hour, 2 minutes, 3 seconds
        assert seconds_to_hms(3723, format="txt") == "01:02:03"
        assert seconds_to_hms(3723.5, format="srt") == "01:02:03,500"
    
    def test_large_hours(self):
        """Test durations exceeding 24 hours."""
        # 50 hours, 0 minutes, 0 seconds
        assert seconds_to_hms(180000, format="txt") == "50:00:00"
        assert seconds_to_hms(180000, format="srt") == "50:00:00,000"
    
    def test_microsecond_precision(self):
        """Test that microseconds are handled correctly."""
        # 1.1234567 seconds should round to 123 milliseconds
        assert seconds_to_hms(1.1234567, format="srt") == "00:00:01,123"
    
    def test_negative_seconds_raises_error(self):
        """Test that negative seconds raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            seconds_to_hms(-1)
    
    def test_invalid_type_raises_error(self):
        """Test that non-numeric input raises TypeError."""
        with pytest.raises(TypeError, match="must be numeric"):
            seconds_to_hms("1")
        with pytest.raises(TypeError, match="must be numeric"):
            seconds_to_hms(None)
    
    def test_unknown_format_raises_error(self):
        """Test that unknown format string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown format"):
            seconds_to_hms(1, format="invalid")


# ============================================================================
# Tests for validate_segment helper function
# ============================================================================

class TestValidateSegment:
    """Test segment validation helper."""
    
    def test_valid_segment(self):
        """Test validation of valid segment."""
        segment = {"start": 1.0, "end": 5.0, "text": "Hello"}
        validate_segment(segment)  # Should not raise
    
    def test_valid_segment_with_index(self):
        """Test validation with index for error messages."""
        segment = {"start": 1.0, "end": 5.0, "text": "Hello"}
        validate_segment(segment, index=0)  # Should not raise
    
    def test_missing_start_raises_keyerror(self):
        """Test that missing 'start' raises KeyError."""
        segment = {"end": 5.0, "text": "Hello"}
        with pytest.raises(KeyError, match="'start'"):
            validate_segment(segment)
    
    def test_missing_end_raises_keyerror(self):
        """Test that missing 'end' raises KeyError."""
        segment = {"start": 1.0, "text": "Hello"}
        with pytest.raises(KeyError, match="'end'"):
            validate_segment(segment)
    
    def test_missing_text_raises_keyerror(self):
        """Test that missing 'text' raises KeyError."""
        segment = {"start": 1.0, "end": 5.0}
        with pytest.raises(KeyError, match="'text'"):
            validate_segment(segment)
    
    def test_invalid_start_type(self):
        """Test that non-numeric start raises TypeError."""
        segment = {"start": "1", "end": 5.0, "text": "Hello"}
        with pytest.raises(TypeError, match="'start'"):
            validate_segment(segment)
    
    def test_invalid_end_type(self):
        """Test that non-numeric end raises TypeError."""
        segment = {"start": 1.0, "end": "5", "text": "Hello"}
        with pytest.raises(TypeError, match="'end'"):
            validate_segment(segment)
    
    def test_invalid_text_type(self):
        """Test that non-string text raises TypeError."""
        segment = {"start": 1.0, "end": 5.0, "text": 123}
        with pytest.raises(TypeError, match="'text'"):
            validate_segment(segment)
    
    def test_start_greater_than_end(self):
        """Test that start >= end raises ValueError."""
        segment = {"start": 5.0, "end": 1.0, "text": "Hello"}
        with pytest.raises(ValueError, match="start"):
            validate_segment(segment)
    
    def test_start_equals_end(self):
        """Test that start == end raises ValueError."""
        segment = {"start": 5.0, "end": 5.0, "text": "Hello"}
        with pytest.raises(ValueError, match="start"):
            validate_segment(segment)
    
    def test_error_message_includes_index(self):
        """Test that error messages include segment index when provided."""
        segment = {"start": 5.0, "end": 1.0, "text": "Hello"}
        with pytest.raises(ValueError, match="segment 3"):
            validate_segment(segment, index=3)
    
    def test_integer_timing_accepted(self):
        """Test that integer timing values are accepted."""
        segment = {"start": 1, "end": 5, "text": "Hello"}
        validate_segment(segment)  # Should not raise
    
    def test_empty_text_allowed(self):
        """Test that empty string text is allowed."""
        segment = {"start": 1.0, "end": 5.0, "text": ""}
        validate_segment(segment)  # Should not raise


# ============================================================================
# Tests for TranscriptFormatter.to_txt
# ============================================================================

class TestTranscriptFormatterToTxt:
    """Test TranscriptFormatter.to_txt method."""
    
    def test_single_segment(self):
        """Test conversion of single segment."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello world"}]
        result = TranscriptFormatter.to_txt(segments)
        assert result == "[00:00:01–00:00:05] Hello world"
    
    def test_multiple_segments(self):
        """Test conversion of multiple segments."""
        segments = [
            {"start": 1.0, "end": 5.0, "text": "First"},
            {"start": 5.0, "end": 10.0, "text": "Second"},
            {"start": 10.0, "end": 15.0, "text": "Third"},
        ]
        result = TranscriptFormatter.to_txt(segments)
        lines = result.split("\n")
        assert len(lines) == 3
        assert lines[0] == "[00:00:01–00:00:05] First"
        assert lines[1] == "[00:00:05–00:00:10] Second"
        assert lines[2] == "[00:00:10–00:00:15] Third"
    
    def test_empty_segments_raises_error(self):
        """Test that empty segment list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            TranscriptFormatter.to_txt([])
    
    def test_uses_en_dash_separator(self):
        """Test that en-dash (–) is used, not hyphen (-)."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        result = TranscriptFormatter.to_txt(segments)
        # En-dash is U+2013, hyphen is U+002D
        assert "–" in result
        assert "-" not in result.split("]")[0]  # Before the closing bracket
    
    def test_long_duration_segments(self):
        """Test segments with hours included."""
        segments = [{"start": 3661.0, "end": 7200.0, "text": "Long segment"}]
        result = TranscriptFormatter.to_txt(segments)
        assert result == "[01:01:01–02:00:00] Long segment"
    
    def test_very_short_segment(self):
        """Test segment under 100ms."""
        segments = [{"start": 1.0, "end": 1.050, "text": "Ping"}]
        result = TranscriptFormatter.to_txt(segments)
        assert "[00:00:01–00:00:01] Ping" == result
    
    def test_empty_text_segment(self):
        """Test segment with empty text."""
        segments = [{"start": 1.0, "end": 5.0, "text": ""}]
        result = TranscriptFormatter.to_txt(segments)
        assert result == "[00:00:01–00:00:05] "
    
    def test_special_characters_in_text(self):
        """Test segments with special characters."""
        segments = [
            {"start": 1.0, "end": 5.0, "text": "Hello, world!"},
            {"start": 5.0, "end": 10.0, "text": "What's up?"},
            {"start": 10.0, "end": 15.0, "text": "café naïve"},
        ]
        result = TranscriptFormatter.to_txt(segments)
        assert "Hello, world!" in result
        assert "What's up?" in result
        assert "café naïve" in result
    
    def test_multiline_text_preserved(self):
        """Test that multiline text is preserved (newlines in segment text)."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Line 1\nLine 2"}]
        result = TranscriptFormatter.to_txt(segments)
        assert "Line 1\nLine 2" in result
    
    def test_consecutive_segments(self):
        """Test segments with no gaps between them."""
        segments = [
            {"start": 0.0, "end": 5.0, "text": "A"},
            {"start": 5.0, "end": 10.0, "text": "B"},
            {"start": 10.0, "end": 15.0, "text": "C"},
        ]
        result = TranscriptFormatter.to_txt(segments)
        assert "[00:00:00–00:00:05] A" in result
        assert "[00:00:05–00:00:10] B" in result
        assert "[00:00:10–00:00:15] C" in result
    
    def test_missing_required_field_raises_error(self):
        """Test that missing required field raises KeyError."""
        segments = [{"start": 1.0, "text": "Hello"}]  # missing 'end'
        with pytest.raises(KeyError):
            TranscriptFormatter.to_txt(segments)
    
    def test_invalid_timing_raises_error(self):
        """Test that invalid timing raises ValueError."""
        segments = [{"start": 5.0, "end": 1.0, "text": "Bad"}]
        with pytest.raises(ValueError):
            TranscriptFormatter.to_txt(segments)


# ============================================================================
# Tests for TranscriptFormatter.to_srt
# ============================================================================

class TestTranscriptFormatterToSrt:
    """Test TranscriptFormatter.to_srt method."""
    
    def test_single_segment(self):
        """Test conversion of single segment."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello world"}]
        result = TranscriptFormatter.to_srt(segments)
        assert "1\n" in result  # Sequence number
        assert "00:00:01,000 --> 00:00:05,000\n" in result  # Timing
        assert "Hello world" in result
    
    def test_multiple_segments(self):
        """Test conversion of multiple segments."""
        segments = [
            {"start": 1.0, "end": 5.0, "text": "First"},
            {"start": 5.0, "end": 10.0, "text": "Second"},
            {"start": 10.0, "end": 15.0, "text": "Third"},
        ]
        result = TranscriptFormatter.to_srt(segments)
        
        # Should have sequence numbers
        assert "1\n" in result
        assert "2\n" in result
        assert "3\n" in result
        
        # Should have blank line between blocks
        assert "\n\n" in result
    
    def test_empty_segments_raises_error(self):
        """Test that empty segment list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            TranscriptFormatter.to_srt([])
    
    def test_millisecond_timing_format(self):
        """Test that timing includes milliseconds in SRT format."""
        segments = [{"start": 1.123, "end": 5.456, "text": "Timed"}]
        result = TranscriptFormatter.to_srt(segments)
        assert "00:00:01,123 --> 00:00:05,456" in result
    
    def test_srt_block_structure(self):
        """Test proper SRT block structure (sequence, timing, text)."""
        segments = [{"start": 0.0, "end": 3.0, "text": "Block 1"}]
        result = TranscriptFormatter.to_srt(segments)
        lines = result.split("\n")
        assert lines[0] == "1"  # Sequence
        assert "00:00:00,000 --> 00:00:03,000" in lines[1]  # Timing
        assert lines[2] == "Block 1"  # Text
    
    def test_sequential_numbering(self):
        """Test that sequence numbers are sequential starting from 1."""
        segments = [
            {"start": 0.0, "end": 3.0, "text": "A"},
            {"start": 3.0, "end": 6.0, "text": "B"},
            {"start": 6.0, "end": 9.0, "text": "C"},
            {"start": 9.0, "end": 12.0, "text": "D"},
        ]
        result = TranscriptFormatter.to_srt(segments)
        
        # Count occurrences of sequence numbers at start of blocks
        blocks = result.split("\n\n")
        for i, block in enumerate(blocks, 1):
            assert block.startswith(str(i))
    
    def test_multiline_subtitle_text(self):
        """Test that multi-line subtitle text is supported."""
        segments = [{"start": 0.0, "end": 5.0, "text": "Line 1\nLine 2\nLine 3"}]
        result = TranscriptFormatter.to_srt(segments)
        assert "Line 1\nLine 2\nLine 3" in result
    
    def test_blank_line_separators(self):
        """Test that blank lines separate SRT blocks."""
        segments = [
            {"start": 0.0, "end": 3.0, "text": "A"},
            {"start": 3.0, "end": 6.0, "text": "B"},
        ]
        result = TranscriptFormatter.to_srt(segments)
        blocks = result.split("\n\n")
        assert len(blocks) == 2
    
    def test_special_characters_preserved(self):
        """Test that special characters are preserved in SRT."""
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Café naïve"},
            {"start": 5.0, "end": 10.0, "text": "émoji 🎉"},
        ]
        result = TranscriptFormatter.to_srt(segments)
        assert "Café naïve" in result
        assert "émoji 🎉" in result
    
    def test_long_duration_subtitles(self):
        """Test subtitles lasting more than 1 hour."""
        segments = [{"start": 3600.0, "end": 7200.0, "text": "Long"}]
        result = TranscriptFormatter.to_srt(segments)
        assert "01:00:00,000 --> 02:00:00,000" in result
    
    def test_missing_required_field_raises_error(self):
        """Test that missing required field raises KeyError."""
        segments = [{"start": 1.0, "text": "Hello"}]  # missing 'end'
        with pytest.raises(KeyError):
            TranscriptFormatter.to_srt(segments)
    
    def test_invalid_timing_raises_error(self):
        """Test that invalid timing raises ValueError."""
        segments = [{"start": 5.0, "end": 1.0, "text": "Bad"}]
        with pytest.raises(ValueError):
            TranscriptFormatter.to_srt(segments)


# ============================================================================
# Tests for TranscriptFormatter.to_json
# ============================================================================

class TestTranscriptFormatterToJson:
    """Test TranscriptFormatter.to_json method."""
    
    def test_basic_json_conversion(self):
        """Test basic conversion to JSON."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 5.0,
        }
        
        result = TranscriptFormatter.to_json(segments, metadata)
        parsed = json.loads(result)
        
        assert parsed["schema_version"] == "1.0"
        assert parsed["metadata"]["engine"] == "faster-whisper"
        assert len(parsed["segments"]) == 1
    
    def test_schema_version_in_output(self):
        """Test that schema_version is included in output."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 5.0,
        }
        
        result = TranscriptFormatter.to_json(segments, metadata)
        parsed = json.loads(result)
        
        assert "schema_version" in parsed
        assert parsed["schema_version"] == "1.0"
    
    def test_metadata_fields_preserved(self):
        """Test that all metadata fields are preserved."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 5.0,
            "timestamp": "2026-02-10T14:30:45Z",
            "mnemofy_version": "0.8.0",
        }
        
        result = TranscriptFormatter.to_json(segments, metadata)
        parsed = json.loads(result)
        
        assert parsed["metadata"]["engine"] == "faster-whisper"
        assert parsed["metadata"]["timestamp"] == "2026-02-10T14:30:45Z"
        assert parsed["metadata"]["mnemofy_version"] == "0.8.0"
    
    def test_segments_array_preserved(self):
        """Test that segment data is preserved."""
        segments = [
            {"start": 1.0, "end": 5.0, "text": "First", "confidence": 0.95},
            {"start": 5.0, "end": 10.0, "text": "Second", "confidence": 0.92},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 10.0,
        }
        
        result = TranscriptFormatter.to_json(segments, metadata)
        parsed = json.loads(result)
        
        assert len(parsed["segments"]) == 2
        assert parsed["segments"][0]["text"] == "First"
        assert parsed["segments"][0]["confidence"] == 0.95
    
    def test_empty_segments_raises_error(self):
        """Test that empty segment list raises ValueError."""
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 5.0,
        }
        with pytest.raises(ValueError, match="empty"):
            TranscriptFormatter.to_json([], metadata)
    
    def test_missing_required_segment_field(self):
        """Test that missing segment field raises KeyError."""
        segments = [{"start": 1.0, "text": "Hello"}]  # missing 'end'
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 5.0,
        }
        with pytest.raises(KeyError):
            TranscriptFormatter.to_json(segments, metadata)
    
    def test_missing_required_metadata_field(self):
        """Test that missing metadata field raises KeyError."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            # missing 'language'
            "duration": 5.0,
        }
        with pytest.raises(KeyError, match="language"):
            TranscriptFormatter.to_json(segments, metadata)
    
    def test_invalid_metadata_type(self):
        """Test that invalid metadata type raises TypeError."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": "5.0",  # Should be numeric, not string
        }
        with pytest.raises(TypeError, match="duration"):
            TranscriptFormatter.to_json(segments, metadata)
    
    def test_json_is_valid(self):
        """Test that output is valid JSON."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 5.0,
        }
        
        result = TranscriptFormatter.to_json(segments, metadata)
        
        # Should not raise json.JSONDecodeError
        parsed = json.loads(result)
        assert parsed is not None
    
    def test_json_indentation(self):
        """Test that JSON is pretty-printed with 2-space indent."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 5.0,
        }
        
        result = TranscriptFormatter.to_json(segments, metadata)
        
        # Check that it has proper indentation (not minified)
        assert "  " in result  # Should have 2-space indentation
        assert "\n" in result  # Should be multi-line
    
    def test_special_characters_in_json(self):
        """Test that special characters are preserved in JSON."""
        segments = [
            {"start": 1.0, "end": 5.0, "text": "Café naïve 🎉"},
            {"start": 5.0, "end": 10.0, "text": "What's—that?"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 10.0,
        }
        
        result = TranscriptFormatter.to_json(segments, metadata)
        parsed = json.loads(result)
        
        assert "Café naïve 🎉" in parsed["segments"][0]["text"]
        assert "What's—that?" in parsed["segments"][1]["text"]
    
    def test_optional_confidence_field_preserved(self):
        """Test that optional confidence field is preserved."""
        segments = [
            {"start": 1.0, "end": 5.0, "text": "Hello", "confidence": 0.95},
            {"start": 5.0, "end": 10.0, "text": "World"},  # no confidence
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 10.0,
        }
        
        result = TranscriptFormatter.to_json(segments, metadata)
        parsed = json.loads(result)
        
        assert parsed["segments"][0]["confidence"] == 0.95
        assert "confidence" not in parsed["segments"][1]
    
    def test_invalid_engine_type(self):
        """Test that non-string engine raises TypeError."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        metadata = {
            "engine": 123,  # Should be string
            "model": "base",
            "language": "en",
            "duration": 5.0,
        }
        with pytest.raises(TypeError, match="engine"):
            TranscriptFormatter.to_json(segments, metadata)
    
    def test_invalid_model_type(self):
        """Test that non-string model raises TypeError."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        metadata = {
            "engine": "faster-whisper",
            "model": ["base"],  # Should be string
            "language": "en",
            "duration": 5.0,
        }
        with pytest.raises(TypeError, match="model"):
            TranscriptFormatter.to_json(segments, metadata)
    
    def test_invalid_language_type(self):
        """Test that non-string language raises TypeError."""
        segments = [{"start": 1.0, "end": 5.0, "text": "Hello"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": {"code": "en"},  # Should be string
            "duration": 5.0,
        }
        with pytest.raises(TypeError, match="language"):
            TranscriptFormatter.to_json(segments, metadata)
    
    def test_numeric_metadata_as_int(self):
        """Test that numeric metadata can be integer."""
        segments = [{"start": 1, "end": 5, "text": "Hello"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 5,  # integer, not float
        }
        
        result = TranscriptFormatter.to_json(segments, metadata)
        parsed = json.loads(result)
        
        assert parsed["metadata"]["duration"] == 5


# ============================================================================
# Integration Tests
# ============================================================================

class TestTranscriptFormatterIntegration:
    """Integration tests for multiple formatters together."""
    
    def test_all_formatters_with_same_segments(self):
        """Test that all formatters handle same segments consistently."""
        segments = [
            {"start": 1.0, "end": 5.0, "text": "First"},
            {"start": 5.0, "end": 10.0, "text": "Second"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 10.0,
        }
        
        # All should succeed without error
        txt = TranscriptFormatter.to_txt(segments)
        srt = TranscriptFormatter.to_srt(segments)
        json_str = TranscriptFormatter.to_json(segments, metadata)
        
        assert txt
        assert srt
        assert json_str
    
    def test_single_segment_all_formatters(self):
        """Test single segment with all formatters."""
        segment = {"start": 0.0, "end": 3.0, "text": "Test"}
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 3.0,
        }
        
        txt = TranscriptFormatter.to_txt([segment])
        srt = TranscriptFormatter.to_srt([segment])
        json_str = TranscriptFormatter.to_json([segment], metadata)
        
        # Verify expected formats
        assert "[00:00:00–00:00:03] Test" == txt
        assert "00:00:00,000 --> 00:00:03,000" in srt
        parsed = json.loads(json_str)
        assert parsed["segments"][0]["text"] == "Test"
    
    def test_large_segment_list(self):
        """Test with a large number of segments (100+)."""
        segments = [
            {"start": float(i), "end": float(i + 1), "text": f"Segment {i}"}
            for i in range(150)
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 150.0,
        }
        
        txt = TranscriptFormatter.to_txt(segments)
        srt = TranscriptFormatter.to_srt(segments)
        json_str = TranscriptFormatter.to_json(segments, metadata)
        
        # Verify all produced output
        assert len(txt.split("\n")) == 150
        assert "150\n" in srt  # Last sequence number should be 150
        parsed = json.loads(json_str)
        assert len(parsed["segments"]) == 150
    
    def test_edge_case_timestamps(self):
        """Test with edge case timestamps."""
        segments = [
            {"start": 0.001, "end": 0.050, "text": "Very short"},  # 49ms
            {"start": 0.05, "end": 0.1, "text": "Short"},  # 50ms
            {"start": 0.999, "end": 1.001, "text": "Across 1s"},  # ~2ms
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 1.001,
        }
        
        txt = TranscriptFormatter.to_txt(segments)
        srt = TranscriptFormatter.to_srt(segments)
        json_str = TranscriptFormatter.to_json(segments, metadata)
        
        # All should complete without error
        assert txt
        assert srt
        parsed = json.loads(json_str)
        assert len(parsed["segments"]) == 3
