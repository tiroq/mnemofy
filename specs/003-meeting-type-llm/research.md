# Research: Meeting Type Detection & Pluggable LLM Engines

**Feature**: `003-meeting-type-llm` | **Date**: 2026-02-10

This document captures technical research conducted to resolve design decisions and technology choices for implementing meeting type detection with pluggable LLM backends.

---

## 1. Jinja2 Template Rendering for Markdown

### Decision
Use Jinja2 with `autoescape=False` for rendering Markdown templates with structured meeting notes.

### Rationale
- **Mature & Stable**: Jinja2 is the industry-standard Python templating engine with excellent documentation
- **Markdown-Safe**: With autoescape disabled, Jinja2 doesn't mangle Markdown syntax (links, code blocks, lists)
- **Package Resources**: Can bundle templates with the package using `importlib.resources` (Python 3.9+)
- **User Override**: Simple override mechanism by checking user config directory first, falling back to bundled templates

### Implementation Pattern
```python
from jinja2 import Environment, FileSystemLoader, select_autoescape
from importlib import resources
import os

def get_template_env():
    # Check user override first
    user_template_dir = os.path.expanduser("~/.config/mnemofy/templates")
    bundled_template_dir = resources.files("mnemofy").joinpath("templates")
    
    loader = FileSystemLoader([user_template_dir, str(bundled_template_dir)])
    env = Environment(
        loader=loader,
        autoescape=False,  # Don't escape Markdown
        trim_blocks=True,
        lstrip_blocks=True
    )
    return env
```

### Alternatives Considered
- **String formatting (f-strings)**: Rejected - too brittle for complex multiline templates with conditionals
- **Manual string concatenation**: Rejected - unmaintainable for 9 different templates
- **Mustache/Handlebars**: Rejected - Jinja2 is more Pythonic and widely adopted

---

## 2. HTTP Client for LLM APIs

### Decision
Use **httpx** for LLM API communication.

### Rationale
- **Timeout Support**: First-class timeout configuration (connect, read, write)
- **Async Ready**: Supports async/await for future optimization (not used in MVP but valuable)
- **HTTP/2**: Built-in HTTP/2 support for better performance with modern APIs
- **Retry Logic**: Easy integration with retry libraries (tenacity)
- **Modern**: Active development, better than `requests` for new projects

### Implementation Pattern
```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_llm_api(url, payload, api_key, timeout=30):
    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        response.raise_for_status()
        return response.json()
```

### Alternatives Considered
- **requests**: Rejected - lacks async support, timeout handling less robust
- **aiohttp**: Rejected - full async adds complexity for CLI tool with sequential workflow
- **urllib**: Rejected - too low-level, manual connection pooling required

---

## 3. Heuristic Classification Algorithm

### Decision
Use **weighted TF-IDF with structural feature boosting** for meeting type classification.

### Rationale
- **Deterministic**: Same transcript always produces same classification
- **Explainable**: Evidence keywords directly map to confidence scores
- **Offline**: No external dependencies, fast execution
- **Python Native**: scikit-learn provides TfidfVectorizer (or custom implementation for minimal dependencies)

### Algorithm
1. **Preprocessing**: Tokenize transcript, remove stopwords, extract bigrams/trigrams
2. **Feature Extraction**:
   - TF-IDF scores for keywords from meeting-type dictionaries
   - Structural features: question density (questions/total sentences)
   - Temporal markers: count of timeline vocab ("tomorrow", "next week", "Q2")
   - Estimate markers: count of estimate vocab ("roughly", "about X hours")
3. **Scoring**: Weighted sum per meeting type
4. **Confidence**: Normalize top score to 0-1 range, considering margin from second-place

### Meeting Type Keyword Dictionaries
```python
MEETING_TYPE_KEYWORDS = {
    "status": ["update", "progress", "blocker", "completed", "working on", "stuck"],
    "planning": ["goal", "scope", "timeline", "milestone", "estimate", "deadline"],
    "design": ["architecture", "approach", "pattern", "trade-off", "options", "pros and cons"],
    "demo": ["show", "walk through", "feature", "released", "see here", "check out"],
    "talk": ["presentation", "introduce", "explain", "overview", "background"],
    "incident": ["outage", "issue", "root cause", "impact", "postmortem", "timeline"],
    "discovery": ["explore", "investigate", "understand", "why", "clarify", "research"],
    "oneonone": ["feedback", "growth", "career", "1:1", "one-on-one", "check in"],
    "brainstorm": ["ideas", "what if", "could we", "brainstorm", "creativity", "options"]
}
```

### Alternatives Considered
- **Naive Bayes**: Rejected - requires training data, not deterministic enough
- **Pre-trained transformer**: Rejected - violates offline-first, too heavy for this task
- **Rule-based (simple keyword matching)**: Rejected - too brittle, low accuracy

---

## 4. High-Signal Segment Extraction

### Decision
Use **decision marker regex + sliding window** to extract segments for LLM classification.

### Rationale
- **Token Optimization**: Sending full 2-hour transcript wastes tokens; first 10-15 min + high-signal segments reduces cost
- **Decision-Focused**: Aligns with "grounded notes" requirement (FR-011)
- **Simple Implementation**: Regex patterns for markers, no ML required

### Extraction Strategy
```python
import re

DECISION_MARKERS = [
    r"\b(we'?ll|let'?s|agreed?|decided?|going to)\b",
    r"\b(action item|TODO|will do|need to)\b",
    r"\b(should we|what if|could we)\b"
]

def extract_high_signal_segments(transcript, max_segments=5):
    """Extract segments containing decision markers."""
    segments = []
    for marker in DECISION_MARKERS:
        matches = re.finditer(marker, transcript, re.IGNORECASE)
        for match in matches:
            # Extract ±50 words context around marker
            start = max(0, match.start() - 250)
            end = min(len(transcript), match.end() + 250)
            segments.append(transcript[start:end])
    
    # Deduplicate and limit to top N by diversity
    return deduplicate_segments(segments, max_segments)
```

### Alternatives Considered
- **Speaker transition density**: Rejected - not all transcripts have speaker labels
- **All segments with keywords**: Rejected - still too many tokens
- **Random sampling**: Rejected - may miss critical context

---

## 5. TOML Configuration Management

### Decision
Use **tomli** (Python 3.10) or **tomllib** (Python 3.11+) for reading TOML, **tomli-w** for writing.

### Rationale
- **Standard Library**: tomllib is built-in for Python 3.11+
- **Lightweight**: tomli is ~200 lines, minimal dependency for older Python
- **Precedence Chain**: Easy to implement CLI > env vars > file > defaults

### Configuration Loading Pattern
```python
import os
import sys
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

def load_config():
    config = DEFAULT_CONFIG.copy()
    
    # 1. Load from file
    config_path = os.path.expanduser("~/.config/mnemofy/config.toml")
    if os.path.exists(config_path):
        with open(config_path, "rb") as f:
            file_config = tomllib.load(f)
            config.update(file_config.get("llm", {}))
    
    # 2. Override with env vars
    for key in ["engine", "model", "base_url", "timeout", "retries"]:
        env_key = f"MNEMOFY_LLM_{key.upper()}"
        if env_key in os.environ:
            config[key] = os.environ[env_key]
    
    # 3. API keys ONLY from env vars (never from file)
    config["api_key"] = os.environ.get("OPENAI_API_KEY") or os.environ.get("MNEMOFY_LLM_API_KEY")
    
    # 4. CLI flags override all (handled in CLI argument parsing)
    return config
```

### Security Note
- Config file validation: If API key found in TOML, raise error with clear message
- File permissions: Not enforced (user responsibility), but documented in quickstart

### Alternatives Considered
- **JSON**: Rejected - no comments, harder for humans to edit
- **YAML**: Rejected - overcomplicated for simple key-value config, security issues (arbitrary code execution)
- **INI**: Rejected - no nested structures, outdated

---

## 6. Interactive TUI Menu (Arrow Key Navigation)

### Decision
Use **prompt_toolkit** for building the interactive meeting type selection menu.

### Rationale
- **Rich TUI**: Built-in support for arrow keys, colors, validation
- **Cross-Platform**: Works on Windows, macOS, Linux
- **Minimal Code**: High-level abstractions for common patterns
- **Existing Dependency**: Already used in mnemofy for model_menu.py

### Implementation Pattern
```python
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog

def select_meeting_type(candidates):
    """Interactive meeting type selection with arrow key navigation."""
    values = [(mtype, f"{mtype} (confidence: {score:.2f})") 
              for mtype, score in candidates]
    
    result = radiolist_dialog(
        title="Meeting Type Detection",
        text=f"Detected: {candidates[0][0]} (recommended)\nSelect meeting type:",
        values=values
    ).run()
    
    return result or candidates[0][0]  # Default to recommended if Esc pressed
```

### Performance
- <200ms latency requirement easily met (prompt_toolkit is highly optimized)
- No blocking I/O in menu rendering

### Alternatives Considered
- **inquirer**: Rejected - less actively maintained than prompt_toolkit
- **pick**: Rejected - limited customization, fewer features
- **Custom curses**: Rejected - too low-level, platform-specific edge cases

---

## 7. LLM Engine Abstraction

### Decision
Use **Abstract Base Class (ABC)** pattern for pluggable LLM backends.

### Rationale
- **Type Safety**: Python's ABC ensures each engine implements required methods
- **Testability**: Easy to mock LLM engines in tests
- **Extensibility**: Adding new engines (Anthropic, Cohere) requires minimal code
- **Error Handling**: Centralized fallback logic in base class

### Interface Design
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMEngine(ABC):
    @abstractmethod
    def classify_meeting_type(self, transcript_window: str) -> Dict[str, Any]:
        """Returns: {type, confidence, evidence, notes_focus}"""
        pass
    
    @abstractmethod
    def generate_notes(self, transcript: str, meeting_type: str, template: str) -> Dict[str, Any]:
        """Returns: {decisions, action_items, mentions, unclear_items}"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Returns True if engine is reachable and configured."""
        pass

class OpenAIEngine(LLMEngine):
    def __init__(self, api_key, model="gpt-4o-mini", base_url=None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
    
    # Implement abstract methods...

class OllamaEngine(LLMEngine):
    def __init__(self, model="llama3.2:3b", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    # Implement abstract methods...
```

### Fallback Strategy
```python
def get_llm_engine(config):
    """Factory with graceful degradation."""
    try:
        if config["engine"] == "openai":
            engine = OpenAIEngine(config["api_key"], config["model"])
        elif config["engine"] == "ollama":
            engine = OllamaEngine(config["model"], config["base_url"])
        
        if not engine.health_check():
            raise ConnectionError("LLM engine unreachable")
        
        return engine
    except Exception as e:
        logger.warning(f"LLM unavailable: {e}. Falling back to heuristic mode.")
        return None  # Caller handles None by using heuristic classifier
```

### Alternatives Considered
- **LangChain**: Rejected - too heavy, unnecessary abstraction layers
- **LiteLLM**: Rejected - adds external dependency for simple use case
- **Direct API calls**: Rejected - harder to test, no abstraction for multi-backend support

---

## 8. Template Placeholder Structure

### Decision
Use **nested data structures** passed to Jinja2 templates for maximum flexibility.

### Rationale
- **Type-Safe**: Python dataclasses or dicts with defined schemas
- **Validation**: Can validate structure before rendering
- **Clarity**: Template placeholders match data model directly

### Template Data Schema
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TranscriptReference:
    start_time: str  # "MM:SS"
    end_time: str
    text_snippet: str

@dataclass
class GroundedItem:
    text: str
    status: str  # "confirmed" | "unclear"
    reason: Optional[str]
    references: List[TranscriptReference]

@dataclass
class MeetingNotes:
    meeting_type: str
    confidence: float
    evidence: List[str]
    decisions: List[GroundedItem]
    action_items: List[GroundedItem]
    mentions: List[GroundedItem]
    type_specific: dict  # Varies by meeting type (e.g., "blockers" for status)
```

### Jinja2 Template Example (status.md)
```markdown
# Status Update Meeting Notes

**Detected Type**: {{ meeting_type }} (confidence: {{ confidence }})
**Evidence**: {{ evidence | join(", ") }}

## Progress
{{ type_specific.progress | default("No progress items extracted") }}

## Blockers
{% for blocker in type_specific.blockers %}
- {{ blocker.text }} [@t={{ blocker.references[0].start_time }}]({{ blocker.references[0].start_time }})
{% endfor %}

## Decisions
{% for decision in decisions %}
- **{{ decision.text }}** {% if decision.status == "unclear" %}⚠️ _Unclear: {{ decision.reason }}_{% endif %}
  - Sources: {% for ref in decision.references %}@t={{ ref.start_time }}-{{ ref.end_time }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}
```

### Alternatives Considered
- **Flat key-value pairs**: Rejected - doesn't support nested structures (lists of items with metadata)
- **JSON templates**: Rejected - less human-readable, harder to edit for users
- **Custom DSL**: Rejected - unnecessary complexity, Jinja2 is mature and well-known

---

## Summary of Key Technology Decisions

| Component | Technology | Reason |
|-----------|------------|--------|
| Template Rendering | Jinja2 | Industry standard, Markdown-safe, user override support |
| HTTP Client | httpx | Modern, timeouts, retry-ready, async-capable |
| Configuration | tomli/tomllib + tomli-w | TOML is human-friendly, Python 3.11+ has built-in support |
| Heuristic Classifier | Weighted TF-IDF + structural features | Deterministic, explainable, offline-capable |
| High-Signal Extraction | Regex markers + sliding window | Token-efficient, simple, decision-focused |
| Interactive Menu | prompt_toolkit | Cross-platform, arrow keys, already in project |
| LLM Abstraction | ABC pattern | Type-safe, testable, extensible |
| Template Data | Dataclasses + nested dicts | Type-safe, validation-ready, Jinja2-compatible |

**All decisions align with constitutional principles**: deterministic-first, local-first, transparent, safe-by-default.
