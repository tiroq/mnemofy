"""End-to-end integration tests for complete transcription pipeline.

Tests the full workflow: input file → audio extraction → transcription → 
multiple output formats (TXT, SRT, JSON, notes MD).
"""

import json
import pytest

from mnemofy.output_manager import OutputManager
from mnemofy.formatters import TranscriptFormatter
from mnemofy.notes import StructuredNotesGenerator


class TestCompleteProcessingPipeline:
    """Test full pipeline from input to all outputs."""

    def test_pipeline_generates_all_output_files(self, tmp_path):
        """Test that complete pipeline generates all 5 output files."""
        # Setup
        input_file = tmp_path / "test.wav"
        input_file.write_text("dummy audio")
        
        manager = OutputManager(input_file)
        
        # Simulate transcription segments
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Hello world"},
            {"start": 5.0, "end": 10.0, "text": "This is a test"},
            {"start": 10.0, "end": 30.0, "text": "Meeting notes generation"},
        ]
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 30.0,
        }
        
        # Generate all formats
        txt_content = TranscriptFormatter.to_txt(segments)
        srt_content = TranscriptFormatter.to_srt(segments)
        json_content = TranscriptFormatter.to_json(segments, metadata)
        
        # Write transcript files
        paths = manager.get_transcript_paths()
        paths["txt"].write_text(txt_content)
        paths["srt"].write_text(srt_content)
        paths["json"].write_text(json_content)
        
        # Generate notes
        notes_gen = StructuredNotesGenerator(mode="basic")
        notes_content = notes_gen.generate(segments, metadata)
        manager.get_notes_path().write_text(notes_content)
        
        # Verify all files exist
        assert paths["txt"].exists()
        assert paths["srt"].exists()
        assert paths["json"].exists()
        assert manager.get_notes_path().exists()
        
        # Verify content is non-empty
        assert len(txt_content) > 0
        assert len(srt_content) > 0
        assert len(json_content) > 0
        assert len(notes_content) > 0

    def test_pipeline_with_outdir_creates_directory(self, tmp_path):
        """Test that pipeline creates outdir if it doesn't exist."""
        input_file = tmp_path / "input" / "test.wav"
        input_file.parent.mkdir(parents=True)
        input_file.write_text("dummy")
        
        outdir = tmp_path / "outputs"
        assert not outdir.exists()
        
        # Create OutputManager with non-existent outdir
        manager = OutputManager(input_file, outdir=outdir)
        
        # outdir should be created
        assert manager.outdir.exists()
        assert manager.outdir.is_dir()

    def test_txt_format_is_parseable(self, tmp_path):
        """Test that generated TXT format can be parsed."""
        segments = [
            {"start": 0.0, "end": 5.5, "text": "First segment"},
            {"start": 5.5, "end": 12.0, "text": "Second segment"},
        ]
        
        txt = TranscriptFormatter.to_txt(segments)
        
        # Should contain timestamp markers (with hours)
        assert "[00:00:00–00:00:05]" in txt
        assert "[00:00:05–00:00:12]" in txt
        
        # Should contain text
        assert "First segment" in txt
        assert "Second segment" in txt
        
        # Should have newlines
        lines = txt.strip().split('\n')
        assert len(lines) == 2

    def test_srt_format_is_valid(self, tmp_path):
        """Test that generated SRT format follows SubRip spec."""
        segments = [
            {"start": 0.0, "end": 5.5, "text": "First subtitle"},
            {"start": 5.5, "end": 10.0, "text": "Second subtitle"},
        ]
        
        srt = TranscriptFormatter.to_srt(segments)
        
        # Should have sequence numbers
        assert "1\n" in srt
        assert "2\n" in srt
        
        # Should have timing lines with commas for milliseconds
        assert "00:00:00,000 --> 00:00:05,500" in srt
        assert "00:00:05,500 --> 00:00:10,000" in srt
        
        # Should have text
        assert "First subtitle" in srt
        assert "Second subtitle" in srt
        
        # Should have blank lines between entries
        assert "\n\n" in srt

    def test_json_format_is_parseable(self, tmp_path):
        """Test that generated JSON can be parsed."""
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Test"},
        ]
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 5.0,
        }
        
        json_str = TranscriptFormatter.to_json(segments, metadata)
        
        # Should be valid JSON
        data = json.loads(json_str)
        
        # Should have expected structure
        assert "schema_version" in data
        assert "metadata" in data
        assert "segments" in data
        
        # Metadata should match
        assert data["metadata"]["engine"] == "faster-whisper"
        assert data["metadata"]["model"] == "base"
        assert data["metadata"]["language"] == "en"
        
        # Segments should match
        assert len(data["segments"]) == 1
        assert data["segments"][0]["text"] == "Test"

    def test_notes_contain_all_sections(self, tmp_path):
        """Test that generated notes contain all 7 sections."""
        segments = [
            {"start": 0.0, "end": 60.0, "text": "We decided to proceed with the plan"},
        ]
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60.0,
        }
        
        gen = StructuredNotesGenerator(mode="basic")
        notes = gen.generate(segments, metadata)
        
        # Should have all 7 sections
        assert "# Meeting Notes:" in notes
        assert "**Date**:" in notes
        assert "**Language**:" in notes
        assert "## Topics" in notes
        assert "## Decisions" in notes
        assert "## Action Items" in notes
        assert "## Concrete Mentions" in notes
        assert "## Risks & Open Questions" in notes
        assert "## Transcript Files" in notes


class TestFileNamingConventions:
    """Test that output files follow naming conventions."""

    def test_audio_file_naming(self, tmp_path):
        """Test .mnemofy.wav naming convention."""
        input_file = tmp_path / "meeting.mp4"
        input_file.write_text("dummy")
        
        manager = OutputManager(input_file)
        audio_path = manager.get_audio_path()
        
        assert audio_path.name == "meeting.mnemofy.wav"
        assert audio_path.parent == tmp_path

    def test_transcript_file_naming(self, tmp_path):
        """Test transcript naming conventions."""
        input_file = tmp_path / "presentation.mkv"
        input_file.write_text("dummy")
        
        manager = OutputManager(input_file)
        paths = manager.get_transcript_paths()
        
        assert paths["txt"].name == "presentation.transcript.txt"
        assert paths["srt"].name == "presentation.transcript.srt"
        assert paths["json"].name == "presentation.transcript.json"

    def test_notes_file_naming(self, tmp_path):
        """Test notes file naming convention."""
        input_file = tmp_path / "lecture.wav"
        input_file.write_text("dummy")
        
        manager = OutputManager(input_file)
        notes_path = manager.get_notes_path()
        
        assert notes_path.name == "lecture.notes.md"


class TestLongTranscriptHandling:
    """Test handling of long transcripts (>1 hour)."""

    def test_long_transcript_txt_format(self):
        """Test TXT format with transcript >1 hour."""
        # Create segments spanning 90 minutes
        segments = [
            {"start": 0.0, "end": 60.0, "text": "First minute"},
            {"start": 3600.0, "end": 3660.0, "text": "At 1 hour mark"},
            {"start": 5400.0, "end": 5460.0, "text": "At 90 minute mark"},
        ]
        
        txt = TranscriptFormatter.to_txt(segments)
        
        # Should handle hour timestamps properly
        assert "[00:00:00–00:01:00]" in txt
        assert "[01:00:00–01:01:00]" in txt
        assert "[01:30:00–01:31:00]" in txt

    def test_long_transcript_srt_format(self):
        """Test SRT format with transcript >1 hour."""
        segments = [
            {"start": 3600.5, "end": 3605.0, "text": "One hour mark"},
        ]
        
        srt = TranscriptFormatter.to_srt(segments)
        
        # Should have proper hour formatting
        assert "01:00:00,500 --> 01:00:05,000" in srt

    def test_long_transcript_notes_generation(self):
        """Test notes generation with long transcript."""
        # Create 2 hour transcript
        segments = []
        for i in range(120):  # 2 hours, 1-minute segments
            segments.append({
                "start": i * 60.0,
                "end": (i + 1) * 60.0,
                "text": f"Segment {i}"
            })
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 7200.0,
        }
        
        gen = StructuredNotesGenerator(mode="basic")
        notes = gen.generate(segments, metadata)
        
        # Should handle long duration
        assert "120m 0s" in notes or "2h" in notes.lower()
        assert len(notes) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_segments_list(self):
        """Test handling of empty segments."""
        segments = []
        # Empty segments should raise ValueError
        with pytest.raises(ValueError, match="Cannot format empty segment list"):
            TranscriptFormatter.to_txt(segments)

    def test_very_short_transcript_notes(self):
        """Test notes generation with transcript < 30 seconds."""
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Short"}
        ]
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 5.0,
        }
        
        gen = StructuredNotesGenerator(mode="basic")
        
        # Should raise ValueError for < 30 seconds
        with pytest.raises(ValueError, match="minimum 30 seconds required"):
            gen.generate(segments, metadata)

    def test_special_characters_in_filename(self, tmp_path):
        """Test handling of special characters in file names."""
        # Create file with special chars
        input_file = tmp_path / "test file (2024).mp4"
        input_file.write_text("dummy")
        
        manager = OutputManager(input_file)
        
        # Should preserve basename
        assert "test file (2024)" in manager.basename

    def test_unicode_text_in_segments(self):
        """Test handling of unicode characters in transcript."""
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Hello 世界 мир "},
        ]
        
        # Should handle unicode in all formats
        txt = TranscriptFormatter.to_txt(segments)
        assert "世界" in txt
        assert "мир" in txt
        
        srt = TranscriptFormatter.to_srt(segments)
        assert "世界" in srt
        
        metadata = {"engine": "test", "model": "test", "language": "multi", "duration": 5.0}
        json_str = TranscriptFormatter.to_json(segments, metadata)
        data = json.loads(json_str)
        assert "世界" in data["segments"][0]["text"]

    def test_very_long_single_segment(self):
        """Test handling of very long single segment text."""
        long_text = "This is a very long segment. " * 100  # 300+ words
        segments = [
            {"start": 0.0, "end": 300.0, "text": long_text}
        ]
        
        # All formats should handle long text
        txt = TranscriptFormatter.to_txt(segments)
        assert len(txt) > 2500
        
        srt = TranscriptFormatter.to_srt(segments)
        assert long_text in srt
        
        metadata = {"engine": "test", "model": "test", "language": "en", "duration": 300.0}
        json_str = TranscriptFormatter.to_json(segments, metadata)
        data = json.loads(json_str)
        assert len(data["segments"][0]["text"]) > 2500


class TestBackwardCompatibility:
    """Test backward compatibility with existing workflows."""

    def test_output_manager_without_outdir(self, tmp_path):
        """Test OutputManager with outdir=None (default behavior)."""
        input_file = tmp_path / "test.wav"
        input_file.write_text("dummy")
        
        manager = OutputManager(input_file, outdir=None)
        
        # Should default to input file's parent directory
        assert manager.outdir == tmp_path

    def test_formatters_with_minimal_metadata(self):
        """Test formatters with minimal required metadata."""
        segments = [{"start": 0.0, "end": 5.0, "text": "Test"}]
        
        # Minimal metadata
        metadata = {
            "engine": "test",
            "model": "test",
            "language": "en",
            "duration": 5.0,
        }
        
        # Should work without errors
        json_str = TranscriptFormatter.to_json(segments, metadata)
        data = json.loads(json_str)
        
        assert data["metadata"]["engine"] == "test"
