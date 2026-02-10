# Example Meeting Transcripts

This directory contains sample transcripts demonstrating different meeting types.

## Available Examples

### 1. Status Meeting (`status-meeting-example.txt`)
Daily standup or status update with progress reports and blockers.

### 2. Planning Meeting (`planning-meeting-example.txt`)
Sprint planning or roadmap discussion with scope and timeline.

### 3. Design Meeting (`design-meeting-example.txt`)
Technical design review with architecture decisions.

### 4. Demo Meeting (`demo-meeting-example.txt`)
Product demo or feature showcase.

### 5. Incident Review (`incident-meeting-example.txt`)
Postmortem or incident analysis with root cause.

## Usage

These examples can be used to:
- Test meeting type detection
- Understand type-specific note templates
- Verify LLM classification accuracy

## Testing Detection

```bash
# Simulate processing (requires actual audio file)
mnemofy transcribe audio.mp3 --meeting-type auto

# The system should detect the appropriate type based on content patterns
```
