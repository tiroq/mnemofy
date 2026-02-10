# mnemofy — Detailed Specification (v0.1 Draft)

Generated: 2026-02-10T06:10:41

## 1. Purpose

mnemofy is a CLI tool that converts **audio or video** recordings into:
1) an **inspectable transcript** (with timestamps), and  
2) a **documented Markdown report** that captures meaning: topics, decisions, action items, and concrete mentions.

mnemofy is **local-first** by default and designed to be **safe-by-default** (no OOM crashes, no silent magic, no hidden persistence).

---

## 2. Scope

### In scope
- Accept input media files: audio and video (anything supported by `ffmpeg`).
- **Default behavior:** if input is video, automatically **extract audio** and **save it next to the original file**.
- Normalize audio (mono, 16kHz WAV).
- Transcribe locally (default engine: `faster-whisper`).
- Generate outputs: transcript (txt/srt/json) + notes (md).
- Adaptive model selection when `--model` is not provided:
  - resource detection (CPU/RAM/GPU)
  - safe recommendation
  - interactive arrow-key model picker
- CI-safe behavior (no interactive hangs).
- Deterministic, reproducible transcript outputs (given same engine/model/params).

### Out of scope (v0.1)
- Full diarization (speaker labels). (Planned extension)
- Word-level forced alignment (WhisperX mode). (Planned extension)
- Live/streaming transcription guarantees.
- Any “interpretation” that invents information beyond transcript evidence.

---

## 3. Inputs

### 3.1 Supported Media
mnemofy accepts any media input supported by `ffmpeg`.

**Common audio:** `.aac .m4a .mp3 .wav .ogg .flac`  
**Common video:** `.mkv .mp4 .mov .webm .avi`

### 3.2 Audio Track Selection (video)
- Default: use **first audio track** (`a:0`).
- Future flag: `--audio-track auto|0|1|...`

### 3.3 Language
- Default: `--lang auto` (engine auto-detection when supported)  
- Explicit: `--lang ru|en|...`

---

## 4. Default Output Behavior

### 4.1 Output Location
- Default: outputs are written **next to the input file** (same directory) under a predictable naming scheme.
- Optional: user may override with `--outdir <path>`.

### 4.2 Automatic Audio Extraction (Default)
If the input is a **video file**, mnemofy MUST:
1) extract the audio,
2) normalize to 16kHz mono WAV,
3) save the extracted WAV **next to the original video**,
4) then use that WAV for transcription.

**Naming rule (default):**
- Input: `meeting.mkv`
- Extracted audio (saved next to input): `meeting.mnemofy.wav`

If `--outdir` is provided, mnemofy MAY additionally copy/produce normalized audio into the outdir (implementation choice), but the core requirement remains:
> **A normalized extracted audio WAV is saved alongside the input video by default.**

---

## 5. Pipeline

### 5.1 Media Handling
1) Determine media type:
   - If video → extract audio track `a:0`
   - If audio → proceed directly
2) Normalize audio to 16kHz mono WAV
3) Optional (configurable later): denoise / loudness normalize

### 5.2 Transcription (default engine: faster-whisper)
- Transcribe normalized WAV
- Produce segments with timestamps
- Generate:
  - `.transcript.txt` (timestamped lines)
  - `.transcript.srt` (subtitle format)
  - `.transcript.json` (raw segments/metadata)

### 5.3 Notes Generation
- Always preserve raw transcript outputs.
- Notes must be derived **only** from transcript evidence.
- Notes include topics, decisions, action items, concrete mentions, open questions/risks.
- Notes format: `.notes.md`

**Modes:**
- `--notes basic` (local deterministic summarizer; no LLM)
- `--notes llm` (optional; requires API key; strict non-hallucination prompt)

---

## 6. Output Artifacts

Given input `meeting.mkv` (or `meeting.aac`), default outputs next to input:

- `meeting.mnemofy.wav` *(only if input is video; extracted + normalized)*
- `meeting.transcript.txt`
- `meeting.transcript.srt`
- `meeting.transcript.json`
- `meeting.notes.md`

### 6.1 Transcript TXT Format
- One segment per line with time range:
  - `[HH:MM:SS–HH:MM:SS] text...`

### 6.2 Notes MD Structure (required sections)
1) Metadata: date, source file, duration, engine, model
2) Topics (with time ranges)
3) Decisions (or explicit “No explicit decisions found”)
4) Action Items (owner if known, else `owner: unknown`)
5) Concrete Mentions (names, projects, companies, dates, numbers, URLs) **with timestamps**
6) Risks / Open Questions **with timestamps**
7) Link/reference to transcript files

---

## 7. CLI Specification

### 7.1 Core Commands
```bash
mnemofy <input_media>
```

### 7.2 Flags (v0.1)
- `--outdir PATH`  
  Write outputs to PATH (default: same directory as input).

- `--lang auto|ru|en|...`  
  Transcription language.

- `--engine faster` *(default)*  
  Transcription engine selector (future: `openai` API, `whisperx`).

- `--model MODEL_NAME`  
  Explicit model selection; skips adaptive selection.

- `--auto`  
  Auto-select recommended model without prompting.

- `--list-models`  
  Print model capability matrix and exit.

- `--no-gpu`  
  Ignore GPU (including Metal) even if available.

- `--notes basic|llm` *(default: basic)*  
  Notes generation mode.

- `--audio-track auto|0|1|...` *(optional in v0.1; required by v0.2)*  
  Select audio track for video inputs.

### 7.3 Exit Codes (recommended)
- `0` success
- `2` invalid arguments
- `3` ffmpeg error / unsupported input
- `4` transcription error
- `5` notes generation error

---

## 8. Adaptive Model Selection (When --model not provided)

This section incorporates the finalized decisions from the 5-question flow.

### 8.1 Resource Detection
Collect:
- CPU cores, architecture
- Available RAM
- GPU presence (CUDA/Metal/ROCm) where possible

If detection fails (unsupported OS, permission issues), use fallback model (see 8.4).

### 8.2 Metal (macOS unified memory) Handling — Decision: Option B
- Treat **Metal** as GPU-eligible.
- Model “fit” checks MUST be based on **available RAM only** (ignore VRAM checks) to match unified memory reality.
- Provide clear output explaining that unified memory is used.

### 8.3 Safety Margin for Fit Checks — Decision: Option B (85%)
When determining “fits into memory”, use an **85% ceiling** of *available RAM*.
- Example: available RAM = 5.0 GB → ceiling = 4.25 GB
- Prevents OOM crashes while allowing practical usage.

### 8.4 Fallback Model on Detection Failure — Decision: Option B (base)
If resource detection fails, default to:
- model: `base`
- explain to user:
  - detection failure reason (if known)
  - why `base` was chosen (balanced compatibility vs quality)

### 8.5 Interactive Selection Timeout — Decision: Option C (Context-Aware)
- If stdin is a TTY (interactive terminal): **wait indefinitely** for user input.
- If stdin is not a TTY (CI/piped/non-interactive): do not prompt; behave like `--auto` and select recommended/fallback model.
- No hard timeout in TTY mode.

### 8.6 Caching Recommendations — Decision: Option C (Hybrid TTL)
Cache recommendations with a **1-hour TTL**:
- Path: `~/.mnemofy/cache/model-recommendation.json` (or platform equivalent)
- Keyed by system fingerprint (OS + arch + total RAM + GPU backend)
- Cache invalidation:
  - TTL expired, or
  - fingerprint changed
- On cache miss/expired: compute fresh recommendation

### 8.7 Interactive Model Picker UI
When prompting (TTY + no `--auto`):
- Arrow keys ↑ ↓ to move
- Enter to select
- Esc to cancel
- Highlight recommended option
- Mark risky options with ⚠ (may be slow or near memory limit)

---

## 9. ffmpeg Requirements & Behavior

### 9.1 Hard Dependency
`ffmpeg` must be present on PATH.
- If missing, fail fast with an actionable message.

### 9.2 Default Extraction Command (reference)
mnemofy SHOULD use a robust extraction + normalization step, equivalent to:

```bash
ffmpeg -y -i input.mkv -map a:0 -vn -ac 1 -ar 16000 output.wav
```

Optional audio cleanup (future preset):
- loudness normalization
- highpass/lowpass
- light denoise

---

## 10. Notes Generation Rules (Anti-Hallucination)

If `--notes llm` is used:
- The prompt MUST state:
  - “Use ONLY the transcript; do not invent facts.”
  - “If unclear, label as unclear and cite timestamp.”
- All decisions/action items/mentions MUST include timestamps or be omitted.

If `--notes basic`:
- Must be deterministic and not fabricate details.
- Should include only what can be trivially derived (e.g., time buckets + frequent keywords).

---

## 11. Logging & Observability

- Default: concise CLI progress output.
- Optional: `--verbose` for full ffmpeg and engine logs.
- Any error must include:
  - failing subsystem (ffmpeg / transcription / notes)
  - actionable next step

---

## 12. Definition of Done (v0.1)

A release is “done” when:
- Video inputs automatically extract and save normalized WAV **next to the input** by default.
- Transcription produces `.txt`, `.srt`, `.json` with timestamps.
- Notes produce `.md` with required sections and timestamp citations.
- Adaptive selection works:
  - Metal RAM-only fit checks
  - 85% safety margin
  - fallback to `base` if detection fails
  - context-aware prompting
  - TTL cache
- CI/non-interactive mode never hangs.
- README documents:
  - installation, ffmpeg requirement
  - basic usage examples
  - output files
  - model selection behavior
