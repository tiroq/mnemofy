"""Format transcript segments into multiple output formats (TXT, SRT, JSON).

This module provides TranscriptFormatter for converting transcription results
into three industry-standard formats: plain text with timestamps (TXT), SubRip
subtitle format (SRT), and machine-readable JSON.

All formatters maintain consistency in timing precision, character encoding,
and error handling across outputs.
"""

import json
from typing import Any, Dict, List, Optional


def seconds_to_hms(seconds: float, format: str = "srt") -> str:
    """Convert seconds to formatted time string.
    
    Args:
        seconds: Duration in seconds (float).
        format: Output format - "txt" (HH:MM:SS), "srt" (HH:MM:SS,mmm).
    
    Returns:
        Formatted time string with appropriate precision.
    
    Raises:
        ValueError: If seconds is negative.
        TypeError: If seconds is not numeric.
    
    Examples:
        >>> seconds_to_hms(65.123, format="txt")
        '00:01:05'
        >>> seconds_to_hms(65.123, format="srt")
        '00:01:05,123'
        >>> seconds_to_hms(3661.5, format="txt")
        '01:01:01'
    """
    if not isinstance(seconds, (int, float)):
        raise TypeError(f"seconds must be numeric, got {type(seconds)}")
    
    if seconds < 0:
        raise ValueError(f"seconds must be non-negative, got {seconds}")
    
    # Calculate components
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if format == "txt":
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    elif format == "srt":
        # For SRT, handle milliseconds with proper normalization to avoid overflow
        millis = int(round((seconds % 1) * 1000))
        
        # Normalize if rounding produced 1000 milliseconds
        if millis == 1000:
            millis = 0
            secs += 1
            if secs == 60:
                secs = 0
                minutes += 1
                if minutes == 60:
                    minutes = 0
                    hours += 1
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    else:
        raise ValueError(f"Unknown format: {format}")


def validate_segment(segment: Dict[str, Any], index: Optional[int] = None) -> None:
    """Validate segment has required fields and correct types.
    
    Args:
        segment: Segment dict to validate.
        index: Optional segment index for error messages.
    
    Raises:
        KeyError: If required fields ('start', 'end', 'text') missing.
        TypeError: If fields have incorrect types.
        ValueError: If timing is invalid (start >= end).
    """
    idx_str = f" (segment {index})" if index is not None else ""
    
    # Check required fields
    if "start" not in segment:
        raise KeyError(f"Segment missing 'start' field{idx_str}")
    if "end" not in segment:
        raise KeyError(f"Segment missing 'end' field{idx_str}")
    if "text" not in segment:
        raise KeyError(f"Segment missing 'text' field{idx_str}")
    
    # Check types
    if not isinstance(segment["start"], (int, float)):
        raise TypeError(
            f"Segment 'start' must be numeric, got {type(segment['start'])}{idx_str}"
        )
    if not isinstance(segment["end"], (int, float)):
        raise TypeError(
            f"Segment 'end' must be numeric, got {type(segment['end'])}{idx_str}"
        )
    if not isinstance(segment["text"], str):
        raise TypeError(
            f"Segment 'text' must be string, got {type(segment['text'])}{idx_str}"
        )
    
    # Check timing order
    if segment["start"] >= segment["end"]:
        raise ValueError(
            f"Segment start ({segment['start']}) must be less than "
            f"end ({segment['end']}){idx_str}"
        )


class TranscriptFormatter:
    """Format transcript segments into multiple output formats.
    
    Provides static methods to convert transcription results into three
    industry-standard formats: TXT (timestamped text), SRT (SubRip subtitles),
    and JSON (machine-readable with metadata).
    
    All methods maintain consistent validation, error handling, and UTF-8
    encoding across formats.
    """
    
    @staticmethod
    def to_txt(segments: List[Dict[str, Any]]) -> str:
        """Convert segments to timestamped text format.
        
        Each segment is output as one line with format: [HH:MM:SS–HH:MM:SS] text
        
        Args:
            segments: List of segment dicts from transcription.
                     Each segment must have: start, end, text.
        
        Returns:
            str: Text with one line per segment.
        
        Raises:
            ValueError: If segments list is empty.
            KeyError: If required fields (start, end, text) missing.
            TypeError: If segment timing is not numeric.
        
        Example:
            >>> segments = [
            ...     {'start': 1.0, 'end': 5.0, 'text': 'Hello world'},
            ...     {'start': 5.0, 'end': 10.0, 'text': 'Second segment'},
            ... ]
            >>> txt = TranscriptFormatter.to_txt(segments)
            >>> print(txt)
            [00:00:01–00:00:05] Hello world
            [00:00:05–00:00:10] Second segment
        """
        if not segments:
            raise ValueError("Cannot format empty segment list")
        
        lines = []
        for i, segment in enumerate(segments):
            validate_segment(segment, index=i)
            
            start_time = seconds_to_hms(segment["start"], format="txt")
            end_time = seconds_to_hms(segment["end"], format="txt")
            text = segment["text"]
            
            # Use en-dash (–) as separator, not hyphen (-)
            line = f"[{start_time}–{end_time}] {text}"
            lines.append(line)
        
        return "\n".join(lines)
    
    @staticmethod
    def to_srt(segments: List[Dict[str, Any]]) -> str:
        """Convert segments to SubRip subtitle format.
        
        Produces properly formatted SRT with sequence numbers, timing in
        milliseconds (HH:MM:SS,mmm), and text blocks separated by blank lines.
        
        Args:
            segments: List of segment dicts from transcription.
                     Each segment must have: start, end, text.
        
        Returns:
            str: SRT format with sequence numbers, timing, text blocks.
        
        Raises:
            ValueError: If segments list is empty or invalid.
            KeyError: If required fields missing.
            TypeError: If timing not numeric or text not string.
        
        Example:
            >>> segments = [
            ...     {'start': 1.0, 'end': 5.0, 'text': 'Hello world'},
            ...     {'start': 5.0, 'end': 10.0, 'text': 'Second segment'},
            ... ]
            >>> srt = TranscriptFormatter.to_srt(segments)
            >>> print(srt)
            1
            00:00:01,000 --> 00:00:05,000
            Hello world
            <BLANKLINE>
            2
            00:00:05,000 --> 00:00:10,000
            Second segment
        """
        if not segments:
            raise ValueError("Cannot format empty segment list")
        
        blocks = []
        for i, segment in enumerate(segments):
            validate_segment(segment, index=i)
            
            sequence = i + 1
            start_time = seconds_to_hms(segment["start"], format="srt")
            end_time = seconds_to_hms(segment["end"], format="srt")
            text = segment["text"]
            
            # Build SRT block: sequence, timing, text
            block = f"{sequence}\n{start_time} --> {end_time}\n{text}"
            blocks.append(block)
        
        return "\n\n".join(blocks)
    
    @staticmethod
    def to_json(
        segments: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> str:
        """Convert segments and metadata to JSON format.
        
        Produces a JSON structure with schema_version, metadata, and segments
        arrays. All data is validated and formatted with 2-space indentation.
        
        Args:
            segments: List of segment dicts from transcription.
                     Each segment must have: start, end, text.
            metadata: Metadata dict with required fields:
                     - engine: str (e.g., "faster-whisper")
                     - model: str (e.g., "base")
                     - language: str (e.g., "en")
                     - duration: float (audio duration in seconds)
                     
                     Optional fields (preserved as-is):
                     - schema_version, timestamp, mnemofy_version, model_size_gb,
                     - quality_rating, speed_rating, processing_time_seconds, etc.
        
        Returns:
            str: JSON string (pretty-printed with 2-space indent).
        
        Raises:
            ValueError: If segments or metadata invalid.
            KeyError: If required metadata fields missing.
            TypeError: If data structures not JSON-serializable.
        
        Example:
            >>> segments = [
            ...     {'start': 1.0, 'end': 5.0, 'text': 'Hello', 'confidence': 0.95},
            ... ]
            >>> metadata = {
            ...     'engine': 'faster-whisper',
            ...     'model': 'base',
            ...     'language': 'en',
            ...     'duration': 5.0,
            ...     'schema_version': '1.0'
            ... }
            >>> json_str = TranscriptFormatter.to_json(segments, metadata)
            >>> parsed = json.loads(json_str)
            >>> parsed['schema_version']
            '1.0'
        """
        if not segments:
            raise ValueError("Cannot format empty segment list")
        
        # Validate all segments
        for i, segment in enumerate(segments):
            validate_segment(segment, index=i)
        
        # Validate required metadata fields
        required_fields = {"engine", "model", "language", "duration"}
        missing = required_fields - set(metadata.keys())
        if missing:
            raise KeyError(f"Metadata missing required fields: {missing}")
        
        # Validate metadata types
        if not isinstance(metadata.get("engine"), str):
            raise TypeError(f"Metadata 'engine' must be string, got {type(metadata['engine'])}")
        if not isinstance(metadata.get("model"), str):
            raise TypeError(f"Metadata 'model' must be string, got {type(metadata['model'])}")
        if not isinstance(metadata.get("language"), str):
            raise TypeError(f"Metadata 'language' must be string, got {type(metadata['language'])}")
        if not isinstance(metadata.get("duration"), (int, float)):
            raise TypeError(f"Metadata 'duration' must be numeric, got {type(metadata['duration'])}")
        
        # Ensure schema_version is set (defaulting to "1.0" if not provided)
        if "schema_version" not in metadata:
            metadata = {**metadata, "schema_version": "1.0"}
        
        # Enrich metadata with additional computed fields
        enriched_metadata = {**metadata}
        
        # Add generation timestamp if not present
        if "generated_at" not in enriched_metadata:
            from datetime import datetime
            enriched_metadata["generated_at"] = datetime.now().isoformat()
        
        # Add segment statistics if not present
        if "segment_count" not in enriched_metadata:
            enriched_metadata["segment_count"] = len(segments)
        
        # Add word count if not present
        if "word_count" not in enriched_metadata:
            transcript_text = " ".join(seg.get("text", "") for seg in segments)
            enriched_metadata["word_count"] = len(transcript_text.split())
        
        # Build output structure
        output = {
            "schema_version": enriched_metadata.get("schema_version", "1.0"),
            "metadata": enriched_metadata,
            "segments": segments,
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)

