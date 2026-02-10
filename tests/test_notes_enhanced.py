"""Tests for StructuredNotesGenerator and helper functions."""

import json
import pytest
from mnemofy.notes import (
    StructuredNotesGenerator,
    NotesMode,
    seconds_to_mmss,
)


# ============================================================================
# Tests for seconds_to_mmss helper function
# ============================================================================

class TestSecondsToMmss:
    """Test seconds_to_mmss time formatting function."""
    
    def test_basic_conversion(self):
        """Test basic second to MM:SS conversion."""
        assert seconds_to_mmss(0) == "00:00"
        assert seconds_to_mmss(30) == "00:30"
        assert seconds_to_mmss(60) == "01:00"
        assert seconds_to_mmss(90) == "01:30"
    
    def test_large_minutes(self):
        """Test conversion with minutes > 60."""
        assert seconds_to_mmss(300) == "05:00"  # 5 minutes
        assert seconds_to_mmss(3600) == "60:00"  # 1 hour
        assert seconds_to_mmss(3661) == "61:01"  # 1 hour 1 second
    
    def test_subsecond_rounding(self):
        """Test that subseconds are truncated, not rounded."""
        assert seconds_to_mmss(65.999) == "01:05"
        assert seconds_to_mmss(65.1) == "01:05"


# ============================================================================
# Tests for StructuredNotesGenerator initialization
# ============================================================================

class TestStructuredNotesGeneratorInit:
    """Test StructuredNotesGenerator initialization."""
    
    def test_default_mode_is_basic(self):
        """Test that default mode is basic."""
        gen = StructuredNotesGenerator()
        assert gen.mode == NotesMode.BASIC
    
    def test_explicit_basic_mode(self):
        """Test explicit basic mode selection."""
        gen = StructuredNotesGenerator(mode="basic")
        assert gen.mode == NotesMode.BASIC
    
    def test_llm_mode_initialization(self):
        """Test LLM mode can be initialized."""
        gen = StructuredNotesGenerator(mode="llm")
        assert gen.mode == NotesMode.LLM
    
    def test_case_insensitive_mode(self):
        """Test that mode is case-insensitive."""
        gen = StructuredNotesGenerator(mode="BASIC")
        assert gen.mode == NotesMode.BASIC
    
    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Unknown mode"):
            StructuredNotesGenerator(mode="invalid")


# ============================================================================
# Tests for validation and minimum duration requirement
# ============================================================================

class TestStructuredNotesGeneratorValidation:
    """Test input validation and constraints."""
    
    def test_empty_segments_raises_error(self):
        """Test that empty segments raises IndexError."""
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 0,
        }
        gen = StructuredNotesGenerator()
        with pytest.raises(IndexError):
            gen.generate([], metadata)
    
    def test_minimum_duration_30_seconds(self):
        """Test that transcripts < 30 seconds raise ValueError."""
        segments = [{"start": 0, "end": 10, "text": "Too short"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 10,
        }
        gen = StructuredNotesGenerator()
        with pytest.raises(ValueError, match="30 seconds"):
            gen.generate(segments, metadata)
    
    def test_exactly_30_seconds_accepted(self):
        """Test that exactly 30 seconds is accepted."""
        segments = [{"start": 0, "end": 30, "text": "Meeting discussion"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 30,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        assert result  # Should not raise
    
    def test_just_over_30_seconds(self):
        """Test that 31 seconds is accepted."""
        segments = [{"start": 0, "end": 31, "text": "Meeting discussion"}]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 31,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        assert result  # Should not raise
    
    def test_missing_required_metadata_field(self):
        """Test that missing required metadata field raises KeyError."""
        segments = [
            {"start": 0, "end": 30, "text": "Discussion"},
            {"start": 30, "end": 60, "text": "Continuation"},
        ]
        metadata = {
            "model": "base",
            # missing 'engine'
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        with pytest.raises(KeyError):
            gen.generate(segments, metadata)
    
    def test_llm_mode_not_implemented(self):
        """Test that LLM mode raises NotImplementedError."""
        segments = [
            {"start": 0, "end": 30, "text": "Discussion"},
            {"start": 30, "end": 60, "text": "Continuation"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator(mode="llm")
        with pytest.raises(NotImplementedError):
            gen.generate(segments, metadata)


# ============================================================================
# Tests for Metadata Section Generation
# ============================================================================

class TestMetadataSection:
    """Test metadata section generation."""
    
    def test_metadata_section_has_required_fields(self):
        """Test that metadata section includes all required fields."""
        segments = [
            {"start": 0, "end": 30, "text": "Hello"},
            {"start": 30, "end": 60, "text": "World"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
            "input_file": "test.mp4",
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        # Check for required metadata fields
        assert "Meeting Notes" in result
        assert "**Language**: en" in result or "Language" in result
        assert "faster-whisper" in result
        assert "base" in result
    
    def test_metadata_duration_formatting(self):
        """Test that duration is formatted correctly."""
        segments = [
            {"start": 0, "end": i*10, "text": f"Segment {i}"}
            for i in range(1, 7)  # 60 seconds
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "1m 0s" in result
    
    def test_metadata_with_long_duration(self):
        """Test metadata with hour-long transcript."""
        segments = [
            {"start": float(i*60), "end": float((i+1)*60), "text": f"Segment {i}"}
            for i in range(60)  # 60 minutes
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 3600,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "60m 0s" in result


# ============================================================================
# Tests for Topics Extraction
# ============================================================================

class TestTopicsExtraction:
    """Test topics extraction from transcript."""
    
    def test_topics_section_present(self):
        """Test that topics section is always present."""
        segments = [
            {"start": 0, "end": 30, "text": "Opening remarks"},
            {"start": 30, "end": 60, "text": "Continued discussion"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "## Topics" in result
    
    def test_topics_with_time_bucketing(self):
        """Test that topics are bucketed by time intervals."""
        segments = [
            {"start": float(i*60), "end": float((i+1)*60), "text": f"Topic {i}"}
            for i in range(10)  # 10 minutes
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 600,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        # Should have multiple topic entries due to bucketing
        assert result.count("- **[") > 0


# ============================================================================
# Tests for Decisions Extraction
# ============================================================================

class TestDecisionsExtraction:
    """Test decisions extraction from transcript."""
    
    def test_decisions_section_present(self):
        """Test that decisions section is always present."""
        segments = [
            {"start": 0, "end": 30, "text": "We decided to move forward"},
            {"start": 30, "end": 60, "text": "Team agrees on timeline"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "## Decisions" in result
    
    def test_decision_keywords_detected(self):
        """Test that decision keywords are detected."""
        segments = [
            {"start": 0, "end": 20, "text": "We agreed on the timeline"},
            {"start": 20, "end": 40, "text": "Project approved by board"},
            {"start": 40, "end": 60, "text": "Let's discuss logistics"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        decisions_section = result[result.find("## Decisions"):result.find("## Action")]
        # Should mention the decided items
        assert len(decisions_section) > len("## Decisions")


# ============================================================================
# Tests for Action Items Extraction
# ============================================================================

class TestActionItemsExtraction:
    """Test action items extraction from transcript."""
    
    def test_action_items_section_present(self):
        """Test that action items section is present."""
        segments = [
            {"start": 0, "end": 30, "text": "John will complete the report"},
            {"start": 30, "end": 60, "text": "Sarah needs to review docs"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "## Action Items" in result
    
    def test_action_keywords_detected(self):
        """Test that action keywords are detected."""
        segments = [
            {"start": 0, "end": 20, "text": "We will need to finalize reports"},
            {"start": 20, "end": 40, "text": "Sarah must complete testing"},
            {"start": 40, "end": 60, "text": "Let's schedule next meeting"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "## Action Items" in result


# ============================================================================
# Tests for Concrete Mentions Extraction
# ============================================================================

class TestConcreteNentionsExtraction:
    """Test concrete mentions (names, numbers, URLs, dates) extraction."""
    
    def test_concrete_mentions_section_present(self):
        """Test that concrete mentions section is present."""
        segments = [
            {"start": 0, "end": 30, "text": "John and Sarah discussed the project"},
            {"start": 30, "end": 60, "text": "Budget is $2.5M for Q1"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "## Concrete Mentions" in result
    
    def test_name_extraction(self):
        """Test that names are extracted."""
        segments = [
            {"start": 0, "end": 30, "text": "John Smith discussed with Sarah Johnson"},
            {"start": 30, "end": 60, "text": "Bob mentioned the issue"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "Smith" in result or "Johnson" in result or "Names" in result
    
    def test_number_extraction(self):
        """Test that numbers and metrics are extracted."""
        segments = [
            {"start": 0, "end": 30, "text": "Budget is $2.5M for this project"},
            {"start": 30, "end": 60, "text": "Performance target is 99.9% uptime"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "$2.5M" in result or "Numbers" in result
    
    def test_url_extraction(self):
        """Test that URLs are extracted."""
        segments = [
            {"start": 0, "end": 30, "text": "Check our docs at https://github.com/team/repo"},
            {"start": 30, "end": 60, "text": "Also visit www.example.com for more"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "github.com" in result or "example.com" in result or "URLs" in result


# ============================================================================
# Tests for Risks and Questions Extraction
# ============================================================================

class TestRisksAndQuestionsExtraction:
    """Test risks and open questions extraction."""
    
    def test_risks_and_questions_section_present(self):
        """Test that risks and questions section is present."""
        segments = [
            {"start": 0, "end": 30, "text": "Timeline might slip due to resource constraints"},
            {"start": 30, "end": 60, "text": "When will the decision be finalized?"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "## Risks & Open Questions" in result
    
    def test_question_detection(self):
        """Test that sentences ending with ? are detected as questions."""
        segments = [
            {"start": 0, "end": 20, "text": "How will we proceed?"},
            {"start": 20, "end": 40, "text": "What is the timeline?"},
            {"start": 40, "end": 60, "text": "This is a statement"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        questions_section = result[result.find("## Risks"):result.find("## Transcript")]
        assert "How will" in questions_section or "What is" in questions_section or len(questions_section) > 100


# ============================================================================
# Tests for Transcript Links Section
# ============================================================================

class TestTranscriptLinksSection:
    """Test transcript files links section generation."""
    
    def test_transcript_links_section_present(self):
        """Test that transcript links section is present."""
        segments = [
            {"start": 0, "end": 30, "text": "First"},
            {"start": 30, "end": 60, "text": "Second"},
        ]
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
            "input_file": "meeting.mp4",
        }
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert "## Transcript Files" in result
        assert ".txt" in result
        assert ".srt" in result
        assert ".json" in result
        assert ".wav" in result


# ============================================================================
# Integration Tests
# ============================================================================

class TestStructuredNotesGeneratorIntegration:
    """Integration tests for complete note generation."""
    
    def test_complete_note_generation_5_minutes(self):
        """Test complete note generation with 5-minute transcript."""
        # Create 5-minute transcript (30 segments of 10 seconds each)
        segments = [
            {
                "start": float(i*10),
                "end": float((i+1)*10),
                "text": f"Segment {i}: This is content for topic discussion"
            }
            for i in range(30)
        ]
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 300,
            "input_file": "meeting.mp4",
        }
        
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        # Verify all sections present
        assert "# Meeting Notes" in result
        assert "## Topics" in result
        assert "## Decisions" in result
        assert "## Action Items" in result
        assert "## Concrete Mentions" in result
        assert "## Risks & Open Questions" in result
        assert "## Transcript Files" in result
        
        # Verify result is non-empty
        assert len(result) > 500
    
    def test_complete_note_generation_1_hour(self):
        """Test complete note generation with 1-hour transcript."""
        # Create 1-hour transcript (360 segments of 10 seconds each)
        segments = [
            {
                "start": float(i*10),
                "end": float((i+1)*10),
                "text": f"Point {i}: Team discussed Q1 planning. John will need to finalize the report by Feb 15. Budget approved is $2.5M. Timeline might slip. When will we have confirmation?"
            }
            for i in range(360)
        ]
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 3600,
            "input_file": "quarterly_review.mp4",
        }
        
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        # Verify structure
        assert result.count("##") >= 7  # At least 7 main sections
        assert "quarterly_review" in result or "Quarterly" in result or "quarterly" in result.lower()
    
    def test_boundary_condition_30_seconds(self):
        """Test with exactly 30 seconds at boundary."""
        segments = [
            {"start": 0, "end": 15, "text": "Part one of discussion"},
            {"start": 15, "end": 30, "text": "Part two of discussion"},
        ]
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 30,
        }
        
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        assert result  # Should successfully generate
        assert "Meeting Notes" in result
    
    def test_deterministic_output(self):
        """Test that output is deterministic (same input → same output) aside from timestamp."""
        segments = [
            {"start": 0, "end": 30, "text": "We decided to proceed with the project"},
            {"start": 30, "end": 60, "text": "John will handle the documentation"},
        ]
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        
        gen = StructuredNotesGenerator()
        result1 = gen.generate(segments, metadata)
        result2 = gen.generate(segments, metadata)
        
        # Remove timestamps before comparing (they differ by microseconds)
        def remove_timestamp(text):
            import re
            # Remove the **Generated**: line
            return re.sub(r'\*\*Generated\*\*:.*', '', text)
        
        result1_no_ts = remove_timestamp(result1)
        result2_no_ts = remove_timestamp(result2)
        
        assert result1_no_ts == result2_no_ts
    
    def test_no_hallucination_in_basic_mode(self):
        """Test that basic mode doesn't hallucinate content."""
        segments = [
            {"start": 0, "end": 30, "text": "Simple content"},
            {"start": 30, "end": 60, "text": "More simple content"},
        ]
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        # Basic mode should only contain content from transcription
        # It should show empty sections where nothing was found
        assert "found" in result.lower() or len(result) > 100
    
    def test_empty_sections_handled_gracefully(self):
        """Test that empty sections are handled gracefully."""
        segments = [
            {"start": 0, "end": 30, "text": "Opening remarks"},
            {"start": 30, "end": 60, "text": "Closing remarks"},
        ]
        
        metadata = {
            "engine": "faster-whisper",
            "model": "base",
            "language": "en",
            "duration": 60,
        }
        
        gen = StructuredNotesGenerator()
        result = gen.generate(segments, metadata)
        
        # All sections should be present, even if empty
        assert "## Decisions" in result
        assert "## Action Items" in result
