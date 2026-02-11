"""Speech transcription module using faster-whisper."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel


@dataclass
class TranscriptChange:
    """Represents a change made during transcript normalization or repair."""
    
    segment_id: int
    timestamp: str  # Format: "MM:SS-MM:SS"
    before: str
    after: str
    reason: str
    change_type: str = "normalization"  # "normalization" or "repair"


@dataclass
class NormalizationResult:
    """Result of transcript normalization."""
    
    transcription: dict[str, Any]
    changes: list[TranscriptChange] = field(default_factory=list)


class Transcriber:
    """Transcribe audio using faster-whisper."""

    def __init__(self, model_name: str = "base") -> None:
        """
        Initialize the transcriber.

        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model: WhisperModel | None = None

    def _load_model(self) -> None:
        """Load the Whisper model if not already loaded."""
        if self.model is None:
            # Use CPU with int8 for efficiency
            self.model = WhisperModel(self.model_name, device="cpu", compute_type="int8")

    def transcribe(self, audio_file: Path, language: str | None = None) -> dict[str, Any]:
        """
        Transcribe audio file.

        Args:
            audio_file: Path to audio file (WAV format recommended)
            language: Language code for transcription (e.g., 'en', 'es'). 
                     If None, language is auto-detected.

        Returns:
            Dictionary containing transcription results with segments

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        self._load_model()

        try:
            # Transcribe with word-level timestamps
            segments, info = self.model.transcribe(
                str(audio_file),
                word_timestamps=True,
                language=language,
            )
            
            # Convert faster-whisper format to openai-whisper compatible format
            result: dict[str, Any] = {
                "text": "",
                "segments": [],
                "language": info.language,
            }
            
            for segment in segments:
                result["text"] += segment.text
                result["segments"].append({
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": [
                        {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                        }
                        for word in (segment.words or [])
                    ] if segment.words else [],
                })
            
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to transcribe audio: {e}") from e

    def get_segments(self, transcription: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract segments from transcription result.

        Args:
            transcription: Result from transcribe()

        Returns:
            List of segment dictionaries with text, start, and end times
        """
        segments: list[dict[str, Any]] = transcription.get("segments", [])
        return segments

    def get_full_text(self, transcription: dict[str, Any]) -> str:
        """
        Get full transcribed text.

        Args:
            transcription: Result from transcribe()

        Returns:
            Complete transcribed text
        """
        text: str = transcription.get("text", "")
        return text.strip()

    def normalize_transcript(
        self,
        transcription: dict[str, Any],
        remove_fillers: bool = False,
        normalize_numbers: bool = True,
    ) -> NormalizationResult:
        """
        Apply deterministic normalization to transcript.
        
        Performs:
        - Stutter reduction (repeated words)
        - Optional filler word removal
        - Sentence stitching across short pauses (≤500ms)
        - Safe number/date normalization
        
        Args:
            transcription: Result from transcribe()
            remove_fillers: If True, remove filler words (um, uh, like)
            normalize_numbers: If True, convert spoken numbers to digits
            
        Returns:
            NormalizationResult with updated transcription and change log
        """
        import copy
        
        result_transcription = copy.deepcopy(transcription)
        changes: list[TranscriptChange] = []
        
        segments = result_transcription.get("segments", [])
        
        # Step 1: Reduce stutters
        for seg in segments:
            original_text = seg["text"]
            normalized_text = self._reduce_stutters(original_text)
            
            if normalized_text != original_text:
                changes.append(TranscriptChange(
                    segment_id=seg["id"],
                    timestamp=self._format_timestamp(seg["start"], seg["end"]),
                    before=original_text,
                    after=normalized_text,
                    reason="Stutter reduction",
                    change_type="normalization",
                ))
                seg["text"] = normalized_text
        
        # Step 2: Filter fillers (optional)
        if remove_fillers:
            for seg in segments:
                original_text = seg["text"]
                filtered_text = self._filter_fillers(original_text)
                
                if filtered_text != original_text:
                    changes.append(TranscriptChange(
                        segment_id=seg["id"],
                        timestamp=self._format_timestamp(seg["start"], seg["end"]),
                        before=original_text,
                        after=filtered_text,
                        reason="Filler word removal",
                        change_type="normalization",
                    ))
                    seg["text"] = filtered_text
        
        # Step 3: Stitch sentences across short pauses
        stitched_segments, stitch_changes = self._stitch_sentences(segments)
        changes.extend(stitch_changes)
        result_transcription["segments"] = stitched_segments
        
        # Step 4: Normalize numbers/dates (safe, conservative)
        if normalize_numbers:
            for seg in stitched_segments:
                original_text = seg["text"]
                normalized_text = self._normalize_numbers_dates(original_text)
                
                if normalized_text != original_text:
                    changes.append(TranscriptChange(
                        segment_id=seg["id"],
                        timestamp=self._format_timestamp(seg["start"], seg["end"]),
                        before=original_text,
                        after=normalized_text,
                        reason="Number/date normalization",
                        change_type="normalization",
                    ))
                    seg["text"] = normalized_text
        
        # Rebuild full text
        result_transcription["text"] = " ".join(
            seg["text"] for seg in stitched_segments
        )
        
        return NormalizationResult(
            transcription=result_transcription,
            changes=changes,
        )

    def _reduce_stutters(self, text: str) -> str:
        """
        Reduce repeated words (stutters) to single instance.
        
        Example: "I I I think" → "I think"
        
        Args:
            text: Original text
            
        Returns:
            Text with stutters reduced
        """
        # Match repeated words (same word 2+ times in a row)
        # Use word boundaries to avoid partial matches
        pattern = r'\b(\w+)(\s+\1\b)+(?!\w)'
        
        def replace_stutter(match: re.Match[str]) -> str:
            return match.group(1)
        
        return re.sub(pattern, replace_stutter, text, flags=re.IGNORECASE)

    def _filter_fillers(self, text: str) -> str:
        """
        Remove filler words conservatively.
        
        Removes: um, uh, hmm, like (when used as filler), you know
        
        Args:
            text: Original text
            
        Returns:
            Text with fillers removed
        """
        # Conservative pattern - only remove obvious fillers
        filler_patterns = [
            r'\bum+\b',
            r'\buh+\b',
            r'\bhmm+\b',
            r'\b(you know|I mean)\b',
            # Remove "so like" or "kind of like" filler phrases
            r'\bso like\b',
            r'\bkind of like\b',
        ]
        
        result = text
        for pattern in filler_patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result

    def _stitch_sentences(
        self,
        segments: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[TranscriptChange]]:
        """
        Join segments across pauses ≤500ms.
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            Tuple of (stitched segments, change log)
        """
        if not segments:
            return segments, []
        
        stitched: list[dict[str, Any]] = []
        changes: list[TranscriptChange] = []
        
        current_segment = segments[0].copy()
        
        for i in range(1, len(segments)):
            prev_seg = segments[i - 1]
            curr_seg = segments[i]
            
            # Calculate pause duration
            pause_duration = curr_seg["start"] - prev_seg["end"]
            
            # If pause ≤ 500ms, stitch to current segment
            if pause_duration <= 0.5:
                current_segment["text"] = current_segment["text"].strip() + " " + curr_seg["text"].strip()
                current_segment["end"] = curr_seg["end"]
                
                # Update words if available
                if "words" in current_segment and "words" in curr_seg:
                    current_segment["words"].extend(curr_seg["words"])
                
                changes.append(TranscriptChange(
                    segment_id=current_segment["id"],
                    timestamp=self._format_timestamp(current_segment["start"], current_segment["end"]),
                    before=f"[Segment {prev_seg['id']}] + [Segment {curr_seg['id']}]",
                    after=f"[Stitched segment {current_segment['id']}]",
                    reason=f"Stitched across {pause_duration:.3f}s pause",
                    change_type="normalization",
                ))
            else:
                # Pause is too long, save current and start new
                stitched.append(current_segment)
                current_segment = curr_seg.copy()
        
        # Append the last segment
        stitched.append(current_segment)
        
        return stitched, changes

    def _normalize_numbers_dates(self, text: str) -> str:
        """
        Safely normalize spoken numbers and dates when unambiguous.
        
        Examples:
        - "march three" → "March 3"
        - "twenty twenty four" → "2024"
        - "five hundred" → "500"
        
        Args:
            text: Original text
            
        Returns:
            Text with normalized numbers/dates
        """
        # Month names (case-insensitive)
        months = {
            "january": "January", "february": "February", "march": "March",
            "april": "April", "may": "May", "june": "June",
            "july": "July", "august": "August", "september": "September",
            "october": "October", "november": "November", "december": "December",
        }
        
        # Simple number words
        number_words = {
            "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
            "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
            "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
            "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
            "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
            "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
            "eighty": "80", "ninety": "90",
        }
        
        result = text
        
        # Normalize "month + number" patterns (e.g., "march three" → "March 3")
        for month_lower, month_title in months.items():
            for num_word, num_digit in number_words.items():
                pattern = rf'\b{month_lower}\s+{num_word}\b'
                replacement = f"{month_title} {num_digit}"
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Normalize simple number words when standalone or obvious context
        # Only replace when followed by space or punctuation to avoid false positives
        for num_word, num_digit in number_words.items():
            # Be conservative - only replace in certain contexts
            pattern = rf'\b{num_word}\s+(am|pm|o\'clock|dollars|percent)\b'
            replacement = rf'{num_digit} \1'
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result

    def _format_timestamp(self, start: float, end: float) -> str:
        """
        Format timestamp range.
        
        Args:
            start: Start time in seconds
            end: End time in seconds
            
        Returns:
            Formatted timestamp string (MM:SS-MM:SS)
        """
        def format_seconds(seconds: float) -> str:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"
        
        return f"{format_seconds(start)}-{format_seconds(end)}"

    async def repair_transcript(
        self,
        transcription: dict[str, Any],
        llm_engine: Any,
    ) -> NormalizationResult:
        """
        Use LLM to repair ASR errors in transcript.
        
        Args:
            transcription: Result from transcribe()
            llm_engine: LLM engine instance (must have repair_transcript method)
            
        Returns:
            NormalizationResult with repaired transcription and change log
            
        Raises:
            RuntimeError: If LLM repair fails
        """
        import copy
        
        result_transcription = copy.deepcopy(transcription)
        changes: list[TranscriptChange] = []
        
        segments = result_transcription.get("segments", [])
        
        # Build full transcript text for LLM
        full_text = " ".join(seg["text"] for seg in segments)
        
        # Build repair prompt
        prompt = self._build_repair_prompt(full_text)
        
        try:
            # Call LLM engine's repair method
            repair_response = await llm_engine.repair_transcript(prompt)
            
            # Parse response - expecting JSON with repaired_text and changes
            if isinstance(repair_response, dict):
                repaired_text = repair_response.get("repaired_text", full_text)
                repair_changes = repair_response.get("changes", [])
            else:
                # If response is just text, use it as repaired text
                repaired_text = str(repair_response).strip()
                repair_changes = []
            
            # Update segments with repaired text
            if repaired_text and repaired_text != full_text:
                # Update the full text field
                result_transcription["text"] = repaired_text
                
                # Map repaired text back to segments
                # Strategy: Split repaired text into words and distribute to segments
                # based on approximate word counts per segment
                repaired_words = repaired_text.split()
                original_words = full_text.split()
                
                # If word counts are similar, map proportionally
                if len(repaired_words) > 0:
                    word_index = 0
                    
                    for seg_idx, seg in enumerate(segments):
                        original_seg_text = seg["text"]
                        original_seg_word_count = len(original_seg_text.split())
                        
                        # Determine how many words from repaired text to assign to this segment
                        if seg_idx == len(segments) - 1:
                            # Last segment gets all remaining words
                            seg_repaired_words = repaired_words[word_index:]
                        else:
                            # Proportional allocation
                            words_to_take = max(1, original_seg_word_count)
                            seg_repaired_words = repaired_words[word_index:word_index + words_to_take]
                            word_index += words_to_take
                        
                        repaired_seg_text = " ".join(seg_repaired_words)
                        
                        # Update segment if text changed
                        if repaired_seg_text != original_seg_text:
                            seg["text"] = repaired_seg_text
                            
                            # Log the change
                            changes.append(TranscriptChange(
                                segment_id=seg.get("id", seg_idx),
                                timestamp=self._format_timestamp(seg["start"], seg["end"]),
                                before=original_seg_text,
                                after=repaired_seg_text,
                                reason="LLM-based ASR error correction",
                                change_type="repair",
                            ))
                
                # Also log any structured changes from LLM response
                for change_info in repair_changes:
                    if isinstance(change_info, dict) and change_info.get("before") != change_info.get("after"):
                        changes.append(TranscriptChange(
                            segment_id=change_info.get("segment_id", 0),
                            timestamp=change_info.get("timestamp", "00:00-00:00"),
                            before=change_info.get("before", ""),
                            after=change_info.get("after", ""),
                            reason=change_info.get("reason", "ASR error correction"),
                            change_type="repair",
                        ))
        
        except Exception as e:
            raise RuntimeError(f"Failed to repair transcript: {e}") from e
        
        return NormalizationResult(
            transcription=result_transcription,
            changes=changes,
        )

    def _build_repair_prompt(self, transcript_text: str) -> str:
        """
        Build prompt for LLM transcript repair.
        
        Args:
            transcript_text: Original transcript text
            
        Returns:
            Repair prompt
        """
        prompt = f"""You are a transcript repair assistant. Your task is to fix ASR (Automatic Speech Recognition) errors in the following transcript while preserving the original meaning and timestamps.

**Instructions:**
1. Fix obvious ASR errors (misheard words, incorrect homophones, grammatical errors from poor recognition)
2. Preserve the original meaning - do NOT add, remove, or change the intent
3. Do NOT invent content or add information not present in the original
4. Keep technical terms, names, and domain-specific vocabulary intact unless clearly wrong
5. Output the repaired transcript text

**Original Transcript:**
{transcript_text}

**Repaired Transcript:**
"""
        return prompt
