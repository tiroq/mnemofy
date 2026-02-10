# Quickstart: Meeting Type Detection & LLM Notes

**Feature**: `003-meeting-type-llm`

Get started with automatic meeting type detection and structured notes generation in under 5 minutes.

---

## Basic Usage (No LLM Required)

The simplest way to use meeting type detection with **offline, deterministic** classification:

```bash
# Transcribe and generate notes with auto-detected meeting type
mnemofy path/to/meeting.mp3

# Output:
# - meeting.transcript.txt
# - meeting.notes.md (using detected template)
# - meeting.meeting-type.json (detection metadata)
```

The tool will:
1. Transcribe audio (existing functionality)
2. Auto-detect meeting type using keyword heuristics
3. Generate structured notes using the appropriate template
4. Display confidence and evidence for the detection

---

## Interactive Mode (Override Detection)

When run in a terminal, you can review and override the auto-detected type:

```bash
mnemofy meeting.mp3

# You'll see:
# ┌─ Meeting Type Detection ─────────────┐
# │ Detected: planning (confidence: 0.72)│
# │ Evidence: timeline, scope, estimate  │
# │                                       │
# │ Select meeting type:                  │
# │ ○ planning (recommended)              │
# │ ○ status                              │
# │ ○ design                              │
# │ ○ demo                                │
# └───────────────────────────────────────┘
# Use ↑↓ to navigate, Enter to confirm, Esc to use recommended
```

**Skip interactive mode** for scripts/automation:

```bash
mnemofy meeting.mp3 --no-interactive
```

---

## Explicit Meeting Type

Override auto-detection completely:

```bash
# Force a specific meeting type
mnemofy meeting.mp3 --meeting-type incident

# Use a custom template
mnemofy meeting.mp3 --meeting-type planning --template custom_planning.md
```

---

## LLM-Enhanced Notes (Optional)

For richer, more nuanced notes with inferred context and subtle decisions, enable LLM mode.

### Setup (One-Time)

#### Option 1: OpenAI

```bash
# Set API key via environment variable
export OPENAI_API_KEY="sk-..."

# Run with LLM-enhanced notes
mnemofy meeting.mp3 --llm

# Output shows:
# [llm] Using engine=openai, model=gpt-4o-mini
# [llm] Classification: planning (confidence: 0.85)
# [llm] Generating enhanced notes...
```

#### Option 2: Ollama (Local, Private)

```bash
# 1. Install Ollama: https://ollama.ai
# 2. Pull model:
ollama pull llama3.2:3b

# 3. Run with local LLM:
mnemofy meeting.mp3 --llm --llm-engine ollama --llm-model llama3.2:3b

# Output shows:
# [llm] Using engine=ollama, model=llama3.2:3b
# [llm] Classification: status (confidence: 0.78)
# [llm] Generating enhanced notes...
```

### Configuration File (Optional)

Save settings in `~/.config/mnemofy/config.toml`:

```toml
[llm]
engine = "openai"
model = "gpt-4o-mini"
timeout = 30
max_retries = 2

# Or for Ollama:
# engine = "ollama"
# model = "llama3.2:3b"
# base_url = "http://localhost:11434"
```

Then simply run:

```bash
export OPENAI_API_KEY="sk-..."  # Still required for API key
mnemofy meeting.mp3 --llm
```

**Security Note**: Never put API keys in config files. Always use environment variables.

---

## LLM Mode: Classification vs. Notes

You can use LLM for just classification or just notes generation, or both:

```bash
# LLM classification + LLM notes (default when --llm is used)
mnemofy meeting.mp3 --llm

# Heuristic classification + LLM notes
mnemofy meeting.mp3 --classify heuristic --llm

# LLM classification + basic (deterministic) notes
mnemofy meeting.mp3 --classify llm

# Disable classification (use explicit type), enable LLM notes
mnemofy meeting.mp3 --meeting-type planning --llm
```

---

## Understanding Output

### Notes File (meeting.notes.md)

```markdown
# Planning Session Meeting Notes

**Detected Type**: planning (confidence: 0.72)
**Evidence**: timeline, scope, estimate, Q2, milestone

## Goal/Outcome
Finalize Q2 product roadmap and resource allocation.

## Decisions
- **Use PostgreSQL for analytics database** ✓
  - Sources: @t=23:15-23:42
- **Push mobile app to Q3** ⚠️ _Unclear: Decision mentioned but not finalized_
  - Sources: @t=45:02-45:18

## Action Items
- **Alice: Draft technical design doc by Feb 15** [@t=34:22]
- **Bob: Schedule architecture review** [@t=34:35]

## Transcript References
- ref_001: @t=23:15-23:42 - "So we're going with PostgreSQL then?..."
- ref_002: @t=34:22-34:40 - "I'll draft the design doc by next Friday."
```

### Metadata File (meeting.meeting-type.json)

```json
{
  "detected_type": "planning",
  "confidence": 0.72,
  "evidence": ["timeline", "scope", "estimate", "Q2", "milestone"],
  "secondary_types": [
    {"type": "status", "score": 0.48},
    {"type": "design", "score": 0.31}
  ],
  "engine": "heuristic",
  "timestamp": "2026-02-10T14:32:15Z"
}
```

---

## Template Customization

### Using Built-in Templates

Nine templates included:
- `status.md` - Status updates, blockers, progress
- `planning.md` - Goals, scope, timelines, risks
- `design.md` - Problem statement, solutions, trade-offs
- `demo.md` - Features shown, feedback, next steps
- `talk.md` - Presentation content, Q&A
- `incident.md` - Timeline, root cause, impact, remediation
- `discovery.md` - Questions, findings, unknowns
- `oneonone.md` - Feedback, growth, career discussion
- `brainstorm.md` - Ideas, creativity, exploration

### Custom Templates

1. Copy a built-in template:
   ```bash
   mkdir -p ~/.config/mnemofy/templates
   cp /path/to/mnemofy/src/mnemofy/templates/planning.md ~/.config/mnemofy/templates/my_planning.md
   ```

2. Edit the template (Jinja2 + Markdown):
   ```jinja2
   # My Custom Planning Template

   ## Objectives
   {{ type_specific.goals | default("Not discussed") }}

   ## Decisions
   {% for decision in decisions %}
   - {{ decision.text }} [@t={{ decision.references[0].start_time }}]
   {% endfor %}
   ```

3. Use your custom template:
   ```bash
   mnemofy meeting.mp3 --template my_planning.md
   ```

Templates in `~/.config/mnemofy/templates/` override built-in templates.

---

## Troubleshooting

### Q: Low confidence detection (< 0.6)?

**A**: Review the evidence and select manually:
```bash
# Interactive mode shows all candidates
mnemofy meeting.mp3

# Or specify explicitly:
mnemofy meeting.mp3 --meeting-type status
```

### Q: LLM not working?

**A**: Check:
1. API key set: `echo $OPENAI_API_KEY`
2. Network connectivity: `curl https://api.openai.com`
3. Ollama running: `curl http://localhost:11434/api/version`

Tool automatically falls back to heuristic mode if LLM fails.

### Q: Wrong template selected?

**A**: Override manually:
```bash
mnemofy meeting.mp3 --meeting-type design
```

### Q: Want to see detection details?

**A**: Check the metadata file:
```bash
cat meeting.meeting-type.json | jq
```

---

## Advanced Examples

### Batch Processing (Non-Interactive)

```bash
for file in meetings/*.mp3; do
  mnemofy "$file" --no-interactive --llm
done
```

### Custom LLM Endpoint (Enterprise Gateway)

```bash
mnemofy meeting.mp3 \
  --llm \
  --llm-engine openai_compat \
  --llm-base-url https://api.company.com/v1 \
  --llm-model gpt-4o
```

### Verbose Output (Debugging)

```bash
mnemofy meeting.mp3 --llm --verbose

# Shows:
# [llm] Request duration: 3.2s
# [llm] Response size: 1847 tokens
# [llm] Classification confidence: 0.83
```

---

## Configuration Summary

### Precedence Order (Highest to Lowest)

1. **CLI flags**: `--llm-model gpt-4o`
2. **Environment variables**: `MNEMOFY_LLM_MODEL=gpt-4o`
3. **Config file**: `~/.config/mnemofy/config.toml`
4. **Defaults**: `gpt-4o-mini` (OpenAI), `llama3.2:3b` (Ollama)

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` |
| `MNEMOFY_LLM_API_KEY` | Generic LLM API key | `sk-...` |
| `MNEMOFY_LLM_ENGINE` | Engine type | `openai`, `ollama` |
| `MNEMOFY_LLM_MODEL` | Model name | `gpt-4o-mini` |
| `MNEMOFY_LLM_BASE_URL` | API endpoint | `http://localhost:11434` |
| `MNEMOFY_LLM_TIMEOUT` | Timeout (seconds) | `30` |
| `MNEMOFY_LLM_RETRIES` | Max retries | `2` |

---

## Next Steps

- See [data-model.md](./data-model.md) for detailed schema
- See [contracts/](./contracts/) for JSON schemas
- Customize templates for your workflow
- Integrate into CI/CD pipelines
- Explore meeting type detection patterns

**Need help?** File an issue or check the docs.
