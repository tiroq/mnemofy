"""Tests for the note generation module."""

from mnemofy.notes import AnnotatedSegment, NoteGenerator, TimeStamp


def test_timestamp_formatting() -> None:
    """Test timestamp formatting."""
    assert str(TimeStamp(0, 0, 5)) == "00:05"
    assert str(TimeStamp(0, 12, 30)) == "12:30"
    assert str(TimeStamp(1, 5, 15)) == "01:05:15"
    assert str(TimeStamp(2, 30, 45)) == "02:30:45"


def test_timestamp_from_seconds() -> None:
    """Test creating timestamps from seconds."""
    ts = TimeStamp.from_seconds(125.5)
    assert ts.minutes == 2
    assert ts.seconds == 5

    ts = TimeStamp.from_seconds(3665.0)
    assert ts.hours == 1
    assert ts.minutes == 1
    assert ts.seconds == 5


def test_topic_detection() -> None:
    """Test topic detection patterns."""
    generator = NoteGenerator()

    assert generator._is_topic("Let's talk about the new feature")
    assert generator._is_topic("Discussing the timeline")
    assert generator._is_topic("Now let's discuss the budget")
    assert not generator._is_topic("This is just a regular sentence")


def test_decision_detection() -> None:
    """Test decision detection patterns."""
    generator = NoteGenerator()

    assert generator._is_decision("We've decided to use Python")
    assert generator._is_decision("The decision is to launch in Q2")
    assert generator._is_decision("We agreed to move forward")
    assert not generator._is_decision("This is just a regular sentence")


def test_action_item_detection() -> None:
    """Test action item detection patterns."""
    generator = NoteGenerator()

    assert generator._is_action_item("John needs to create the documentation")
    assert generator._is_action_item("Action item: review the code")
    assert generator._is_action_item("We should follow up next week")
    assert generator._is_action_item("Sarah will handle the deployment")
    assert not generator._is_action_item("This is just a regular sentence")


def test_mention_extraction() -> None:
    """Test @mention extraction."""
    generator = NoteGenerator()

    mentions = generator._extract_mentions("@john needs to review @sarah's code")
    assert mentions == {"john", "sarah"}

    mentions = generator._extract_mentions("No mentions here")
    assert mentions == set()


def test_annotate_segments() -> None:
    """Test segment annotation."""
    generator = NoteGenerator()

    segments = [
        {"text": "Let's talk about the project", "start": 0.0, "end": 3.0},
        {"text": "We've decided to use Python", "start": 3.0, "end": 6.0},
        {"text": "@john will create the docs", "start": 6.0, "end": 9.0},
    ]

    annotated = generator.annotate_segments(segments)

    assert len(annotated) == 3
    assert annotated[0].is_topic
    assert annotated[1].is_decision
    assert annotated[2].is_action
    assert "john" in annotated[2].mentions


def test_markdown_generation() -> None:
    """Test Markdown note generation."""
    generator = NoteGenerator()

    segments = [
        AnnotatedSegment(
            text="Let's discuss the roadmap",
            start=0.0,
            end=3.0,
            timestamp=TimeStamp(0, 0, 0),
            is_topic=True,
        ),
        AnnotatedSegment(
            text="We decided to launch in Q2",
            start=3.0,
            end=6.0,
            timestamp=TimeStamp(0, 0, 3),
            is_decision=True,
        ),
        AnnotatedSegment(
            text="@alice will prepare the report",
            start=6.0,
            end=9.0,
            timestamp=TimeStamp(0, 0, 6),
            is_action=True,
            mentions={"alice"},
        ),
    ]

    markdown = generator.generate_markdown(segments, title="Test Meeting")

    assert "# Test Meeting" in markdown
    assert "## Topics Discussed" in markdown
    assert "Let's discuss the roadmap" in markdown
    assert "## Decisions Made" in markdown
    assert "We decided to launch in Q2" in markdown
    assert "## Action Items" in markdown
    assert "@alice will prepare the report" in markdown
    assert "## Mentions" in markdown
    assert "@alice" in markdown
    assert "## Full Transcript" in markdown
