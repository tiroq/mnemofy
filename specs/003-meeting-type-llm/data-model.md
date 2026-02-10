# Data Model: Meeting Type Detection & Pluggable LLM Engines

**Feature**: `003-meeting-type-llm` | **Date**: 2026-02-10

This document defines the data structures, relationships, and validation rules for meeting type detection and template-based notes generation.

---

## Entity Relationship Overview

```
Transcript (input)
    ↓
ClassificationResult ──→ MeetingType
    ↓                       ↓
NotesTemplate ←───────────┘
    ↓
MeetingNotes (output)
    ├── GroundedItem (Decision)
    ├── GroundedItem (Action Item)
    ├── GroundedItem (Mention)
    └── TranscriptReference
```

---

## Core Entities

### 1. MeetingType

Represents one of the nine supported meeting categories.

**Attributes**:
- `type_id` (str): One of `["status", "planning", "design", "demo", "talk", "incident", "discovery", "oneonone", "brainstorm"]`
- `display_name` (str): Human-readable name (e.g., "Status Update", "Planning Session")
- `template_name` (str): Filename of associated Jinja2 template (e.g., "status.md")
- `keywords` (List[str]): Heuristic detection keywords
- `bigrams` (List[str]): Two-word phrases for detection (optional)
- `structural_markers` (Dict[str, Any]): Expected patterns (e.g., `{"high_question_density": true}`)

**Validation Rules**:
- `type_id` MUST be one of the nine supported types
- `template_name` MUST reference an existing template file
- `keywords` MUST contain at least 3 entries
- All fields are immutable (loaded from static config)

**Example**:
```python
{
    "type_id": "status",
    "display_name": "Status Update",
    "template_name": "status.md",
    "keywords": ["update", "progress", "blocker", "completed", "working on", "stuck"],
    "bigrams": ["status update", "working on", "next week"],
    "structural_markers": {"question_density_threshold": 0.1}
}
```

---

### 2. ClassificationResult

Output of the meeting type detection process.

**Attributes**:
- `detected_type` (str): The primary meeting type ID
- `confidence` (float): Confidence score (0.0 - 1.0)
- `evidence` (List[str]): Keywords/phrases that led to classification
- `secondary_types` (List[Tuple[str, float]]): Alternative types with scores (up to 5)
- `engine` (str): Detection engine used (`"heuristic"` or `"llm"`)
- `timestamp` (str): ISO 8601 timestamp of classification

**Validation Rules**:
- `confidence` MUST be in range [0.0, 1.0]
- `detected_type` MUST be valid MeetingType.type_id
- `evidence` MUST contain at least 1 entry
- `secondary_types` sorted by score descending
- If `confidence < 0.5`, `secondary_types` MUST have at least 3 entries

**State Transitions**:
- **High Confidence (≥0.6)**: Auto-accept → proceed to notes generation
- **Medium Confidence (0.5-0.6)**: Display warning → allow override → proceed
- **Low Confidence (<0.5)**: Require selection → user picks from secondary_types

**Example**:
```python
{
    "detected_type": "planning",
    "confidence": 0.72,
    "evidence": ["timeline", "milestone", "estimate", "scope", "Q2 goals"],
    "secondary_types": [
        ("status", 0.48),
        ("design", 0.31),
        ("brainstorm", 0.19)
    ],
    "engine": "heuristic",
    "timestamp": "2026-02-10T14:32:15Z"
}
```

---

### 3. LLMConfiguration

Settings for LLM backend connection and behavior.

**Attributes**:
- `engine_type` (str): One of `["openai", "ollama", "openai_compat"]`
- `model` (str): Model identifier (e.g., "gpt-4o-mini", "llama3.2:3b")
- `base_url` (str): API endpoint (optional for OpenAI default)
- `api_key_env_var` (str): Name of environment variable containing API key (e.g., "OPENAI_API_KEY")
- `timeout` (int): Request timeout in seconds (default: 30)
- `max_retries` (int): Maximum retry attempts (default: 2)
- `temperature` (float): LLM temperature (default: 0.0 for deterministic)
- `enabled` (bool): Whether LLM features are active

**Validation Rules**:
- `engine_type` MUST be one of supported types
- `model` MUST NOT be empty string
- `timeout` MUST be > 0
- `max_retries` MUST be ≥ 0
- `temperature` MUST be in range [0.0, 2.0]
- `api_key_env_var` MUST reference existing env var for OpenAI/openai_compat engines
- API key value MUST NEVER be stored in this config (only env var name)

**Defaults**:
```python
{
    "engine_type": None,  # LLM disabled by default
    "model": "gpt-4o-mini",  # If OpenAI enabled
    "base_url": "https://api.openai.com/v1",
    "api_key_env_var": "OPENAI_API_KEY",
    "timeout": 30,
    "max_retries": 2,
    "temperature": 0.0,
    "enabled": False
}
```

**Precedence Chain** (highest to lowest):
1. CLI flags (`--llm-engine`, `--llm-model`, etc.)
2. Environment variables (`MNEMOFY_LLM_ENGINE`, `MNEMOFY_LLM_MODEL`, etc.)
3. Config file (~/.config/mnemofy/config.toml under `[llm]` section)
4. Built-in defaults (above)

---

### 4. TranscriptReference

Links a note item to its source location in the transcript.

**Attributes**:
- `reference_id` (str): Unique identifier (e.g., "ref_001")
- `start_time` (str): Timestamp in format "MM:SS" or "HH:MM:SS"
- `end_time` (str): Timestamp in same format
- `speaker` (Optional[str]): Speaker name/ID if available
- `text_snippet` (str): Excerpt from transcript (50-200 chars)

**Validation Rules**:
- `start_time` and `end_time` MUST be valid timestamp strings
- `end_time` MUST be ≥ `start_time`
- `text_snippet` MUST be non-empty
- `text_snippet` SHOULD be exact quote from transcript (no paraphrasing)

**Example**:
```python
{
    "reference_id": "ref_004",
    "start_time": "12:45",
    "end_time": "13:02",
    "speaker": "Alice",
    "text_snippet": "Let's prioritize the API refactor for Q2. I'll take ownership of the design doc."
}
```

---

### 5. GroundedItem

A Decision, Action Item, or Mention extracted from the transcript with evidence.

**Attributes**:
- `text` (str): The extracted claim or item
- `status` (str): One of `["confirmed", "unclear"]`
- `reason` (Optional[str]): Explanation if status is "unclear"
- `references` (List[TranscriptReference]): Source timestamps (at least 1 required)
- `item_type` (str): One of `["decision", "action_item", "mention"]`
- `metadata` (Dict[str, Any]): Optional additional data (e.g., `{"owner": "Alice"}` for action items)

**Validation Rules**:
- `text` MUST be non-empty
- `status` MUST be one of valid statuses
- If `status == "unclear"`, `reason` MUST be provided
- `references` MUST contain at least 1 TranscriptReference
- `item_type` MUST be one of valid types
- For LLM-generated items: MUST have valid references (FR-011)

**Example (Decision)**:
```python
{
    "text": "Team agreed to use PostgreSQL for the analytics database",
    "status": "confirmed",
    "reason": None,
    "references": [
        {
            "reference_id": "ref_007",
            "start_time": "23:15",
            "end_time": "23:42",
            "speaker": "Bob",
            "text_snippet": "So we're going with PostgreSQL then? Everyone agreed? Yep, sounds good."
        }
    ],
    "item_type": "decision",
    "metadata": {}
}
```

**Example (Unclear Action Item)**:
```python
{
    "text": "Someone should update the documentation",
    "status": "unclear",
    "reason": "No explicit owner assigned; mentioned casually without commitment",
    "references": [
        {
            "reference_id": "ref_012",
            "start_time": "34:05",
            "end_time": "34:12",
            "speaker": "Charlie",
            "text_snippet": "Yeah, we should probably update the docs at some point."
        }
    ],
    "item_type": "action_item",
    "metadata": {"owner": null}
}
```

---

### 6. NotesTemplate

Defines the structure and rendering rules for meeting type-specific notes.

**Attributes**:
- `template_id` (str): Matches MeetingType.template_name (e.g., "status.md")
- `sections` (List[str]): Ordered list of section names
- `required_sections` (List[str]): Sections that MUST be present (invariants)
- `optional_sections` (List[str]): Sections specific to this meeting type
- `jinja2_template_path` (str): Path to .md template file

**Validation Rules**:
- `required_sections` MUST include: `["Decisions", "Action Items", "Concrete Mentions", "Transcript References"]` (FR-009)
- `sections` preserves order for rendering
- Template file MUST exist at specified path
- Template MUST be valid Jinja2 syntax

**Invariant Sections** (all templates):
1. **Decisions**: List of GroundedItem with type="decision"
2. **Action Items**: List of GroundedItem with type="action_item"
3. **Concrete Mentions**: List of GroundedItem with type="mention"
4. **Transcript References**: All TranscriptReference objects used

**Type-Specific Sections** (examples):
- **Status**: Progress, Blockers, Next Steps
- **Planning**: Goal/Outcome, Scope, Estimates/Timeline, Risks
- **Incident**: Timeline, Root Cause, Impact, Remediation
- **Design**: Problem Statement, Proposed Solution, Trade-offs, Open Questions

**Example**:
```python
{
    "template_id": "planning.md",
    "sections": [
        "Goal/Outcome",
        "Scope",
        "Options Considered",
        "Estimates/Timeline",
        "Risks",
        "Decisions",
        "Action Items",
        "Concrete Mentions",
        "Transcript References"
    ],
    "required_sections": ["Decisions", "Action Items", "Concrete Mentions", "Transcript References"],
    "optional_sections": ["Goal/Outcome", "Scope", "Options Considered", "Estimates/Timeline", "Risks"],
    "jinja2_template_path": "src/mnemofy/templates/planning.md"
}
```

---

### 7. MeetingNotes

The final output document containing structured notes.

**Attributes**:
- `meeting_type` (str): Selected MeetingType.type_id
- `confidence` (float): From ClassificationResult
- `evidence` (List[str]): From ClassificationResult
- `template_used` (str): Template filename
- `generated_at` (str): ISO 8601 timestamp
- `engine_info` (Dict[str, str]): `{"classification": "heuristic|llm", "notes": "basic|llm"}`
- `decisions` (List[GroundedItem]): Extracted decisions
- `action_items` (List[GroundedItem]): Extracted action items
- `mentions` (List[GroundedItem]): Extracted mentions
- `type_specific_content` (Dict[str, Any]): Content for optional sections (varies by meeting type)
- `transcript_references` (List[TranscriptReference]): All unique references used

**Validation Rules**:
- All invariant sections MUST be present (even if empty lists)
- `decisions`, `action_items`, `mentions` MUST be lists of GroundedItem
- `transcript_references` MUST include all references from grounded items
- `type_specific_content` keys MUST match template's optional_sections

**Example**:
```python
{
    "meeting_type": "status",
    "confidence": 0.68,
    "evidence": ["update", "blocker", "progress", "working on"],
    "template_used": "status.md",
    "generated_at": "2026-02-10T15:20:33Z",
    "engine_info": {
        "classification": "heuristic",
        "notes": "basic"
    },
    "decisions": [
        {
            "text": "Push release to next week due to testing delays",
            "status": "confirmed",
            "references": [{"reference_id": "ref_003", "start_time": "08:12", ...}],
            "item_type": "decision",
            "metadata": {}
        }
    ],
    "action_items": [
        {
            "text": "Alice will coordinate with QA on test plan",
            "status": "confirmed",
            "references": [{"reference_id": "ref_009", "start_time": "14:22", ...}],
            "item_type": "action_item",
            "metadata": {"owner": "Alice"}
        }
    ],
    "mentions": [...],
    "type_specific_content": {
        "progress": "Feature X completed, PR merged",
        "blockers": ["Waiting on design review", "Flaky test in CI"],
        "next_steps": "Complete testing, schedule release for next Monday"
    },
    "transcript_references": [
        {"reference_id": "ref_003", ...},
        {"reference_id": "ref_009", ...}
    ]
}
```

---

## Data Flow Summary

```
1. INPUT: Transcript (existing entity)
   ↓
2. CLASSIFY: MeetingType detection
   → Produces: ClassificationResult
   ↓
3. SELECT: User confirmation (interactive mode) or auto-accept (high confidence)
   → Finalizes: MeetingType selection
   ↓
4. GENERATE: Notes extraction (basic or LLM mode)
   → Creates: GroundedItem[] + TranscriptReference[]
   ↓
5. RENDER: Template rendering
   → Uses: NotesTemplate + MeetingNotes data
   ↓
6. OUTPUT: *.notes.md file + optional *.meeting-type.json metadata
```

---

## Storage & Persistence

### Files Created
- **{input}.notes.md**: Rendered Markdown notes (primary output)
- **{input}.meeting-type.json**: Classification metadata (optional, for debugging)

### Configuration Files
- **~/.config/mnemofy/config.toml**: User settings (engine, model, timeouts)
  - MUST NOT contain API keys
  - Example:
    ```toml
    [llm]
    engine = "openai"
    model = "gpt-4o-mini"
    timeout = 30
    max_retries = 2
    ```

### Template Storage
- **Bundled**: `src/mnemofy/templates/*.md` (included with package)
- **User Overrides**: `~/.config/mnemofy/templates/*.md` (check first, fallback to bundled)

---

## Validation Summary

| Entity | Critical Validations |
|--------|---------------------|
| MeetingType | Type ID in allowed set, template exists |
| ClassificationResult | Confidence [0,1], evidence non-empty, low confidence → multiple candidates |
| LLMConfiguration | No API keys in config objects, engine type valid, timeout > 0 |
| TranscriptReference | Timestamps valid format, end ≥ start, snippet non-empty |
| GroundedItem | Unclear → reason required, references ≥ 1, LLM mode → valid timestamps |
| NotesTemplate | Invariant sections present, template file exists, valid Jinja2 |
| MeetingNotes | All invariant sections present, references deduplicated, engine info logged |

All validations enforce **FR-009** (invariant sections), **FR-011** (grounded references), **FR-016** (API key security), and **FR-013** (unclear status handling).
