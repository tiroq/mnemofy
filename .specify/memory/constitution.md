<!--
SYNC IMPACT REPORT
==================
Version Change: 1.0.0 → 1.1.0
Date: 2026-02-10

MINOR version bump: Added expanded guidance and structure without changing core principles.

Modified Principles:
  - All 10 principles enhanced with formal Requirements and Rationale sections
  - No principle definitions changed, only documentation expanded

Added Sections:
  - Sync Impact Report (this header)
  - Requirements subsections for each principle
  - Rationale subsections for each principle
  - Expanded Non-Goals with rationale
  - Expanded Definition of "Done" with consequences
  - Governance section with amendment process
  - Version metadata footer

Removed Sections: None

Templates Requiring Updates:
  ✅ constitution-template.md - already aligned
  ✅ plan-template.md - reviewed, aligns with principles
  ✅ spec-template.md - reviewed, aligns with principles
  ✅ tasks-template.md - reviewed, aligns with principles

Follow-up TODOs: None - all templates verified for compliance.
-->

# mnemofy Constitution

## Purpose
mnemofy exists to reliably transform spoken conversations into structured, inspectable memory.
Its primary goal is to help users preserve meaning, decisions, and context from audio or video sources with minimal friction and maximum transparency.

---

## Core Principles

### 1. User Control Over Automation
Automation must never remove user agency.

**Requirements:**
- Automatic decisions must be explainable.
- Any automatic choice must be overridable.
- Explicit user input always takes precedence over heuristics.

**Rationale:** Users trust tools that respect their agency. Black-box automation erodes trust and prevents learning.

---

### 2. Safe-by-Default Execution
mnemofy must avoid surprising failures.

**Requirements:**
- The tool must not crash due to insufficient system resources.
- Resource constraints must be detected before execution.
- When failure is unavoidable, errors must be explicit, human-readable, and actionable.

**Rationale:** Silent failures and cryptic errors destroy user confidence. Safety-first design prevents data loss and frustration.

---

### 3. Transparency Over Magic
The system must explain *what it is doing and why*.

**Requirements:**
- Model recommendations must include reasoning.
- No silent fallbacks.
- No hidden downloads or background execution without user awareness.

**Rationale:** Understanding builds trust. Users should never wonder "what is this tool doing right now?"

---

### 4. Deterministic First, Intelligent Second
Core functionality must be deterministic.

**Requirements:**
- Transcription output must always be reproducible given the same inputs.
- AI-based interpretation must be layered on top, never replace raw outputs.
- Raw transcripts and timestamps must always be preserved.

**Rationale:** Non-deterministic systems are impossible to debug or verify. Intelligence is valuable, but predictability is essential.

---

### 5. Local-First by Default
mnemofy prioritizes local execution.

**Requirements:**
- Local inference is the default mode.
- Remote APIs are opt-in, never mandatory.
- The tool must remain functional offline when local models are available.

**Rationale:** Privacy, cost control, and offline capability matter. Cloud dependencies create vendor lock-in and privacy concerns.

---

### 6. Progressive Disclosure of Complexity
Beginner users should succeed with zero configuration.
Advanced users must have full control.

**Requirements:**
- Sensible defaults for first-time users.
- Advanced flags must exist but not be required.
- Interactive flows should guide, not overwhelm.

**Rationale:** Accessibility and power are not mutually exclusive. Tools should grow with user expertise.

---

### 7. Performance Is a Feature
Efficiency is not optional.

**Requirements:**
- CPU-friendly operation is required.
- Memory usage must be bounded and predictable.
- Faster solutions are preferred when quality is equal.

**Rationale:** Performance directly impacts usability. Slow tools don't get used, regardless of features.

---

### 8. Explicit Over Implicit Persistence
Nothing is remembered without consent.

**Requirements:**
- Configuration persistence must be opt-in.
- Saved preferences must be visible and editable.
- No telemetry or hidden state.

**Rationale:** User data sovereignty is non-negotiable. Hidden state creates security risks and trust issues.

---

### 9. Media-Agnostic Input
Input format must not restrict usefulness.

**Requirements:**
- Any media supported by ffmpeg is valid input.
- Video inputs must be treated as first-class citizens.
- Audio extraction must be automatic and loss-aware.

**Rationale:** Users have diverse media sources. Format restrictions create unnecessary friction.

---

### 10. OSS Quality Bar
mnemofy is an open-source project and must behave like one.

**Requirements:**
- Clear documentation is mandatory.
- CLI contracts must be stable.
- Breaking changes require explicit justification.

**Rationale:** Open source means community accountability. Quality is not optional for projects others depend on.

---

## Non-Goals

The following are explicitly **out of scope** for mnemofy:

- **Real-time transcription guarantees**: mnemofy optimizes for quality over speed. Real-time processing would compromise accuracy.
- **Automatic interpretation beyond transcript evidence**: The tool provides structure, not speculation. Summaries must be grounded in spoken content.
- **Opinionated summaries that invent intent or meaning**: Analysis should reflect what was said, not what the tool assumes was meant.
- **Enterprise-only dependencies**: All core functionality must work with open-source components.

**Rationale:** Clear boundaries prevent scope creep and maintain focus on core value.

---

## Definition of "Done"

A feature is considered complete only when:

1. **It is documented** - User-facing documentation exists and is accurate.
2. **It fails safely** - Error paths are handled gracefully with clear feedback.
3. **It can be overridden** - User control is preserved through flags or configuration.
4. **Its behavior is explainable** - A user can understand what it does in one paragraph.

**Consequences of Incompletion:**
- Undocumented features are not released.
- Unsafe features are blocked by maintainers.
- Non-overridable automation is rejected.
- Unexplainable behavior requires redesign.

---

## Governance

**Constitutional Supremacy:**
If a design decision conflicts with this constitution, **the constitution wins**.

**Amendment Process:**
1. Proposed changes must document the conflict or limitation being addressed.
2. Impact analysis required (what breaks, what improves).
3. Community review period (minimum 7 days for MAJOR version changes).
4. Version bump according to semantic versioning:
   - **MAJOR**: Principle removal or redefinition
   - **MINOR**: New principle or expanded guidance
   - **PATCH**: Clarifications, wording fixes

**Compliance:**
- All pull requests must verify constitution compliance.
- Maintainers are constitution guardians.
- Violations require justification or rollback.

---

**Version: 1.1.0** | **Ratified: 2026-02-10** | **Last Amended: 2026-02-10**
