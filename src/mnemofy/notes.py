"""Note generation module for creating structured Markdown notes from transcripts.

This module provides StructuredNotesGenerator for converting transcription results
into well-organized meeting notes with 7 sections: metadata, topics, decisions,
action items, concrete mentions, risks/questions, and transcript file links.

Supports two modes:
- basic: Deterministic, conservative extraction (default)
- llm: LLM-enhanced extraction (future feature, stubbed)
"""

import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class NotesMode(Enum):
    """Notes generation mode."""

    BASIC = "basic"
    LLM = "llm"


def seconds_to_mmss(seconds: float) -> str:
    """Convert seconds to MM:SS format (for notes).
    
    Args:
        seconds: Duration in seconds (float).
    
    Returns:
        Formatted time string in MM:SS format.
    
    Examples:
        >>> seconds_to_mmss(65.5)
        '01:05'
        >>> seconds_to_mmss(3661.0)
        '61:01'
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


class StructuredNotesGenerator:
    """Generate structured meeting notes from transcript segments.
    
    Converts transcription results into markdown notes with 7 required sections:
    1. Metadata (title, date, source, language, engine, timestamp)
    2. Topics (topic segmentation with timestamps)
    3. Decisions (explicit decisions with keywords)
    4. Action Items (assignments with owners and timestamps)
    5. Concrete Mentions (names, numbers, URLs, dates found in transcript)
    6. Risks & Open Questions (conditional statements and questions)
    7. Transcript Files (links to all output formats)
    
    Operates in two modes:
    - basic: Deterministic extraction using keyword matching (no hallucination)
    - llm: LLM-enhanced extraction (stubbed for future release)
    """

    # Decision keywords
    DECISION_KEYWORDS = {
        "decided",
        "decision",
        "agreed",
        "approved",
        "approved",
        "will go",
        "consensus",
        "approved",
    }

    # Action keywords
    ACTION_KEYWORDS = {
        "will",
        "going to",
        "need to",
        "should",
        "must",
        "task",
        "follow up",
        "next step",
        "action item",
    }

    # Pattern for extracting names (capitalized words)
    NAME_PATTERN = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b"

    # Pattern for currency, percentages, and numbers
    NUMBER_PATTERN = r"(\$[\d,.]+[MKB]?|\d+\.?\d*%|\d+(?:\.\d+)?(?:\s*(?:million|thousand|billion|M|K|B))?)"

    # Pattern for URLs
    URL_PATTERN = r"https?://[^\s)]+|www\.[^\s)]+"

    # Pattern for dates
    DATE_PATTERN = r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:\s+\d{4})?|\d{4}-\d{2}-\d{2}\b"

    def __init__(self, mode: str = "basic") -> None:
        """Initialize notes generator.
        
        Args:
            mode: "basic" (default) or "llm"
                 - basic: Deterministic, conservative extraction
                 - llm: LLM-enhanced extraction (future feature)
        
        Raises:
            ValueError: If mode not recognized.
        
        Examples:
            gen = StructuredNotesGenerator(mode="basic")
            gen = StructuredNotesGenerator()  # defaults to "basic"
        """
        try:
            self.mode = NotesMode(mode.lower())
        except ValueError:
            raise ValueError(f"Unknown mode: {mode}. Use 'basic' or 'llm'.")

    def generate(
        self,
        segments: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> str:
        """Generate structured notes markdown.
        
        Args:
            segments: List of transcript segments with start, end, text.
            metadata: Transcription metadata (engine, model, language, duration, etc.).
        
        Returns:
            str: Markdown notes with 7 sections.
        
        Raises:
            ValueError: If transcript < 30 seconds.
            KeyError: If required metadata fields missing.
            IndexError: If segments list empty.
        
        Examples:
            segments = [
                {'start': 0, 'end': 5, 'text': 'Hello everyone'},
                {'start': 5, 'end': 10, 'text': 'Lets discuss Q1'},
            ]
            metadata = {
                'engine': 'faster-whisper',
                'model': 'base',
                'language': 'en',
                'duration': 125.5,
                'input_file': 'meeting.mp4'
            }
            gen = StructuredNotesGenerator(mode="basic")
            notes = gen.generate(segments, metadata)
        """
        if self.mode == NotesMode.LLM:
            raise NotImplementedError("LLM mode coming in future release")

        # Validate inputs
        if not segments:
            raise IndexError("Segments list cannot be empty")

        # Check minimum duration
        total_duration = segments[-1]["end"]
        if total_duration < 30:
            raise ValueError(
                f"Transcript too short: minimum 30 seconds required (got {int(total_duration)})"
            )

        # Validate metadata
        required_fields = {"engine", "model", "language", "duration"}
        missing = required_fields - set(metadata.keys())
        if missing:
            raise KeyError(f"Metadata missing required fields: {missing}")

        # Generate all sections
        sections = []
        sections.append(self._extract_metadata_section(metadata, total_duration))
        sections.append(self._extract_topics(segments))
        sections.append(self._extract_decisions(segments))
        sections.append(self._extract_action_items(segments))
        sections.append(self._extract_concrete_mentions(segments))
        sections.append(self._extract_risks_and_questions(segments))
        sections.append(self._generate_transcript_links(metadata))

        return "\n".join(sections)

    def _extract_metadata_section(
        self,
        metadata: Dict[str, Any],
        total_duration: float,
    ) -> str:
        """Generate metadata section header."""
        # Extract from filename if available
        input_file = metadata.get("input_file", "recording")
        if isinstance(input_file, (str, Path)):
            title = Path(input_file).stem
        else:
            title = "Meeting Notes"

        # Format duration
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        duration_str = f"{minutes}m {seconds}s"

        # Get timestamp
        timestamp = metadata.get("timestamp", datetime.utcnow().isoformat() + "Z")

        # Build metadata section
        lines = [
            f"# Meeting Notes: {title}",
            "",
            f"**Date**: {datetime.utcnow().strftime('%Y-%m-%d')}",
            f"**Source**: {Path(input_file).name} ({duration_str})" if input_file else f"**Duration**: {duration_str}",
            f"**Language**: {metadata.get('language', 'Unknown')}",
            f"**Engine**: {metadata.get('engine', 'Unknown')} ({metadata.get('model', 'Unknown')})",
            f"**Generated**: {timestamp}",
        ]
        return "\n".join(lines)

    def _extract_topics(self, segments: List[Dict[str, Any]]) -> str:
        """Extract topics by dividing transcript into time buckets."""
        if not segments:
            return "## Topics\n\n*No topics found*"

        # Divide into 5-minute chunks
        bucket_size = 300  # 5 minutes
        topics = []

        start_time = 0
        end_time = bucket_size

        while start_time < segments[-1]["end"]:
            # Find segments in this bucket
            bucket_segments = [
                s for s in segments
                if s["start"] < end_time and s["end"] > start_time
            ]

            if bucket_segments:
                # Use first few words of segment as topic summary
                summary = bucket_segments[0]["text"].split()[:5]
                summary_text = " ".join(summary) if summary else "Continued discussion"

                start_mmss = seconds_to_mmss(start_time)
                end_mmss = seconds_to_mmss(min(end_time, segments[-1]["end"]))

                topics.append(f"- **[{start_mmss}–{end_mmss}]** {summary_text}")

            start_time = end_time
            end_time += bucket_size

        if not topics:
            return "## Topics\n\n*No topics found*"

        return "## Topics\n\n" + "\n".join(topics)

    def _extract_decisions(self, segments: List[Dict[str, Any]]) -> str:
        """Extract explicit decisions using keyword matching."""
        decisions = []

        for segment in segments:
            text = segment.get("text", "").lower()

            # Check for decision keywords
            if any(keyword in text for keyword in self.DECISION_KEYWORDS):
                original_text = segment.get("text", "").strip()
                timestamp = seconds_to_mmss(segment["start"])
                decisions.append(f"- **[{timestamp}]** {original_text}")

        if not decisions:
            return "## Decisions\n\n*No explicit decisions found*"

        return "## Decisions\n\n" + "\n".join(decisions)

    def _extract_action_items(self, segments: List[Dict[str, Any]]) -> str:
        """Extract action items with potential owner/assignment."""
        action_items = []

        for segment in segments:
            text = segment.get("text", "").lower()

            # Check for action keywords
            if any(keyword in text for keyword in self.ACTION_KEYWORDS):
                original_text = segment.get("text", "").strip()
                timestamp = seconds_to_mmss(segment["start"])
                action_items.append(f"- **[{timestamp}]** {original_text}")

        if not action_items:
            return "## Action Items\n\n*No action items found*"

        return "## Action Items\n\n" + "\n".join(action_items)

    def _extract_concrete_mentions(
        self, segments: List[Dict[str, Any]]
    ) -> str:
        """Extract names, numbers, URLs, and dates."""
        all_text = " ".join(s.get("text", "") for s in segments)

        # Extract names (capitalized words)
        names = set(re.findall(self.NAME_PATTERN, all_text))
        # Filter out common words that shouldn't be names
        stopwords = {
            "The",
            "A",
            "An",
            "And",
            "Or",
            "But",
            "In",
            "Is",
            "Are",
            "Was",
            "Were",
            "I",
            "You",
        }
        names = names - stopwords

        # Extract numbers
        numbers = re.findall(self.NUMBER_PATTERN, all_text)

        # Extract URLs
        urls = re.findall(self.URL_PATTERN, all_text)

        # Extract dates
        dates = re.findall(self.DATE_PATTERN, all_text)

        # Build sections
        sections = ["## Concrete Mentions"]

        if names:
            sections.append("\n### Names\n")
            for name in sorted(set(names)):
                sections.append(f"- {name}")

        if numbers:
            sections.append("\n### Numbers & Metrics\n")
            for number in sorted(set(numbers)):
                sections.append(f"- {number}")

        if urls:
            sections.append("\n### URLs & References\n")
            for url in sorted(set(urls)):
                sections.append(f"- {url}")

        if dates:
            sections.append("\n### Dates\n")
            for date in sorted(set(dates)):
                sections.append(f"- {date}")

        if not any([names, numbers, urls, dates]):
            sections.append("\n\n*No concrete mentions found*")

        return "\n".join(sections)

    def _extract_risks_and_questions(
        self, segments: List[Dict[str, Any]]
    ) -> str:
        """Extract risks and open questions."""
        questions = []
        risks = []

        risk_keywords = {"risk", "concern", "might", "could cause", "issue", "problem"}

        for segment in segments:
            text = segment.get("text", "").strip()
            timestamp = seconds_to_mmss(segment["start"])

            # Check for questions
            if text.endswith("?"):
                questions.append(f"- {text} **[{timestamp}]**")

            # Check for risks
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in risk_keywords):
                risks.append(f"- {text} **[{timestamp}]**")

        sections = ["## Risks & Open Questions"]

        if risks:
            sections.append("\n### Risks\n")
            sections.extend(risks)

        if questions:
            sections.append("\n### Open Questions\n")
            sections.extend(questions)

        if not any([risks, questions]):
            sections.append("\n\n*No risks or open questions found*")

        return "\n".join(sections)

    def _generate_transcript_links(self, metadata: Dict[str, Any]) -> str:
        """Generate transcript file links section.
        
        Note: Uses placeholder filenames based on input filename.
        Actual file generation is handled by OutputManager + formatters.
        """
        input_file = metadata.get("input_file", "transcript")
        if isinstance(input_file, (str, Path)):
            basename = Path(input_file).stem
        else:
            basename = "transcript"

        lines = [
            "## Transcript Files",
            "",
            f"- **Full Transcript (TXT)**: {basename}.transcript.txt",
            f"- **Subtitle Format (SRT)**: {basename}.transcript.srt",
            f"- **Structured Data (JSON)**: {basename}.transcript.json",
            f"- **Audio (WAV)**: {basename}.mnemofy.wav",
        ]
        return "\n".join(lines)


# Legacy compatibility
class NoteGenerator:
    """Legacy alias for backwards compatibility."""

    def __init__(self) -> None:
        """Initialize legacy note generator."""
        self.generator = StructuredNotesGenerator(mode="basic")

    def annotate_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Legacy method - kept for backwards compatibility."""
        return segments

    def generate_markdown(
        self, annotated_segments: List[Dict[str, Any]], title: str = "Meeting Notes"
    ) -> str:
        """Legacy method - kept for backwards compatibility."""
        # Convert to expected format
        metadata = {
            "engine": "unknown",
            "model": "unknown",
            "language": "en",
            "duration": 0,
            "input_file": title,
        }
        try:
            if annotated_segments:
                total_duration = max(
                    s.get("end", 0) for s in annotated_segments
                )
                metadata["duration"] = total_duration
            return self.generator.generate(annotated_segments, metadata)
        except (ValueError, KeyError, IndexError):
            # Fall back for backwards compatibility
            return f"# {title}\n\n(Unable to generate structured notes)"
