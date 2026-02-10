"""Note generation module for creating structured Markdown notes from transcripts.

This module provides StructuredNotesGenerator for converting transcription results
into well-organized meeting notes with 7 sections: metadata, topics, decisions,
action items, concrete mentions, risks/questions, and transcript file links.

Supports two modes:
- basic: Deterministic, conservative extraction (default)
- llm: LLM-enhanced extraction (future feature, stubbed)
"""

import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from mnemofy.classifier import TranscriptReference, GroundedItem, MeetingType


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


def load_jinja_template(template_name: str, custom_dir: Optional[Path] = None) -> Any:
    """Load a Jinja2 template from bundled templates or user override directory.
    
    Template search order (first match wins):
    1. Custom directory (if provided)
    2. User config: ~/.config/mnemofy/templates/
    3. Bundled templates: <package>/templates/
    
    Args:
        template_name: Name of template file (e.g., "status.md", "planning.md")
        custom_dir: Optional custom template directory path
    
    Returns:
        Jinja2 Template object ready for rendering
    
    Raises:
        TemplateNotFound: If template not found in any search path
        jinja2.TemplateError: If template has syntax errors
    
    Examples:
        >>> template = load_jinja_template("status.md")
        >>> output = template.render(decisions=[], actions=[], title="Daily Standup")
        
        >>> custom_path = Path("/custom/templates")
        >>> template = load_jinja_template("planning.md", custom_dir=custom_path)
    """
    search_paths: List[Path] = []
    
    # 1. Custom directory (highest priority)
    if custom_dir:
        search_paths.append(custom_dir)
    
    # 2. User config directory
    user_config = Path.home() / ".config" / "mnemofy" / "templates"
    if user_config.exists():
        search_paths.append(user_config)
    
    # 3. Bundled templates (fallback)
    bundled_templates = Path(__file__).parent / "templates"
    search_paths.append(bundled_templates)
    
    # Try each path in order
    for search_path in search_paths:
        try:
            env = Environment(
                loader=FileSystemLoader(str(search_path)),
                autoescape=False,  # Templates are Markdown, not HTML
                trim_blocks=True,
                lstrip_blocks=True,
            )
            # Add custom filters for timestamp formatting
            env.filters['seconds_to_mmss'] = seconds_to_mmss
            template = env.get_template(template_name)
            return template
        except TemplateNotFound:
            continue
    
    # No template found in any path
    raise TemplateNotFound(
        f"Template '{template_name}' not found in: {', '.join(str(p) for p in search_paths)}"
    )


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
        include_audio: bool = True,
    ) -> str:
        """Generate structured notes markdown.
        
        Args:
            segments: List of transcript segments with start, end, text.
            metadata: Transcription metadata (engine, model, language, duration, etc.).
            include_audio: Whether to include audio file link in transcript files section.
        
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
        sections.append(self._generate_transcript_links(metadata, include_audio))

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
        utc_now = datetime.now(timezone.utc)
        timestamp = metadata.get("timestamp", utc_now.isoformat().replace("+00:00", "Z"))

        # Build metadata section
        lines = [
            f"# Meeting Notes: {title}",
            "",
            f"**Date**: {utc_now.strftime('%Y-%m-%d')}",
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

    def _generate_transcript_links(self, metadata: Dict[str, Any], include_audio: bool = True) -> str:
        """Generate transcript file links section.
        
        Args:
            metadata: Transcription metadata containing input_file.
            include_audio: Whether to include audio file link.
        
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
        ]
        
        if include_audio:
            lines.append(f"- **Audio (WAV)**: {basename}.mnemofy.wav")
        
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


class BasicNotesExtractor:
    """Extract structured information from transcripts using deterministic rules.
    
    Operates completely offline without LLM dependencies. Uses keyword matching,
    pattern recognition, and heuristics to extract:
    - Decisions (explicit decision markers)
    - Action items (commitments and tasks)
    - Mentions (names, numbers, URLs, dates)
    - Timestamp references for all extracted items
    
    All extracted items are grounded with transcript references to ensure traceability.
    """
    
    # Decision keywords (extended from StructuredNotesGenerator)
    DECISION_KEYWORDS = {
        "decided", "decision", "agree", "agreed", "approved", "approve",
        "will go", "consensus", "let's go", "settled on", "finalized",
        "we'll do", "going with", "chosen", "selected"
    }
    
    # Action keywords
    ACTION_KEYWORDS = {
        "will", "going to", "need to", "should", "must", "task",
        "follow up", "next step", "action item", "todo", "to-do",
        "assign", "owner", "responsible", "commit", "promise"
    }
    
    # Pattern for extracting names (capitalized words, avoiding common words)
    NAME_PATTERN = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b"
    COMMON_WORDS = {
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
        "January", "February", "March", "April", "May", "June", "July", "August",
        "September", "October", "November", "December", "I", "The", "A", "An"
    }
    
    # Pattern for numbers, currency, percentages
    NUMBER_PATTERN = r"(\$[\d,.]+[MKB]?|\d+\.?\d*%|\d+(?:\.\d+)?(?:\s*(?:million|thousand|billion|M|K|B))?)"
    
    # Pattern for URLs
    URL_PATTERN = r"https?://[^\s)]+|www\.[^\s)]+"
    
    # Pattern for dates
    DATE_PATTERN = r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,?\s+\d{4})?|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}\b"
    
    def __init__(self):
        """Initialize basic notes extractor."""
        pass
    
    def extract_decisions(
        self,
        segments: List[Dict[str, Any]],
        transcript_text: Optional[str] = None
    ) -> List[GroundedItem]:
        """Extract decision items from transcript segments.
        
        Looks for decision keywords and extracts surrounding context.
        
        Args:
            segments: List of transcript segments with start, end, text, speaker
            transcript_text: Optional full transcript text (will be constructed if not provided)
        
        Returns:
            List of GroundedItem objects with decision text and timestamp references
        """
        decisions = []
        
        for segment in segments:
            text = segment.get("text", "")
            text_lower = text.lower()
            
            # Check if segment contains decision keywords
            for keyword in self.DECISION_KEYWORDS:
                if keyword in text_lower:
                    # Create reference
                    ref = TranscriptReference(
                        reference_id=str(uuid.uuid4())[:8],
                        start_time=segment.get("start", 0),
                        end_time=segment.get("end", 0),
                        speaker=segment.get("speaker"),
                        text_snippet=text[:100]  # First 100 chars
                    )
                    
                    # Create grounded decision item
                    decision = GroundedItem(
                        text=text.strip(),
                        status="confirmed",
                        reason=None,
                        references=[ref],
                        item_type="decision",
                        metadata={"keyword": keyword}
                    )
                    decisions.append(decision)
                    break  # Only count each segment once
        
        return decisions
    
    def extract_action_items(
        self,
        segments: List[Dict[str, Any]],
        transcript_text: Optional[str] = None
    ) -> List[GroundedItem]:
        """Extract action items from transcript segments.
        
        Looks for action keywords and commitment phrases.
        
        Args:
            segments: List of transcript segments with start, end, text, speaker
            transcript_text: Optional full transcript text
        
        Returns:
            List of GroundedItem objects with action items and timestamp references
        """
        actions = []
        
        for segment in segments:
            text = segment.get("text", "")
            text_lower = text.lower()
            
            # Check if segment contains action keywords
            for keyword in self.ACTION_KEYWORDS:
                if keyword in text_lower:
                    # Create reference
                    ref = TranscriptReference(
                        reference_id=str(uuid.uuid4())[:8],
                        start_time=segment.get("start", 0),
                        end_time=segment.get("end", 0),
                        speaker=segment.get("speaker"),
                        text_snippet=text[:100]
                    )
                    
                    # Try to extract owner from speaker or text
                    owner = segment.get("speaker")
                    
                    # Create grounded action item
                    action = GroundedItem(
                        text=text.strip(),
                        status="confirmed",
                        reason=None,
                        references=[ref],
                        item_type="action",
                        metadata={"keyword": keyword, "owner": owner}
                    )
                    actions.append(action)
                    break  # Only count each segment once
        
        return actions
    
    def extract_mentions(
        self,
        segments: List[Dict[str, Any]],
        transcript_text: Optional[str] = None
    ) -> List[GroundedItem]:
        """Extract mentions (names, numbers, URLs, dates) from transcript.
        
        Args:
            segments: List of transcript segments
            transcript_text: Optional full transcript text
        
        Returns:
            List of GroundedItem objects with mentions and timestamp references
        """
        mentions = []
        
        # Build full text if not provided
        if not transcript_text:
            transcript_text = " ".join(s.get("text", "") for s in segments)
        
        # Extract different types of mentions
        mention_patterns = [
            (self.URL_PATTERN, "url"),
            (self.DATE_PATTERN, "date"),
            (self.NUMBER_PATTERN, "number"),
        ]
        
        for pattern, mention_type in mention_patterns:
            for match in re.finditer(pattern, transcript_text):
                matched_text = match.group(0)
                
                # Find segment containing this mention
                char_pos = match.start()
                current_pos = 0
                
                for segment in segments:
                    seg_text = segment.get("text", "")
                    if current_pos <= char_pos < current_pos + len(seg_text):
                        # Found the segment
                        ref = TranscriptReference(
                            reference_id=str(uuid.uuid4())[:8],
                            start_time=segment.get("start", 0),
                            end_time=segment.get("end", 0),
                            speaker=segment.get("speaker"),
                            text_snippet=seg_text[:100]
                        )
                        
                        mention = GroundedItem(
                            text=matched_text,
                            status="confirmed",
                            reason=None,
                            references=[ref],
                            item_type="mention",
                            metadata={"mention_type": mention_type}
                        )
                        mentions.append(mention)
                        break
                    
                    current_pos += len(seg_text) + 1  # +1 for space
        
        return mentions
    
    def extract_all(
        self,
        segments: List[Dict[str, Any]],
        meeting_type: Optional[MeetingType] = None
    ) -> Dict[str, List[GroundedItem]]:
        """Extract all structured information from transcript.
        
        Args:
            segments: List of transcript segments
            meeting_type: Optional detected meeting type for context
        
        Returns:
            Dictionary with keys: decisions, actions, mentions
        """
        transcript_text = " ".join(s.get("text", "") for s in segments)
        
        return {
            "decisions": self.extract_decisions(segments, transcript_text),
            "actions": self.extract_action_items(segments, transcript_text),
            "mentions": self.extract_mentions(segments, transcript_text),
        }


def render_meeting_notes(
    meeting_type: MeetingType,
    extracted_items: Dict[str, List[GroundedItem]],
    metadata: Dict[str, Any],
    custom_template_dir: Optional[Path] = None
) -> str:
    """Render meeting notes using the appropriate template for the meeting type.
    
    Args:
        meeting_type: Detected meeting type (determines template selection)
        extracted_items: Dictionary with decisions, actions, mentions, etc.
        metadata: Meeting metadata (date, duration, confidence, etc.)
        custom_template_dir: Optional custom template directory
    
    Returns:
        Rendered Markdown notes as string
    
    Raises:
        TemplateNotFound: If template file not found
        jinja2.TemplateError: If template has syntax errors
    
    Examples:
        >>> items = {
        ...     "decisions": [GroundedItem(text="Use Python", ...)],
        ...     "actions": [GroundedItem(text="Write tests", ...)],
        ...     "mentions": []
        ... }
        >>> metadata = {"date": "2026-02-10", "duration": "30min", "confidence": "0.85"}
        >>> notes = render_meeting_notes(MeetingType.PLANNING, items, metadata)
    """
    # Load appropriate template
    template_name = f"{meeting_type.value}.md"
    template = load_jinja_template(template_name, custom_template_dir)
    
    # Prepare template context
    context = {
        # Metadata
        "title": metadata.get("title", f"{meeting_type.value.title()} Meeting"),
        "date": metadata.get("date", datetime.now().strftime("%Y-%m-%d")),
        "duration": metadata.get("duration", "N/A"),
        "confidence": metadata.get("confidence", "N/A"),
        "engine": metadata.get("engine", "heuristic"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        
        # Extracted items (default to empty lists)
        "decisions": extracted_items.get("decisions", []),
        "actions": extracted_items.get("actions", []),
        "mentions": extracted_items.get("mentions", []),
        
        # Meeting-type-specific mappings
        "progress_items": extracted_items.get("progress_items", []),
        "blockers": extracted_items.get("blockers", []),
        "next_steps": extracted_items.get("next_steps", []),
        "objectives": extracted_items.get("objectives", []),
        "milestones": extracted_items.get("milestones", []),
        "priorities": extracted_items.get("priorities", []),
        "resources": extracted_items.get("resources", []),
        "dependencies": extracted_items.get("dependencies", []),
        "goals": extracted_items.get("goals", []),
        "architecture": extracted_items.get("architecture", []),
        "components": extracted_items.get("components", []),
        "tradeoffs": extracted_items.get("tradeoffs", []),
        "questions": extracted_items.get("questions", []),
        "features": extracted_items.get("features", []),
        "highlights": extracted_items.get("highlights", []),
        "feedback": extracted_items.get("feedback", []),
        "overview": extracted_items.get("overview", []),
        "key_points": extracted_items.get("key_points", []),
        "examples": extracted_items.get("examples", []),
        "takeaways": extracted_items.get("takeaways", []),
        "summary": extracted_items.get("summary", []),
        "root_cause": extracted_items.get("root_cause", []),
        "timeline": extracted_items.get("timeline", []),
        "impact": extracted_items.get("impact", []),
        "mitigations": extracted_items.get("mitigations", []),
        "prevention": extracted_items.get("prevention", []),
        "pain_points": extracted_items.get("pain_points", []),
        "workflow": extracted_items.get("workflow", []),
        "insights": extracted_items.get("insights", []),
        "requirements": extracted_items.get("requirements", []),
        "opportunities": extracted_items.get("opportunities", []),
        "checkin": extracted_items.get("checkin", []),
        "progress": extracted_items.get("progress", []),
        "challenges": extracted_items.get("challenges", []),
        "growth": extracted_items.get("growth", []),
        "ideas": extracted_items.get("ideas", []),
        "promising": extracted_items.get("promising", []),
        "constraints": extracted_items.get("constraints", []),
    }
    
    # Render template
    return template.render(**context)