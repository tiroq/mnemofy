"""Note generation module for creating structured Markdown notes."""

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TimeStamp:
    """Timestamp with hours, minutes, and seconds."""

    hours: int
    minutes: int
    seconds: int

    @classmethod
    def from_seconds(cls, total_seconds: float) -> "TimeStamp":
        """Create timestamp from total seconds."""
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return cls(hours, minutes, seconds)

    def __str__(self) -> str:
        """Format as HH:MM:SS or MM:SS."""
        if self.hours > 0:
            return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}"
        return f"{self.minutes:02d}:{self.seconds:02d}"


@dataclass
class AnnotatedSegment:
    """Text segment with annotations."""

    text: str
    start: float
    end: float
    timestamp: TimeStamp
    is_topic: bool = False
    is_decision: bool = False
    is_action: bool = False
    mentions: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Initialize mentions set if None."""
        pass


class NoteGenerator:
    """Generate structured Markdown notes from transcription."""

    # Patterns for identifying different content types
    TOPIC_PATTERNS = [
        r"(?:let'?s talk about|discussing|the topic is|agenda item|next item)",
        r"(?:moving on to|switching to|now (?:let'?s|we'?ll) (?:discuss|talk about))",
    ]

    DECISION_PATTERNS = [
        r"(?:we(?:'ve| have)? decided|decision is|we(?:'ll| will) go with)",
        r"(?:agreed (?:to|that|on)|consensus is|final decision)",
    ]

    ACTION_PATTERNS = [
        r"(?:action item|todo|to do|need(?:s)? to|should|must|will|going to)",
        r"(?:follow up|next step|task|assign(?:ed)?|responsible)",
    ]

    MENTION_PATTERN = r"@(\w+)"

    def __init__(self) -> None:
        """Initialize the note generator."""
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficiency."""
        self.topic_regex = re.compile(
            "|".join(self.TOPIC_PATTERNS), re.IGNORECASE
        )
        self.decision_regex = re.compile(
            "|".join(self.DECISION_PATTERNS), re.IGNORECASE
        )
        self.action_regex = re.compile(
            "|".join(self.ACTION_PATTERNS), re.IGNORECASE
        )
        self.mention_regex = re.compile(self.MENTION_PATTERN)

    def _extract_mentions(self, text: str) -> set[str]:
        """Extract @mentions from text."""
        return set(self.mention_regex.findall(text))

    def _is_topic(self, text: str) -> bool:
        """Check if segment appears to introduce a topic."""
        return bool(self.topic_regex.search(text))

    def _is_decision(self, text: str) -> bool:
        """Check if segment appears to state a decision."""
        return bool(self.decision_regex.search(text))

    def _is_action_item(self, text: str) -> bool:
        """Check if segment appears to be an action item."""
        return bool(self.action_regex.search(text))

    def annotate_segments(
        self, segments: list[dict[str, Any]]
    ) -> list[AnnotatedSegment]:
        """
        Annotate transcription segments.

        Args:
            segments: List of segment dictionaries from transcription

        Returns:
            List of annotated segments
        """
        annotated = []
        for segment in segments:
            text = segment.get("text", "").strip()
            start = segment.get("start", 0.0)
            end = segment.get("end", 0.0)

            ann_segment = AnnotatedSegment(
                text=text,
                start=start,
                end=end,
                timestamp=TimeStamp.from_seconds(start),
                is_topic=self._is_topic(text),
                is_decision=self._is_decision(text),
                is_action=self._is_action_item(text),
                mentions=self._extract_mentions(text),
            )
            annotated.append(ann_segment)

        return annotated

    def generate_markdown(
        self, annotated_segments: list[AnnotatedSegment], title: str = "Meeting Notes"
    ) -> str:
        """
        Generate Markdown notes from annotated segments.

        Args:
            annotated_segments: List of annotated segments
            title: Title for the notes

        Returns:
            Formatted Markdown string
        """
        lines = [f"# {title}\n"]

        # Topics section
        topics = [s for s in annotated_segments if s.is_topic]
        if topics:
            lines.append("## Topics Discussed\n")
            for segment in topics:
                lines.append(f"- **[{segment.timestamp}]** {segment.text}\n")
            lines.append("")

        # Decisions section
        decisions = [s for s in annotated_segments if s.is_decision]
        if decisions:
            lines.append("## Decisions Made\n")
            for segment in decisions:
                lines.append(f"- **[{segment.timestamp}]** {segment.text}\n")
            lines.append("")

        # Action items section
        actions = [s for s in annotated_segments if s.is_action]
        if actions:
            lines.append("## Action Items\n")
            for segment in actions:
                mentions_str = (
                    f" ({', '.join('@' + m for m in sorted(segment.mentions))})"
                    if segment.mentions
                    else ""
                )
                lines.append(
                    f"- **[{segment.timestamp}]** {segment.text}{mentions_str}\n"
                )
            lines.append("")

        # Mentions section
        all_mentions: set[str] = set()
        for segment in annotated_segments:
            all_mentions.update(segment.mentions)

        if all_mentions:
            lines.append("## Mentions\n")
            for mention in sorted(all_mentions):
                # Find all segments mentioning this person
                mention_segments = [
                    s for s in annotated_segments if mention in s.mentions
                ]
                times = ", ".join(str(s.timestamp) for s in mention_segments)
                lines.append(f"- @{mention}: {times}\n")
            lines.append("")

        # Full transcript section
        lines.append("## Full Transcript\n")
        for segment in annotated_segments:
            lines.append(f"**[{segment.timestamp}]** {segment.text}\n\n")

        return "".join(lines)
