# API Contract: StructuredNotesGenerator

**Feature**: 002-enhanced-output-formats  
**Phase**: 1 (Design - API Contracts)  
**Module**: `src/mnemofy/notes.py` (REFACTOR)

---

## Class: StructuredNotesGenerator

Generate structured meeting notes with 7 required sections.

### Purpose
Extract meaningful information from transcripts and format as Markdown notes with timestamp citations. Basic mode is deterministic (no hallucination); LLM mode is stubbed for future.

### Interface

```python
from typing import List, Dict, Any, Optional
from enum import Enum

class NotesMode(Enum):
    """Notes generation mode."""
    BASIC = "basic"          # Deterministic, conservative extraction
    LLM = "llm"              # LLM-enhanced (future feature)

class StructuredNotesGenerator:
    """Generate structured meeting notes from transcript."""
    
    def __init__(self, mode: str = "basic") -> None:
        """
        Initialize notes generator.
        
        Args:
            mode: "basic" (default) or "llm"
                 - basic: Deterministic extraction, no hallucination
                 - llm: LLM-enhanced extraction (future, stub for now)
        
        Raises:
            ValueError: If mode not recognized
        
        Examples:
            gen = StructuredNotesGenerator(mode="basic")
            
            gen = StructuredNotesGenerator()  # defaults to "basic"
        """
        ...
    
    def generate(
        self,
        segments: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate structured notes markdown.
        
        Args:
            segments: List of transcript segments
                     Must have: start, end, text
                     Timing must be in seconds (float)
            
            metadata: Transcription metadata
                     Must have: engine, model, language, duration
                     Optional: timestamp, input_file
        
        Returns:
            str: Markdown notes with 7 sections
        
        Raises:
            ValueError: If segments < 30 seconds (too short for notes)
            KeyError: If required metadata fields missing
            IndexError: If segments list empty
        
        Output Format (7 Sections):
            # Meeting Notes: [Title from filename]
            
            **Date**: 2026-02-10
            **Source**: meeting.mp4 (2m 5s)
            **Language**: English (en)
            **Engine**: faster-whisper (base)
            **Generated**: 2026-02-10T14:30:45Z
            
            ## Topics
            - **[00:00–00:30]** Opening remarks
            - **[00:30–01:15]** Q1 planning
            
            ## Decisions
            - **[00:45]** Budget approved
            - **[01:20]** Timeline postponed
            
            ## Action Items
            - **[01:10]** John: Task by Feb 15
            - **[01:35]** Sarah: Review docs
            
            ## Concrete Mentions
            ### Names
            - John Smith
            - Sarah Johnson
            
            ### Numbers & Metrics
            - Budget: $2.5M [00:45]
            
            ### URLs & References
            - https://github.com/team/repo [01:15]
            
            ## Risks & Open Questions
            ### Risks
            - Timeline might slip
            
            ### Open Questions
            - Budget confirmation status?
            
            ## Transcript Files
            - **Full Transcript (TXT)**: meeting.transcript.txt
            - **Subtitle Format (SRT)**: meeting.transcript.srt
            - **Structured Data (JSON)**: meeting.transcript.json
            - **Audio (WAV)**: meeting.mnemofy.wav
        
        Notes:
            - Minimum 30 seconds of transcript required
            - All timestamps cited with segments
            - Deterministic in basic mode (reproducible)
            - No hallucinated content
            - Times in MM:SS format within notes
        
        Examples:
            segments = [
                {'start': 0, 'end': 10, 'text': 'Hello everyone'},
                {'start': 10, 'end': 20, 'text': 'Lets discuss'},
                ...
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
            # Returns markdown string with 7 sections
        """
        ...
    
    def _extract_metadata_section(
        self,
        metadata: Dict[str, Any],
        total_duration: float
    ) -> str:
        """
        Generate metadata section (header).
        
        Returns:
            Markdown string with title, date, source, etc.
        """
        ...
    
    def _extract_topics(
        self,
        segments: List[Dict[str, Any]]
    ) -> str:
        """
        Extract topics from transcript.
        
        Strategy (basic mode):
        - Time buckets: divide transcript into 5-minute chunks
        - Check for topic keywords: discussion, agenda, topic, focus
        - Return time ranges with summary (first few words of chunk)
        
        Returns:
            Markdown bullet list with topics
        
        Example Output:
            ## Topics
            
            - **[00:00–00:30]** Opening remarks and introductions
            - **[00:30–01:15]** Q1 engineering roadmap discussion
            - **[01:15–02:05]** Budget allocation and planning
        """
        ...
    
    def _extract_decisions(
        self,
        segments: List[Dict[str, Any]]
    ) -> str:
        """
        Extract decisions from transcript.
        
        Strategy (basic mode):
        - Keyword matching: "decided", "agreed", "approved", "will do"
        - Capture sentence containing keyword
        - Extract timestamp from segment
        - Mark explicit decisions only (no inference)
        
        Returns:
            Markdown bullet list with decisions
        
        Example Output:
            ## Decisions
            
            - **[00:45]** Approved Q1 budget of $2.5M
            - **[01:20]** Postponed mobile rewrite to Q3
            
            *Note: No explicit decisions found* (if empty)
        """
        ...
    
    def _extract_action_items(
        self,
        segments: List[Dict[str, Any]]
    ) -> str:
        """
        Extract action items from transcript.
        
        Strategy (basic mode):
        - Keyword matching: "will", "going to", "need to", "task"
        - Capture owner (person name before "will")
        - Capture action and optional deadline
        - Extract timestamp from segment
        
        Returns:
            Markdown bullet list with action items
        
        Example Output:
            ## Action Items
            
            - **[01:10]** John: Complete RFP by Feb 15
            - **[01:35]** Sarah: Review architecture docs
            - **[01:50]** Team: Schedule follow-up for Feb 17
        """
        ...
    
    def _extract_concrete_mentions(
        self,
        segments: List[Dict[str, Any]]
    ) -> str:
        """
        Extract names, numbers, URLs from transcript.
        
        Strategy (basic mode):
        - Names: capitalized words (heuristic)
        - Numbers: regex for currency, metrics ($2.5M, 99.9%)
        - URLs: regex for http:// and https://
        - Dates: regex for common formats (Feb 15, 2026-02-10)
        
        Returns:
            Markdown sections for names, numbers, URLs
        
        Example Output:
            ## Concrete Mentions
            
            ### Names
            - John Smith [00:45]
            - Sarah Johnson [01:10]
            
            ### Numbers & Metrics
            - Q1 budget: $2.5M [00:45]
            - Performance target: 99.9% uptime [02:00]
            
            ### URLs & References
            - https://github.com/team/roadmap [01:15]
        """
        ...
    
    def _extract_risks_and_questions(
        self,
        segments: List[Dict[str, Any]]
    ) -> str:
        """
        Extract risks and open questions.
        
        Strategy (basic mode):
        - Questions: sentences ending with "?"
        - Risks: keywords "risk", "concern", "might", "could cause"
        - Mark as uncertain/conditional only
        - No speculation/inference
        
        Returns:
            Markdown sections for risks and open questions
        
        Example Output:
            ## Risks & Open Questions
            
            ### Risks
            - Budget allocation may be insufficient [00:45]
            
            ### Open Questions
            - When will marketing finalize budget? [01:20]
            - Has baseline been established? [01:50]
        """
        ...
    
    def _generate_transcript_links(
        self,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate transcript file links section.
        
        Returns:
            Markdown links to all transcript files
        
        Example Output:
            ## Transcript Files
            
            - **Full Transcript (TXT)**: meeting.transcript.txt
            - **Subtitle Format (SRT)**: meeting.transcript.srt
            - **Structured Data (JSON)**: meeting.transcript.json
            - **Audio (WAV)**: meeting.mnemofy.wav
        """
        ...
```

### Validation Requirements

✅ **Input Validation**:
- [ ] segments list not empty
- [ ] Each segment has 'start', 'end', 'text'
- [ ] start, end are numeric
- [ ] Total duration >= 30 seconds (raise ValueError if not)
- [ ] metadata has required fields
- [ ] metadata['duration'] is numeric

✅ **Output Validation**:
- [ ] Markdown is valid (can be parsed)
- [ ] All 7 sections present (even if empty)
- [ ] All timestamps in MM:SS format
- [ ] No hallucinated content (basic mode only)
- [ ] Proper formatting (headings, bullets, etc.)

### Error Handling

```python
# Example: Transcript too short
segments = [{'start': 0, 'end': 10, 'text': '...'}]  # 10 seconds
try:
    notes = StructuredNotesGenerator().generate(segments, metadata)
except ValueError as e:
    print(f"Transcript too short: {e}")
    # Output: "Transcript too short: minimum 30 seconds required (got 10)"

# Example: Missing metadata
try:
    notes = gen.generate(segments, {})  # empty metadata
except KeyError as e:
    print(f"Missing metadata: {e}")
    # Output: "Missing metadata: 'engine'"

# Example: Empty segments
try:
    notes = gen.generate([], metadata)
except IndexError:
    print("No segments to process")
```

### Usage in Pipeline

```python
from mnemofy.notes import StructuredNotesGenerator
from mnemofy.output_manager import OutputManager

# After transcription
segments = model.transcribe("audio.wav")
metadata = {
    'engine': 'faster-whisper',
    'model': 'base',
    'language': 'en',
    'duration': 95.5,
    'input_file': 'meeting.mp4'
}

# Generate notes
gen = StructuredNotesGenerator(mode="basic")
try:
    notes = gen.generate(segments, metadata)
    
    # Save notes
    manager = OutputManager("input.mp4", outdir="/out")
    manager.get_notes_path().write_text(notes)
except ValueError as e:
    if "30 seconds" in str(e):
        print(f"Skipping notes: {e}")
    else:
        raise
```

### Testing Acceptance Criteria

- [ ] generate() requires >= 30 seconds (raises ValueError)
- [ ] All 7 sections present in output
- [ ] Metadata section shows correct duration, language, engine
- [ ] Topics section divides transcript into logical segments
- [ ] Decisions section captures explicit decision keywords
- [ ] Action items section extracts owner + task + timestamp
- [ ] Concrete mentions section finds names, numbers, URLs
- [ ] Risks section captures conditional statements
- [ ] Questions section captures sentences with "?"
- [ ] Transcript links section has all 4 file types
- [ ] Error handling for edge cases:
  - [ ] Exactly 30 seconds (boundary)
  - [ ] 31 seconds (just over)
  - [ ] 1 second (too short)
  - [ ] No decisions found
  - [ ] No action items found
  - [ ] No concrete mentions found
- [ ] Deterministic output (same input → same output)
- [ ] No hallucination in basic mode
- [ ] Markdown valid (can be parsed)
- [ ] Achieve 90%+ code coverage
- [ ] Test with 5-minute, 1-hour, 4-hour transcripts

### Implementation Notes

**Dependencies**:
- `re` (stdlib) for regex (names, numbers, URLs, dates)
- `datetime` (stdlib) for timestamps
- No external dependencies required

**Key Implementation Details**:
1. **30-second check**: `total_duration = segments[-1]['end']` check >= 30
2. **Time formatting**: Convert float seconds to MM:SS (not HH:MM:SS for notes)
3. **Topic extraction**: Default to time-based buckets (5-minute chunks)
4. **Keyword detection**: Case-insensitive regex matching
5. **Basic mode strictness**: Quote original text, don't paraphrase

**LLM Mode (Stubbed)**:
```python
def generate(self, segments, metadata):
    if self.mode == NotesMode.BASIC:
        # ... basic extraction logic
    elif self.mode == NotesMode.LLM:
        raise NotImplementedError("LLM mode coming in future release")
```

---

**Status**: ✅ **CONTRACT DEFINED**

Implementation ready: `src/mnemofy/notes.py` (REFACTOR)

