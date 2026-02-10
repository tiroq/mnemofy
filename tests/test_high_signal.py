"""Tests for high-signal segment extraction."""

import pytest
from mnemofy.classifier import extract_high_signal_segments


class TestHighSignalExtraction:
    """Test extraction of high-value transcript segments."""
    
    def test_extract_decision_markers(self):
        """Should extract segments containing decision markers."""
        transcript = """
        We discussed various options for the database.
        After careful consideration, we decided to use PostgreSQL because
        it handles our concurrency requirements better. This is a final decision.
        Let's move forward with the implementation.
        """
        
        segments = extract_high_signal_segments(transcript, context_words=10)
        
        assert len(segments) > 0
        # Should capture "decided" marker with context
        assert any("decided to use PostgreSQL" in seg for seg in segments)
    
    def test_extract_action_markers(self):
        """Should extract segments with action commitments."""
        transcript = """
        The meeting covered several topics.
        Alice will implement the new feature by Friday.
        Bob must review the code before deployment.
        We should also update the documentation.
        """
        
        segments = extract_high_signal_segments(transcript, context_words=15)
        
        assert len(segments) >= 2
        # Should capture "will", "must", "should" markers
        assert any("will implement" in seg for seg in segments)
        assert any("must review" in seg for seg in segments)
    
    def test_extract_incident_markers(self):
        """Should extract segments related to problems and incidents."""
        transcript = """
        Everything was running smoothly yesterday.
        This morning we had a critical incident with the payment service.
        The bug was causing transactions to fail intermittently.
        We resolved the issue by rolling back the latest deployment.
        """
        
        segments = extract_high_signal_segments(transcript, context_words=12)
        
        assert len(segments) >= 2
        assert any("incident" in seg.lower() for seg in segments)
        assert any("resolved" in seg.lower() for seg in segments)
    
    def test_context_window_size(self):
        """Should respect context_words parameter."""
        transcript = " ".join([f"word{i}" for i in range(200)])
        transcript += " decided "  # Add decision marker
        transcript += " ".join([f"word{i}" for i in range(200, 400)])
        
        # Extract with 20-word context
        segments = extract_high_signal_segments(transcript, context_words=20)
        
        assert len(segments) > 0
        first_segment = segments[0]
        word_count = len(first_segment.split())
        # Should be roughly 40 words (20 before + marker + 20 after)
        assert 35 <= word_count <= 45  # Allow some margin for word boundaries
    
    def test_max_segments_limit(self):
        """Should respect max_segments parameter."""
        # Transcript with many decision markers
        transcript = " ".join([
            f"Section {i}. We decided to do X. " for i in range(20)
        ])
        
        segments = extract_high_signal_segments(transcript, max_segments=5)
        
        assert len(segments) <= 5
    
    def test_no_duplicate_overlapping_segments(self):
        """Should avoid extracting overlapping segments."""
        # Two decision markers very close together
        transcript = "We decided to use PostgreSQL and we also decided to use Redis"
        
        segments = extract_high_signal_segments(transcript, context_words=10)
        
        # Should extract only one segment since markers are within context window
        assert len(segments) == 1
    
    def test_empty_transcript(self):
        """Should handle empty transcript gracefully."""
        segments = extract_high_signal_segments("")
        assert segments == []
    
    def test_no_markers_found(self):
        """Should return empty list when no markers present."""
        transcript = """
        This is a simple conversation about weather.
        The temperature is nice today.
        Everyone is enjoying the sunshine.
        """
        
        segments = extract_high_signal_segments(transcript)
        
        assert segments == []
    
    def test_case_insensitive_matching(self):
        """Should detect markers regardless of case."""
        transcript = "We DECIDED to USE the new FRAMEWORK because it WILL help us."
        
        segments = extract_high_signal_segments(transcript, context_words=5)
        
        assert len(segments) > 0
        assert any("DECIDED" in seg for seg in segments)
    
    def test_commitment_markers(self):
        """Should extract commitment and agreement markers."""
        transcript = """
        After the discussion, we agreed to move forward with the plan.
        The team committed to delivering by next week.
        Everyone confirmed the timeline is realistic.
        """
        
        segments = extract_high_signal_segments(transcript, context_words=10)
        
        assert len(segments) >= 2
        assert any("agreed to" in seg.lower() for seg in segments)
        assert any("committed to" in seg.lower() for seg in segments)
    
    def test_planning_markers(self):
        """Should extract "going to" and "let's" markers."""
        transcript = """
        For the next sprint, we're going to focus on performance.
        Let's use React for the frontend framework.
        This will help us move faster.
        """
        
        segments = extract_high_signal_segments(transcript, context_words=10)
        
        assert len(segments) >= 2
        assert any("going to" in seg.lower() for seg in segments)
        assert any("let's use" in seg.lower() for seg in segments)
    
    def test_outcome_markers(self):
        """Should extract resolution and completion markers."""
        transcript = """
        The feature has been completed and deployed to production.
        We fixed the authentication bug yesterday.
        The incident was resolved within 2 hours.
        All tests are now passing.
        """
        
        segments = extract_high_signal_segments(transcript, context_words=10)
        
        assert len(segments) >= 2
        assert any("completed" in seg.lower() for seg in segments)
        assert any("resolved" in seg.lower() or "fixed" in seg.lower() for seg in segments)
    
    def test_multiple_marker_types_in_one_segment(self):
        """Should handle segments with multiple marker types."""
        transcript = """
        After analyzing the issue, we decided that we must fix this blocker
        immediately and Bob will handle the resolution.
        """
        
        segments = extract_high_signal_segments(transcript, context_words=20)
        
        # Should extract segment containing multiple markers
        assert len(segments) > 0
        combined_segment = " ".join(segments)
        assert "decided" in combined_segment
        assert "will" in combined_segment
        assert "blocker" in combined_segment
