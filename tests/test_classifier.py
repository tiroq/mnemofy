"""Tests for meeting type classification."""

import pytest
from mnemofy.classifier import (
    MeetingType,
    HeuristicClassifier,
    ClassificationResult,
    TranscriptReference,
    GroundedItem,
)


class TestMeetingTypeEnum:
    """Test MeetingType enumeration."""
    
    def test_all_meeting_types_exist(self):
        """Test that all 9 meeting types are defined."""
        expected_types = {
            "status", "planning", "design", "demo", "talk",
            "incident", "discovery", "oneonone", "brainstorm"
        }
        actual_types = {mt.value for mt in MeetingType}
        assert actual_types == expected_types
    
    def test_meeting_type_value_access(self):
        """Test accessing meeting type by value."""
        assert MeetingType.STATUS.value == "status"
        assert MeetingType.PLANNING.value == "planning"
        assert MeetingType.DESIGN.value == "design"


class TestHeuristicClassifier:
    """Test heuristic meeting type classifier."""
    
    def test_classifier_initialization(self):
        """Test classifier can be initialized."""
        classifier = HeuristicClassifier()
        assert classifier is not None
        assert classifier.keywords is not None
    
    def test_status_meeting_detection(self):
        """Test detection of status meetings."""
        transcript = """
        Good morning everyone. Let's do our daily standup.
        Yesterday I finished the authentication module.
        Today I'm working on the API integration.
        I'm blocked on the database migration - need help from DevOps.
        Sarah, what's your status? I completed the UI mockups yesterday.
        Today I'm implementing the new dashboard. No blockers on my end.
        John, your update? In progress on the testing framework.
        Yesterday I set up CI/CD pipeline, today continuing tests.
        My blocker is the test data - waiting for the data team.
        """
        
        classifier = HeuristicClassifier()
        result = classifier.detect_meeting_type(transcript)
        
        assert result.detected_type == MeetingType.STATUS
        assert result.confidence > 0.5
        assert result.engine == "heuristic"
        assert len(result.evidence) > 0
    
    def test_planning_meeting_detection(self):
        """Test detection of planning meetings."""
        transcript = """
        Let's plan the next sprint. We need to prioritize the backlog.
        The roadmap shows we have three milestones this quarter.
        We need to estimate story points for each task.
        What's our team velocity? Can we commit to these deadlines?
        """
        
        classifier = HeuristicClassifier()
        result = classifier.detect_meeting_type(transcript)
        
        assert result.detected_type == MeetingType.PLANNING
        assert result.confidence > 0.5
        assert result.engine == "heuristic"
    
    def test_design_meeting_detection(self):
        """Test detection of design meetings."""
        transcript = """
        Let's discuss the architecture for the new microservice.
        We need to evaluate the trade-offs between REST and GraphQL.
        The data model should have these components.
        What design pattern should we use here?
        Performance and scalability are key concerns.
        """
        
        classifier = HeuristicClassifier()
        result = classifier.detect_meeting_type(transcript)
        
        assert result.detected_type == MeetingType.DESIGN
        assert result.confidence > 0.5
    
    def test_demo_meeting_detection(self):
        """Test detection of demo meetings."""
        transcript = """
        Thanks for joining the demo today.
        Let me show you the new features we've built.
        As you can see on the screen, when you click here.
        This is how the feature works. Pretty cool, right?
        What feedback do you have? Any questions?
        """
        
        classifier = HeuristicClassifier()
        result = classifier.detect_meeting_type(transcript)
        
        assert result.detected_type == MeetingType.DEMO
        assert result.confidence > 0.5
    
    def test_incident_meeting_detection(self):
        """Test detection of incident response meetings."""
        transcript = """
        We have a critical incident. The service is down.
        Let's investigate the root cause. Check the error logs.
        We need to rollback the deployment immediately.
        What's the mitigation plan? How do we restore service?
        """
        
        classifier = HeuristicClassifier()
        result = classifier.detect_meeting_type(transcript)
        
        assert result.detected_type == MeetingType.INCIDENT
        assert result.confidence > 0.5
    
    def test_brainstorm_meeting_detection(self):
        """Test detection of brainstorm sessions."""
        transcript = """
        Let's brainstorm ideas for the new feature.
        What if we tried a completely different approach?
        Here's a crazy idea - maybe we could use AI.
        No bad ideas, just throw out whatever comes to mind.
        That's interesting, let's build on that concept.
        """
        
        classifier = HeuristicClassifier()
        result = classifier.detect_meeting_type(transcript)
        
        assert result.detected_type == MeetingType.BRAINSTORM
        assert result.confidence > 0.5
    
    def test_empty_transcript_fallback(self):
        """Test that empty transcript falls back to TALK with zero confidence."""
        classifier = HeuristicClassifier()
        result = classifier.detect_meeting_type("")
        
        assert result.detected_type == MeetingType.TALK
        assert result.confidence == 0.0
    
    def test_confidence_scoring(self):
        """Test confidence scoring mechanism."""
        # Strong indicators should yield high confidence
        strong_transcript = """
        Daily standup. Yesterday I worked on X. Today I'll do Y.
        I'm blocked on Z. Need help with the sprint backlog.
        What's the status of the release?
        """
        
        classifier = HeuristicClassifier()
        result = classifier.detect_meeting_type(strong_transcript)
        
        assert result.confidence > 0.6  # High confidence threshold
    
    def test_secondary_types_ranking(self):
        """Test that secondary types are ranked correctly."""
        classifier = HeuristicClassifier()
        result = classifier.detect_meeting_type("status update planning roadmap")
        
        assert len(result.secondary_types) > 0
        assert len(result.secondary_types) <= 5  # Top 5 alternatives
        
        # Secondary types should have lower scores than primary
        if result.secondary_types:
            assert result.secondary_types[0][1] < result.confidence


class TestTranscriptReference:
    """Test TranscriptReference dataclass."""
    
    def test_creation(self):
        """Test creating a transcript reference."""
        ref = TranscriptReference(
            reference_id="abc123",
            start_time=10.5,
            end_time=15.3,
            speaker="Alice",
            text_snippet="This is a test"
        )
        
        assert ref.reference_id == "abc123"
        assert ref.start_time == 10.5
        assert ref.end_time == 15.3
        assert ref.speaker == "Alice"
        assert ref.text_snippet == "This is a test"


class TestGroundedItem:
    """Test GroundedItem dataclass."""
    
    def test_creation_with_defaults(self):
        """Test creating grounded item with default values."""
        item = GroundedItem(
            text="We decided to use Python",
            status="confirmed",
            reason=None
        )
        
        assert item.text == "We decided to use Python"
        assert item.status == "confirmed"
        assert item.reason is None
        assert item.references == []
        assert item.item_type == "general"
        assert item.metadata == {}
    
    def test_creation_with_references(self):
        """Test creating grounded item with transcript references."""
        ref = TranscriptReference(
            reference_id="xyz",
            start_time=30.0,
            end_time=35.0,
            speaker="Bob",
            text_snippet="Python is the best choice"
        )
        
        item = GroundedItem(
            text="Use Python for the backend",
            status="confirmed",
            reason=None,
            references=[ref],
            item_type="decision"
        )
        
        assert len(item.references) == 1
        assert item.references[0].speaker == "Bob"
        assert item.item_type == "decision"
