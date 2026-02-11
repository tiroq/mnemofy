"""Transcription pipeline orchestration.

This module contains the TranscribePipeline class that orchestrates
the complete transcription process, from model selection through
notes generation and metadata creation.
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import readchar
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mnemofy.artifacts import (
    ASREngineInfo,
    ArtifactManifest,
    LLMEngineInfo,
    ProcessingConfig,
    ProcessingMetadata,
    create_artifact_manifest,
    create_processing_metadata,
)
from mnemofy.audio import AudioExtractor
from mnemofy.classifier import (
    HeuristicClassifier,
    MeetingType,
    extract_high_signal_segments,
)
from mnemofy.formatters import TranscriptFormatter
from mnemofy.llm import get_llm_config, get_llm_engine
from mnemofy.llm.base import LLMError
from mnemofy.model_selector import (
    MODEL_SPECS,
    ModelSelectionError,
    filter_compatible_models,
    recommend_model,
)
from mnemofy.notes import BasicNotesExtractor, render_meeting_notes
from mnemofy.output_manager import OutputManager
from mnemofy.resources import detect_system_resources
from mnemofy.transcriber import Transcriber
from mnemofy.tui.meeting_type_menu import select_meeting_type
from mnemofy.tui.model_menu import ModelMenu, is_interactive_environment


@dataclass
class PipelineConfig:
    """Immutable configuration for pipeline execution."""
    
    # Model selection
    model: Optional[str] = None
    auto: bool = False
    no_gpu: bool = False
    model_suffix: bool = False
    
    # LLM settings
    llm_engine: str = "openai"
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None
    
    # Processing flags
    normalize: bool = False
    repair: bool = False
    repair_requested: bool = False
    remove_fillers: bool = False
    
    # Output settings
    title: str = "Meeting Notes"
    keep_audio: bool = False
    output: Optional[Path] = None
    
    # Language and detection
    lang: Optional[str] = None
    notes_mode: str = "basic"
    meeting_type: str = "auto"
    classify: str = "heuristic"
    template: Optional[Path] = None
    
    # Interaction
    no_interactive: bool = False
    verbose: bool = False


@dataclass
class PipelineContext:
    """Mutable state shared across pipeline steps."""
    
    # Required inputs
    input_file: Path
    manager: OutputManager
    process_start_time: datetime
    
    # Model selection
    selected_model: Optional[str] = None
    
    # Audio extraction
    audio_file: Optional[Path] = None
    
    # LLM engine
    llm_engine_instance: Optional[object] = None
    
    # Transcription
    transcription: Optional[dict] = None
    segments: List[dict] = field(default_factory=list)
    skip_transcription: bool = False
    transcriber: Optional[Transcriber] = None
    transcript_paths: dict = field(default_factory=dict)
    
    # Normalization/repair
    transcript_changes: List = field(default_factory=list)
    
    # Language detection
    effective_language: str = "en"
    
    # Classification
    detected_type: Optional[MeetingType] = None
    classification_result: Optional[object] = None
    
    # Notes generation
    notes_output: Optional[str] = None
    
    # Metadata
    metadata: dict = field(default_factory=dict)


class TranscribePipeline:
    """Orchestrates the complete transcription pipeline."""
    
    def __init__(
        self,
        config: PipelineConfig,
        context: PipelineContext,
        console: Optional[Console] = None,
    ):
        """Initialize the pipeline.
        
        Args:
            config: Immutable pipeline configuration
            context: Mutable pipeline state
            console: Rich console for output (defaults to new Console())
        """
        self.config = config
        self.ctx = context
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)
    
    def run(self) -> None:
        """Execute the complete pipeline."""
        self.select_model()
        self.extract_audio()
        self.init_llm_engine()
        self.load_or_transcribe()
        self.normalize_and_repair()
        self.write_transcripts()
        self.detect_meeting_type()
        self.generate_notes()
        self.write_metadata_and_manifest()
        self.cleanup_and_summary()
    
    def select_model(self) -> None:
        """Step 1: Select or detect the Whisper model to use."""
        # Check for explicit model override
        if self.config.model is not None:
            self.ctx.selected_model = self.config.model
            self.console.print(f"[dim]Using explicit model: {self.ctx.selected_model}[/dim]")
            self.logger.debug(f"Model selection: explicit override '{self.ctx.selected_model}'")
            return
        
        # Detect system resources for auto-selection
        try:
            resources = detect_system_resources()
            use_gpu = not self.config.no_gpu
            
            self.logger.debug(
                f"System resources detected: RAM={resources.available_ram_gb:.1f}GB, "
                f"GPU={'available' if resources.has_gpu else 'not available'}"
            )
            
            # Determine if interactive menu should be shown
            interactive_available = is_interactive_environment()
            should_show_menu = interactive_available and not self.config.auto
            
            self.logger.debug(
                f"Interactive mode: available={interactive_available}, "
                f"auto_mode={self.config.auto}, will_show_menu={should_show_menu}"
            )
            
            if should_show_menu:
                # Interactive mode: show menu for user selection
                compatible = filter_compatible_models(resources, use_gpu=use_gpu)
                recommended, reasoning = recommend_model(resources, use_gpu=use_gpu)
                
                self.logger.debug(
                    f"Compatible models: {[m.name for m in compatible]}, "
                    f"recommended: {recommended.name}"
                )
                
                self.console.print(f"\n[bold]System Resources:[/bold] {reasoning}")
                self.console.print("[bold]Select a model:[/bold]")
                
                menu = ModelMenu(compatible, recommended=recommended, resources=resources)
                
                menu_start = time.time()
                selected_spec = menu.show()
                menu_duration = time.time() - menu_start
                
                self.logger.debug(f"Model menu interaction took {menu_duration*1000:.0f}ms")
                
                if selected_spec is None:
                    self.console.print("[yellow]Model selection cancelled[/yellow]")
                    import typer
                    raise typer.Exit(1)
                
                self.ctx.selected_model = selected_spec.name
                self.console.print(f"[dim]Selected model: {self.ctx.selected_model}[/dim]")
            else:
                # Auto-selection mode (--auto or non-TTY)
                recommended, reasoning = recommend_model(resources, use_gpu=use_gpu)
                self.ctx.selected_model = recommended.name
                mode = "auto-selected"
                self.console.print(
                    f"[dim]{mode.capitalize()}: {recommended.name} ({reasoning})[/dim]"
                )
                self.logger.debug(f"Auto-selected model: {self.ctx.selected_model} ({reasoning})")
        
        except ModelSelectionError as e:
            # No compatible models found - this is a critical error
            self.console.print(f"[red]Error:[/red] {e}")
            self.console.print("[red]No compatible models found for your system.[/red]")
            self.console.print("\nPossible solutions:")
            self.console.print("  • Free up more RAM and try again")
            self.console.print("  • Manually specify a smaller model with --model tiny")
            self.console.print("  • Use --no-gpu to force CPU-only mode")
            import typer
            raise typer.Exit(1)
        except Exception as e:
            self.console.print(f"[yellow]Warning:[/yellow] Resource detection failed: {e}")
            self.console.print("[yellow]Falling back to 'base' model[/yellow]")
            self.ctx.selected_model = "base"
    
    def extract_audio(self) -> None:
        """Step 2: Extract audio from the input file."""
        self.console.print(
            f"\n[bold blue]mnemofy[/bold blue] - Processing {self.ctx.input_file.name}"
        )
        
        # Check if audio has already been extracted
        audio_output_path = self.ctx.manager.get_audio_path()
        if audio_output_path.exists():
            self.console.print(f"[yellow]Note:[/yellow] Audio file already exists: {audio_output_path}")
            self.console.print(
                "[dim]Press 's' to skip extraction, or any other key to re-extract: [/dim]",
                end=""
            )
            try:
                choice = readchar.readchar()
                if choice.lower() == 's':
                    self.ctx.audio_file = audio_output_path
                    self.console.print("Skipping extraction")
                    self.logger.debug(
                        f"User chose to skip audio extraction, using existing file: {self.ctx.audio_file}"
                    )
                else:
                    self.console.print("Re-extracting audio")
                    self._do_extract_audio(audio_output_path)
            except Exception as e:
                self.console.print("Continuing with re-extraction...")
                self.logger.debug(f"Interactive prompt failed: {e}, defaulting to re-extraction")
                self._do_extract_audio(audio_output_path)
        else:
            self._do_extract_audio(audio_output_path)
    
    def _do_extract_audio(self, audio_output_path: Path) -> None:
        """Perform audio extraction with progress indicator."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Extracting audio...", total=None)
            extractor = AudioExtractor()
            self.ctx.audio_file = extractor.extract_audio(
                self.ctx.input_file,
                output_file=audio_output_path
            )
            progress.update(task, description="[green]✓ Audio extracted")
        
        self.console.print(f"[dim]Audio file: {self.ctx.audio_file}[/dim]")
    
    def init_llm_engine(self) -> None:
        """Step 3: Initialize LLM engine if needed."""
        llm_needed = (
            self.config.repair
            or self.config.classify == "llm"
            or self.config.notes_mode == "llm"
        )
        
        if not llm_needed:
            return
        
        self.logger.debug(
            f"LLM mode requested: classify={self.config.classify}, "
            f"notes={self.config.notes_mode}, repair={self.config.repair}"
        )
        
        try:
            # Load configuration from file + env + CLI overrides
            cli_overrides = {}
            if self.config.llm_engine != "openai":  # Only override if not default
                cli_overrides["engine"] = self.config.llm_engine
            if self.config.llm_model:
                cli_overrides["model"] = self.config.llm_model
            if self.config.llm_base_url:
                cli_overrides["base_url"] = self.config.llm_base_url
            
            self.logger.debug(f"Loading LLM config with CLI overrides: {cli_overrides}")
            
            llm_config = get_llm_config(cli_overrides=cli_overrides)
            
            self.logger.debug(
                f"Final LLM config: engine={llm_config.engine}, "
                f"model={llm_config.model}, timeout={llm_config.timeout}s"
            )
            
            # Create LLM engine using merged config
            llm_start = time.time()
            self.ctx.llm_engine_instance = get_llm_engine(
                engine_type=llm_config.engine,
                model=llm_config.model,
                base_url=llm_config.base_url,
                api_key=llm_config.api_key,
                timeout=llm_config.timeout
            )
            llm_init_duration = time.time() - llm_start
            
            if self.ctx.llm_engine_instance:
                self.console.print(
                    f"[dim]LLM engine: {self.ctx.llm_engine_instance.get_model_name()}[/dim]"
                )
                self.logger.debug(
                    f"LLM engine initialized in {llm_init_duration*1000:.0f}ms: "
                    f"{self.ctx.llm_engine_instance.get_model_name()}"
                )
            else:
                self.console.print(
                    "[yellow]Warning:[/yellow] LLM engine unavailable, falling back to heuristic mode"
                )
                self.logger.debug("LLM engine returned None, falling back to heuristic mode")
        except Exception as e:
            self.console.print(f"[yellow]Warning:[/yellow] LLM initialization failed: {e}")
            self.console.print("[dim]Falling back to heuristic mode[/dim]")
            self.logger.debug(f"LLM initialization error: {e}")
    
    def load_or_transcribe(self) -> None:
        """Step 4: Load existing transcript or perform transcription."""
        # Determine transcript paths
        self.ctx.transcript_paths = (
            self.ctx.manager.get_model_aware_transcript_paths(self.ctx.selected_model)
            if self.config.model_suffix
            else self.ctx.manager.get_transcript_paths()
        )
        transcript_json_path = self.ctx.transcript_paths["json"]
        
        # Check if transcripts already exist
        if transcript_json_path.exists():
            self.console.print("[yellow]Note:[/yellow] Transcripts already exist")
            self.console.print(
                "[dim]Press 's' to skip transcription, or any other key to re-transcribe: [/dim]",
                end=""
            )
            try:
                choice = readchar.readchar()
                if choice.lower() == 's':
                    self.console.print("Skipping transcription")
                    self.logger.debug("User chose to skip transcription, loading existing transcripts")
                    self.ctx.skip_transcription = True
                    self._load_existing_transcript(transcript_json_path)
                else:
                    self.console.print("Re-transcribing audio")
                    self.logger.debug("User chose to re-transcribe")
                    self._do_transcribe()
            except Exception as e:
                self.console.print("Continuing with re-transcription...")
                self.logger.debug(f"Interactive prompt failed: {e}, defaulting to re-transcription")
                self._do_transcribe()
        else:
            self._do_transcribe()
    
    def _load_existing_transcript(self, transcript_json_path: Path) -> None:
        """Load transcript from existing JSON file."""
        with open(transcript_json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Reconstruct transcription and segments from JSON
        if isinstance(json_data, dict) and 'segments' in json_data:
            self.ctx.segments = (
                json_data['segments']
                if isinstance(json_data['segments'], list)
                else []
            )
            self.ctx.transcription = {"segments": self.ctx.segments}
            if 'language' in json_data:
                self.ctx.transcription['language'] = json_data['language']
        elif isinstance(json_data, list):
            self.ctx.segments = json_data
            self.ctx.transcription = {"segments": self.ctx.segments}
        
        self.logger.debug(f"Loaded {len(self.ctx.segments)} segments from existing transcript")
    
    def _do_transcribe(self) -> None:
        """Perform transcription with progress indicator."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Generating formatted transcripts...", total=None)
            
            transcript_start = time.time()
            
            self.ctx.transcriber = Transcriber(model_name=self.ctx.selected_model)
            self.ctx.transcription = self.ctx.transcriber.transcribe(
                self.ctx.audio_file,
                language=self.config.lang
            )
            self.ctx.segments = self.ctx.transcriber.get_segments(self.ctx.transcription)
            
            transcript_duration = time.time() - transcript_start
            
            # Format duration nicely
            if transcript_duration < 60:
                duration_str = f"{transcript_duration:.1f}s"
            else:
                minutes = int(transcript_duration // 60)
                seconds = transcript_duration % 60
                duration_str = f"{minutes}m {seconds:.0f}s"
            
            progress.update(
                task,
                description=f"[green]✓ Transcripts generated ({duration_str})"
            )
    
    def normalize_and_repair(self) -> None:
        """Step 5: Apply normalization and/or LLM repair to transcript."""
        if not (self.config.normalize or self.config.repair):
            return
        
        if self.ctx.transcription is None:
            self.console.print(
                "[yellow]Warning:[/yellow] No transcript available for normalization/repair"
            )
            self.logger.debug("Skipping normalization/repair because transcript is unavailable")
            return
        
        self.logger.debug(
            f"Transcript preprocessing enabled: normalize={self.config.normalize}, "
            f"repair={self.config.repair}"
        )
        
        # Ensure transcriber is initialized (needed for normalization/repair utilities)
        if self.ctx.transcriber is None:
            self.ctx.transcriber = Transcriber(model_name=self.ctx.selected_model)
        
        # Handle repair without LLM engine
        if self.config.repair_requested and self.config.repair and not self.ctx.llm_engine_instance:
            self.console.print(
                "[yellow]Note:[/yellow] Repair requires LLM engine, which is not available"
            )
            self.console.print(
                "[dim]Press 'y' to proceed without repair, or any other key to cancel: [/dim]",
                end=""
            )
            try:
                choice = readchar.readchar()
                if choice.lower() == 'y':
                    self.console.print("Proceeding without repair")
                    self.config.repair = False
                    self.logger.debug("User chose to proceed without repair")
                else:
                    self.console.print("Cancelled")
                    self.console.print(
                        "[yellow]Please enable LLM engine or re-run without --repair flag[/yellow]"
                    )
                    import typer
                    raise typer.Exit(1)
            except Exception as e:
                self.console.print("Proceeding without repair (non-interactive)")
                self.config.repair = False
                self.logger.debug(
                    f"Interactive prompt failed: {e}, defaulting to proceed without repair"
                )
        elif self.config.repair and not self.ctx.llm_engine_instance:
            self.console.print(
                "[yellow]Warning:[/yellow] --repair requires LLM engine, skipping repair"
            )
            self.config.repair = False
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Processing transcript...", total=None)
            
            # Apply normalization
            if self.config.normalize:
                progress.update(task, description="Normalizing transcript...")
                
                norm_start = time.time()
                norm_result = self.ctx.transcriber.normalize_transcript(
                    self.ctx.transcription,
                    remove_fillers=self.config.remove_fillers,
                    normalize_numbers=True,
                )
                norm_duration = time.time() - norm_start
                
                self.ctx.transcription = norm_result.transcription
                self.ctx.transcript_changes.extend(norm_result.changes)
                self.ctx.segments = self.ctx.transcriber.get_segments(self.ctx.transcription)
                
                self.console.print(
                    f"[dim]Applied {len(norm_result.changes)} normalization changes[/dim]"
                )
                self.logger.debug(
                    f"Normalization: {len(norm_result.changes)} changes in {norm_duration*1000:.0f}ms"
                )
            
            # Apply LLM-based repair
            if self.config.repair and self.ctx.llm_engine_instance:
                progress.update(task, description="Repairing transcript with LLM...")
                try:
                    repair_start = time.time()
                    repair_result = asyncio.run(
                        self.ctx.transcriber.repair_transcript(
                            self.ctx.transcription,
                            self.ctx.llm_engine_instance
                        )
                    )
                    repair_duration = time.time() - repair_start
                    
                    self.ctx.transcription = repair_result.transcription
                    self.ctx.transcript_changes.extend(repair_result.changes)
                    self.ctx.segments = self.ctx.transcriber.get_segments(self.ctx.transcription)
                    
                    self.console.print(
                        f"[dim]Applied {len(repair_result.changes)} LLM repairs[/dim]"
                    )
                    self.logger.debug(
                        f"LLM repair: {len(repair_result.changes)} changes in {repair_duration*1000:.0f}ms"
                    )
                except Exception as e:
                    self.console.print(f"[yellow]Warning:[/yellow] Transcript repair failed: {e}")
                    self.console.print("[dim]Continuing with normalized transcript[/dim]")
                    self.logger.debug(f"Repair failed: {e}")
            
            progress.update(task, description="[green]✓ Transcript processed")
    
    def write_transcripts(self) -> None:
        """Step 6: Write transcript files in all formats."""
        # Determine effective language: prefer explicit --lang, then detected, then fallback
        detected_language = (
            self.ctx.transcription.get("language")
            if self.ctx.transcription
            else None
        )
        self.ctx.effective_language = (
            self.config.lang or detected_language or "en"
        )
        
        # Prepare metadata (enriched with model details)
        model_spec = MODEL_SPECS.get(self.ctx.selected_model)
        self.ctx.metadata = {
            "engine": "faster-whisper",
            "model": self.ctx.selected_model,
            "language": self.ctx.effective_language,
            "duration": sum(s["end"] - s["start"] for s in self.ctx.segments),
        }
        
        # Add optional model specification details if available
        if model_spec:
            self.ctx.metadata["model_size_gb"] = model_spec.min_ram_gb
            self.ctx.metadata["quality_rating"] = model_spec.quality_rating
            self.ctx.metadata["speed_rating"] = model_spec.speed_rating
        
        # Add processing flags
        if self.config.normalize or self.config.repair:
            self.ctx.metadata["preprocessing"] = {
                "normalized": self.config.normalize,
                "repaired": self.config.repair,
                "remove_fillers": self.config.remove_fillers if self.config.normalize else False,
            }
        
        # Generate all formats
        txt_output = TranscriptFormatter.to_txt(self.ctx.segments)
        srt_output = TranscriptFormatter.to_srt(self.ctx.segments)
        json_output = TranscriptFormatter.to_json(self.ctx.segments, self.ctx.metadata)
        
        # Get paths for writing
        txt_path = self.ctx.transcript_paths["txt"]
        srt_path = self.ctx.transcript_paths["srt"]
        json_path = self.ctx.transcript_paths["json"]
        
        txt_path.write_text(txt_output, encoding="utf-8")
        srt_path.write_text(srt_output, encoding="utf-8")
        json_path.write_text(json_output, encoding="utf-8")
        
        # Write changes log if normalization or repair was performed
        if self.ctx.transcript_changes:
            changes_log_path = self.ctx.manager.get_changes_log_path()
            changes_output = format_changes_log(self.ctx.transcript_changes)
            changes_log_path.write_text(changes_output, encoding="utf-8")
            self.console.print(f"[dim]Changes log: {changes_log_path}[/dim]")
    
    def detect_meeting_type(self) -> None:
        """Step 7: Detect or accept explicit meeting type."""
        # Skip detection if transcription was skipped (unless explicitly requested)
        skip_classification = False
        if (
            self.ctx.skip_transcription
            and self.config.classify != "off"
            and self.config.meeting_type == "auto"
        ):
            self.console.print("[yellow]Note:[/yellow] Transcription was skipped")
            self.console.print(
                "[dim]Press 'c' to detect meeting type, or 's' to skip classification: [/dim]",
                end=""
            )
            try:
                choice = readchar.readchar()
                if choice.lower() == 'c':
                    self.console.print("Detecting meeting type")
                    self.logger.debug("User chose to detect meeting type despite skipping transcription")
                else:
                    self.console.print("Skipping classification")
                    skip_classification = True
                    self.logger.debug("User chose to skip meeting type detection")
            except Exception as e:
                # Non-interactive: skip classification when transcription was skipped
                self.console.print("Skipping classification (non-interactive)")
                skip_classification = True
                self.logger.debug(
                    f"Interactive prompt failed: {e}, defaulting to skip classification"
                )
        
        # Perform detection if enabled
        if (
            self.config.classify != "off"
            and self.config.meeting_type == "auto"
            and not skip_classification
        ):
            self._do_detect_meeting_type()
        elif self.config.meeting_type and self.config.meeting_type != "auto":
            # Use explicit meeting type
            self._use_explicit_meeting_type()
        
        # Interactive meeting type selection (if enabled and available)
        if (
            self.ctx.detected_type
            and self.ctx.classification_result
            and not self.config.no_interactive
        ):
            self._interactive_meeting_type_selection()
    
    def _do_detect_meeting_type(self) -> None:
        """Perform meeting type detection using LLM or heuristic classifier."""
        self.logger.debug(
            f"Meeting type detection: mode={self.config.classify}, auto-detect=True"
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Detecting meeting type...", total=None)
            
            if self.config.classify == "llm" and self.ctx.llm_engine_instance:
                # Use LLM classifier
                try:
                    transcript_text = " ".join(s["text"] for s in self.ctx.segments)
                    
                    self.logger.debug(f"Transcript length for detection: {len(transcript_text)} chars")
                    
                    # Extract high-signal segments (use config values if available)
                    llm_config_for_extract = get_llm_config()
                    high_signal = extract_high_signal_segments(
                        transcript_text,
                        context_words=llm_config_for_extract.context_words,
                        max_segments=llm_config_for_extract.max_segments
                    )
                    
                    self.logger.debug(
                        f"Extracted {len(high_signal)} high-signal segments, "
                        f"total {sum(len(s) for s in high_signal)} chars"
                    )
                    
                    detect_start = time.time()
                    self.ctx.classification_result = (
                        self.ctx.llm_engine_instance.classify_meeting_type(
                            transcript_text,
                            high_signal_segments=high_signal
                        )
                    )
                    detect_duration = time.time() - detect_start
                    self.ctx.detected_type = self.ctx.classification_result.detected_type
                    
                    # Display detection result
                    confidence_pct = self.ctx.classification_result.confidence * 100
                    self.console.print(
                        f"\n[bold]Detected Meeting Type:[/bold] {self.ctx.detected_type.value}"
                    )
                    self.console.print(f"[dim]Confidence: {confidence_pct:.1f}% (LLM)[/dim]")
                    if self.ctx.classification_result.evidence:
                        self.console.print(
                            f"[dim]Evidence: {', '.join(self.ctx.classification_result.evidence[:3])}[/dim]"
                        )
                    
                    self.logger.debug(
                        f"LLM detection: type={self.ctx.detected_type.value}, "
                        f"confidence={confidence_pct:.1f}%, duration={detect_duration*1000:.0f}ms"
                    )
                    
                    progress.update(task, description="[green]✓ Meeting type detected (LLM)")
                except LLMError as e:
                    self.console.print(f"[yellow]Warning:[/yellow] LLM classification failed: {e}")
                    self.console.print("[dim]Falling back to heuristic mode[/dim]")
                    self.logger.debug(f"LLM classification error: {e}, falling back to heuristic")
                    self._heuristic_detection()
                    progress.update(task, description="[green]✓ Meeting type detected (heuristic fallback)")
            else:
                # Use heuristic classifier
                self._heuristic_detection()
                progress.update(task, description="[green]✓ Meeting type detected")
    
    def _heuristic_detection(self) -> None:
        """Perform heuristic meeting type detection."""
        transcript_text = " ".join(s["text"] for s in self.ctx.segments)
        classifier = HeuristicClassifier()
        
        self.logger.debug(f"Using heuristic classifier on {len(transcript_text)} chars")
        
        detect_start = time.time()
        self.ctx.classification_result = classifier.detect_meeting_type(
            transcript_text,
            self.ctx.segments
        )
        detect_duration = time.time() - detect_start
        self.ctx.detected_type = self.ctx.classification_result.detected_type
        
        # Display detection result
        confidence_pct = self.ctx.classification_result.confidence * 100
        self.console.print(
            f"\n[bold]Detected Meeting Type:[/bold] {self.ctx.detected_type.value}"
        )
        self.console.print(f"[dim]Confidence: {confidence_pct:.1f}% (Heuristic)[/dim]")
        if self.ctx.classification_result.evidence:
            self.console.print(
                f"[dim]Evidence: {', '.join(self.ctx.classification_result.evidence[:3])}[/dim]"
            )
        
        self.logger.debug(
            f"Heuristic detection: type={self.ctx.detected_type.value}, "
            f"confidence={confidence_pct:.1f}%, duration={detect_duration*1000:.0f}ms"
        )
    
    def _use_explicit_meeting_type(self) -> None:
        """Use explicit meeting type from config."""
        try:
            self.ctx.detected_type = MeetingType(self.config.meeting_type.lower())
            self.console.print(
                f"\n[dim]Using explicit meeting type: {self.ctx.detected_type.value}[/dim]"
            )
        except ValueError:
            self.console.print(
                f"[red]Error:[/red] Invalid meeting type '{self.config.meeting_type}'"
            )
            self.console.print(f"Valid types: {', '.join(mt.value for mt in MeetingType)}")
            import typer
            raise typer.Exit(1)
    
    def _interactive_meeting_type_selection(self) -> None:
        """Show interactive menu for meeting type confirmation/override."""
        interactive_available = is_interactive_environment()
        
        self.logger.debug(
            f"Interactive meeting type selection: available={interactive_available}, "
            f"detected={self.ctx.detected_type.value}, no_interactive={self.config.no_interactive}"
        )
        
        if interactive_available:
            try:
                # Let user confirm or override via menu
                menu_start = time.time()
                selected_type = select_meeting_type(
                    self.ctx.classification_result,
                    auto_accept_threshold=0.6,
                    interactive=True
                )
                menu_duration = time.time() - menu_start
                
                self.logger.debug(f"Meeting type menu interaction took {menu_duration*1000:.0f}ms")
                
                if selected_type != self.ctx.detected_type:
                    self.console.print(f"\n[cyan]User selected:[/cyan] {selected_type.value}")
                    self.logger.debug(
                        f"User overrode detected type: {self.ctx.detected_type.value} -> {selected_type.value}"
                    )
                    self.ctx.detected_type = selected_type
                else:
                    self.logger.debug(f"User accepted detected type: {self.ctx.detected_type.value}")
            except Exception as e:
                self.console.print(f"[yellow]Warning:[/yellow] Interactive menu failed: {e}")
                self.console.print(
                    f"[dim]Continuing with detected type: {self.ctx.detected_type.value}[/dim]"
                )
                self.logger.debug(f"Interactive menu error: {e}")
    
    def generate_notes(self) -> None:
        """Step 8: Generate meeting notes."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Generating notes...", total=None)
            
            # Use meeting-type-aware notes generation if type detected
            if self.ctx.detected_type and not self.config.template:
                self._generate_meeting_type_aware_notes(task, progress)
            else:
                # Fall back to legacy notes generator (not implemented error expected)
                from mnemofy.notes import StructuredNotesGenerator
                try:
                    notes_generator = StructuredNotesGenerator(mode="basic")
                    self.ctx.notes_output = notes_generator.generate(
                        self.ctx.segments,
                        self.ctx.metadata,
                        include_audio=self.config.keep_audio
                    )
                except NotImplementedError as e:
                    self.console.print(f"[red]Error: {e}[/red]")
                    self.console.print(
                        "[yellow]Please specify a meeting type to use LLM notes generation.[/yellow]"
                    )
                    import typer
                    raise typer.Exit(1)
            
            # Determine output path for notes
            if self.config.output is None:
                output_path = self.ctx.manager.get_notes_path()
            else:
                output_path = self.config.output
            
            # Write notes output
            output_path.write_text(self.ctx.notes_output, encoding="utf-8")
            
            # Write meeting-type.json if type was detected
            if self.ctx.classification_result:
                meeting_type_path = (
                    self.ctx.manager.outdir / f"{self.ctx.manager.basename}.meeting-type.json"
                )
                meeting_type_data = {
                    "detected_type": self.ctx.classification_result.detected_type.value,
                    "confidence": self.ctx.classification_result.confidence,
                    "evidence": self.ctx.classification_result.evidence,
                    "secondary_types": [
                        {"type": mt.value, "score": score}
                        for mt, score in self.ctx.classification_result.secondary_types
                    ],
                    "engine": self.ctx.classification_result.engine,
                    "timestamp": self.ctx.classification_result.timestamp.isoformat(),
                }
                meeting_type_path.write_text(
                    json.dumps(meeting_type_data, indent=2),
                    encoding="utf-8"
                )
            
            progress.update(task, description="[green]✓ Notes generated")
    
    def _generate_meeting_type_aware_notes(self, task, progress) -> None:
        """Generate notes using meeting-type-aware templates."""
        self.logger.debug(
            f"Generating meeting-type-aware notes: type={self.ctx.detected_type.value}, "
            f"mode={self.config.notes_mode}, template={self.config.template}"
        )
        
        # Extract structured information (basic or LLM)
        if self.config.notes_mode == "llm" and self.ctx.llm_engine_instance:
            try:
                # Use LLM notes extraction
                notes_start = time.time()
                extracted_items = self.ctx.llm_engine_instance.generate_notes(
                    transcript_segments=self.ctx.segments,
                    meeting_type=self.ctx.detected_type.value,
                    focus_areas=None
                )
                notes_duration = time.time() - notes_start
                
                self.console.print("[dim]Notes extracted using LLM[/dim]")
                self.logger.debug(
                    f"LLM notes extraction: {len(extracted_items)} items in {notes_duration*1000:.0f}ms"
                )
            except LLMError as e:
                self.console.print(f"[yellow]Warning:[/yellow] LLM notes extraction failed: {e}")
                self.console.print("[dim]Falling back to basic extraction[/dim]")
                self.logger.debug(f"LLM notes extraction failed: {e}, falling back to basic")
                extracted_items = self._basic_extraction()
        else:
            # Use basic heuristic extraction
            extracted_items = self._basic_extraction()
        
        # Prepare metadata for template
        template_metadata = {
            "title": self.config.title,
            "date": self.ctx.metadata.get("date", ""),
            "duration": f"{int(self.ctx.metadata['duration'] // 60)}m {int(self.ctx.metadata['duration'] % 60)}s",
            "confidence": (
                f"{self.ctx.classification_result.confidence:.2f}"
                if self.ctx.classification_result
                else "N/A"
            ),
            "engine": (
                self.ctx.classification_result.engine
                if self.ctx.classification_result
                else "manual"
            ),
        }
        
        # Render using appropriate template
        try:
            self.ctx.notes_output = render_meeting_notes(
                self.ctx.detected_type,
                extracted_items,
                template_metadata,
                custom_template_dir=self.config.template.parent if self.config.template else None
            )
        except Exception as e:
            from jinja2 import TemplateNotFound
            if isinstance(e, TemplateNotFound) or "Template" in str(e):
                self.console.print(f"[red]Error: {e}[/red]")
                self.console.print("[yellow]Tip:[/yellow] Check if templates are installed correctly")
                self.console.print("[dim]Try reinstalling mnemofy with: pip install -e .[/dim]")
                self.logger.debug(f"Template rendering failed: {e}")
                import typer
                raise typer.Exit(1)
            else:
                raise
    
    def _basic_extraction(self) -> list:
        """Perform basic heuristic notes extraction."""
        extractor = BasicNotesExtractor()
        
        notes_start = time.time()
        extracted_items = extractor.extract_all(self.ctx.segments, self.ctx.detected_type)
        notes_duration = time.time() - notes_start
        
        self.logger.debug(
            f"Basic extraction: {len(extracted_items)} items in {notes_duration*1000:.0f}ms"
        )
        
        return extracted_items
    
    def write_metadata_and_manifest(self) -> None:
        """Step 9: Write processing metadata and artifacts manifest."""
        process_end_time = datetime.now()
        
        # Build ASR engine info
        model_spec = MODEL_SPECS.get(self.ctx.selected_model)
        asr_info = ASREngineInfo(
            engine="faster-whisper",
            model=self.ctx.selected_model,
            model_size_gb=model_spec.min_ram_gb if model_spec else None,
            quality_rating=model_spec.quality_rating if model_spec else None,
            speed_rating=model_spec.speed_rating if model_spec else None,
        )
        
        # Build LLM engine info (if used)
        llm_info = None
        if self.ctx.llm_engine_instance:
            llm_purposes = []
            if self.config.classify == "llm":
                llm_purposes.append("meeting_type_detection")
            if self.config.notes_mode == "llm":
                llm_purposes.append("notes_generation")
            if self.config.repair:
                llm_purposes.append("transcript_repair")
            
            llm_info = LLMEngineInfo(
                engine=self.config.llm_engine,
                model=self.ctx.llm_engine_instance.get_model_name(),
                purpose=", ".join(llm_purposes) if llm_purposes else "general",
            )
        
        # Build processing config
        proc_config = ProcessingConfig(
            language=self.ctx.effective_language,
            normalize=self.config.normalize,
            repair=self.config.repair,
            meeting_type=self.ctx.detected_type.value if self.ctx.detected_type else None,
            classify_mode=self.config.classify,
            notes_mode=self.config.notes_mode,
        )
        
        # Count words in transcript
        transcript_text = " ".join(s["text"] for s in self.ctx.segments)
        word_count = len(transcript_text.split())
        
        # Detect language from transcription
        detected_language = (
            self.ctx.transcription.get("language")
            if self.ctx.transcription
            else None
        )
        
        # Create processing metadata
        proc_metadata = create_processing_metadata(
            input_file=self.ctx.input_file.name,
            asr_engine=asr_info,
            config=proc_config,
            start_time=self.ctx.process_start_time,
            end_time=process_end_time,
            llm_engine=llm_info,
            language_detected=detected_language,
            transcript_duration_seconds=self.ctx.metadata["duration"],
            word_count=word_count,
            segment_count=len(self.ctx.segments),
        )
        
        # Save processing metadata
        metadata_path = self.ctx.manager.get_metadata_path()
        if self.config.model_suffix:
            # Use model-suffixed metadata filename for comparison
            metadata_path = (
                self.ctx.manager.outdir
                / f"{self.ctx.manager.basename}.{self.ctx.selected_model}.metadata.json"
            )
            self.logger.debug(f"Using model-suffixed metadata path: {metadata_path}")
        
        metadata_path.write_text(proc_metadata.to_json(), encoding="utf-8")
        
        # Track run history (append to history file)
        history_path = (
            self.ctx.manager.outdir / f"{self.ctx.manager.basename}.run-history.jsonl"
        )
        run_record = {
            "timestamp": process_end_time.isoformat(),
            "model": self.ctx.selected_model,
            "duration_seconds": proc_metadata.duration_seconds,
            "transcript_duration": self.ctx.metadata["duration"],
            "word_count": word_count,
            "segment_count": len(self.ctx.segments),
            "config": asdict(proc_config),
        }
        
        # Append to history file (JSONL format - one JSON object per line)
        with open(history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(run_record, ensure_ascii=False) + "\n")
        
        self.logger.debug(f"Appended run record to history: {history_path}")
        
        # Create artifacts manifest
        manifest = create_artifact_manifest(
            input_file=self.ctx.input_file.name,
            model_name=self.ctx.selected_model,
        )
        
        # Add artifacts to manifest
        self._add_artifacts_to_manifest(manifest)
        
        # Save artifacts manifest
        manifest_path = self.ctx.manager.get_artifacts_manifest_path()
        if self.config.model_suffix:
            # Use model-suffixed manifest filename
            manifest_path = (
                self.ctx.manager.outdir
                / f"{self.ctx.manager.basename}.{self.ctx.selected_model}.artifacts.json"
            )
            self.logger.debug(f"Using model-suffixed manifest path: {manifest_path}")
        
        manifest_path.write_text(manifest.to_json(), encoding="utf-8")
    
    def _add_artifacts_to_manifest(self, manifest: ArtifactManifest) -> None:
        """Add all artifacts to the manifest."""
        def get_file_size(path: Path) -> int:
            try:
                return path.stat().st_size if path.exists() else 0
            except Exception:
                return 0
        
        # Transcript artifacts
        txt_path = self.ctx.transcript_paths["txt"]
        srt_path = self.ctx.transcript_paths["srt"]
        json_path = self.ctx.transcript_paths["json"]
        
        manifest.add_artifact(
            "transcript",
            str(txt_path.relative_to(self.ctx.manager.outdir)),
            "txt",
            "Plain text transcript with timestamps",
            get_file_size(txt_path),
            self.ctx.selected_model
        )
        manifest.add_artifact(
            "transcript",
            str(srt_path.relative_to(self.ctx.manager.outdir)),
            "srt",
            "SubRip subtitle format transcript",
            get_file_size(srt_path),
            self.ctx.selected_model
        )
        manifest.add_artifact(
            "transcript",
            str(json_path.relative_to(self.ctx.manager.outdir)),
            "json",
            "Structured JSON transcript with metadata",
            get_file_size(json_path),
            self.ctx.selected_model,
            "1.0"
        )
        
        # Notes artifact
        output_path = (
            self.config.output
            if self.config.output
            else self.ctx.manager.get_notes_path()
        )
        manifest.add_artifact(
            "notes",
            str(output_path.relative_to(self.ctx.manager.outdir)),
            "md",
            "Structured meeting notes",
            get_file_size(output_path),
            (
                self.ctx.llm_engine_instance.get_model_name()
                if (self.config.notes_mode == "llm" and self.ctx.llm_engine_instance)
                else "basic_extractor"
            )
        )
        
        # Classification result (if generated)
        if self.ctx.classification_result:
            meeting_type_path = (
                self.ctx.manager.outdir / f"{self.ctx.manager.basename}.meeting-type.json"
            )
            manifest.add_artifact(
                "classification",
                str(meeting_type_path.relative_to(self.ctx.manager.outdir)),
                "json",
                "Meeting type classification result",
                get_file_size(meeting_type_path),
                (
                    self.ctx.llm_engine_instance.get_model_name()
                    if (self.config.classify == "llm" and self.ctx.llm_engine_instance)
                    else "heuristic_classifier"
                )
            )
        
        # Changes log (if generated)
        if self.ctx.transcript_changes:
            changes_log_path = self.ctx.manager.get_changes_log_path()
            changes_model = (
                self.ctx.llm_engine_instance.get_model_name()
                if (self.config.repair and self.ctx.llm_engine_instance)
                else "normalizer"
            )
            manifest.add_artifact(
                "log",
                str(changes_log_path.relative_to(self.ctx.manager.outdir)),
                "md",
                "Transcript normalization/repair changes log",
                get_file_size(changes_log_path),
                changes_model
            )
        
        # Metadata artifact
        metadata_path = self.ctx.manager.get_metadata_path()
        if self.config.model_suffix:
            metadata_path = (
                self.ctx.manager.outdir
                / f"{self.ctx.manager.basename}.{self.ctx.selected_model}.metadata.json"
            )
        
        manifest.add_artifact(
            "metadata",
            str(metadata_path.relative_to(self.ctx.manager.outdir)),
            "json",
            "Processing metadata and configuration",
            get_file_size(metadata_path),
            None,
            "1.0"
        )
        
        # Audio artifact (if kept)
        if self.config.keep_audio:
            audio_path = self.ctx.manager.get_audio_path()
            manifest.add_artifact(
                "audio",
                str(audio_path.relative_to(self.ctx.manager.outdir)),
                "wav",
                "Extracted audio (16kHz mono WAV)",
                get_file_size(audio_path)
            )
    
    def cleanup_and_summary(self) -> None:
        """Step 10: Clean up temporary files and print summary."""
        # Clean up temporary audio file if needed
        if not self.config.keep_audio and self.ctx.audio_file != self.ctx.input_file:
            try:
                self.ctx.audio_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors
        
        self.console.print("\n[bold green]✓ Success![/bold green]")
        
        if self.config.model_suffix:
            self.console.print(
                f"[cyan]ℹ Model-suffixed filenames enabled ({self.ctx.selected_model})[/cyan]"
            )
        
        # Display output files
        txt_path = self.ctx.transcript_paths["txt"]
        srt_path = self.ctx.transcript_paths["srt"]
        json_path = self.ctx.transcript_paths["json"]
        output_path = (
            self.config.output
            if self.config.output
            else self.ctx.manager.get_notes_path()
        )
        
        self.console.print("[dim]Output files generated:[/dim]")
        self.console.print(f"  Transcript (TXT): {txt_path}")
        self.console.print(f"  Subtitle (SRT): {srt_path}")
        self.console.print(f"  Structured (JSON): {json_path}")
        if self.ctx.classification_result:
            meeting_type_path = (
                self.ctx.manager.outdir / f"{self.ctx.manager.basename}.meeting-type.json"
            )
            self.console.print(f"  Meeting Type: {meeting_type_path}")
        self.console.print(f"  Notes: {output_path}")
        
        # Display metadata files
        metadata_path = self.ctx.manager.get_metadata_path()
        if self.config.model_suffix:
            metadata_path = (
                self.ctx.manager.outdir
                / f"{self.ctx.manager.basename}.{self.ctx.selected_model}.metadata.json"
            )
        
        manifest_path = self.ctx.manager.get_artifacts_manifest_path()
        if self.config.model_suffix:
            manifest_path = (
                self.ctx.manager.outdir
                / f"{self.ctx.manager.basename}.{self.ctx.selected_model}.artifacts.json"
            )
        
        history_path = (
            self.ctx.manager.outdir / f"{self.ctx.manager.basename}.run-history.jsonl"
        )
        
        self.console.print("[dim]Metadata:[/dim]")
        self.console.print(f"  Processing Info: {metadata_path}")
        self.console.print(f"  Artifacts Index: {manifest_path}")
        self.console.print(f"  Run History: {history_path}")
        
        # Show stats
        total_duration = sum(s["end"] - s["start"] for s in self.ctx.segments)
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        
        self.console.print("\n[bold]Statistics:[/bold]")
        self.console.print(f"  Segments: {len(self.ctx.segments)}")
        self.console.print(f"  Duration: {minutes}m {seconds}s")


def format_changes_log(changes: list) -> str:
    """Format transcript changes into markdown log.
    
    Args:
        changes: List of TranscriptChange objects
    
    Returns:
        Markdown-formatted changes log
    """
    output_lines = [
        "# Transcript Changes Log",
        "",
        "This document logs all modifications made to the transcript during normalization and/or repair.",
        "",
    ]
    
    # Group changes by type
    normalization_changes = [c for c in changes if c.change_type == "normalization"]
    repair_changes = [c for c in changes if c.change_type == "repair"]
    
    # Summary
    output_lines.append("## Summary")
    output_lines.append("")
    output_lines.append(f"- **Total Changes**: {len(changes)}")
    output_lines.append(f"- **Normalization Changes**: {len(normalization_changes)}")
    output_lines.append(f"- **Repair Changes**: {len(repair_changes)}")
    output_lines.append("")
    
    # Normalization changes
    if normalization_changes:
        output_lines.append("## Normalization Changes")
        output_lines.append("")
        output_lines.append("Deterministic changes applied during transcript normalization:")
        output_lines.append("")
        
        for change in normalization_changes:
            output_lines.append(f"### Change #{change.segment_id} @ {change.timestamp}")
            output_lines.append("")
            output_lines.append(f"**Reason**: {change.reason}")
            output_lines.append("")
            output_lines.append("**Before**:")
            output_lines.append("```")
            output_lines.append(change.before)
            output_lines.append("```")
            output_lines.append("")
            output_lines.append("**After**:")
            output_lines.append("```")
            output_lines.append(change.after)
            output_lines.append("```")
            output_lines.append("")
    
    # Repair changes
    if repair_changes:
        output_lines.append("## LLM Repair Changes")
        output_lines.append("")
        output_lines.append("ASR error corrections applied by LLM:")
        output_lines.append("")
        
        for change in repair_changes:
            output_lines.append(f"### Repair #{change.segment_id} @ {change.timestamp}")
            output_lines.append("")
            output_lines.append(f"**Reason**: {change.reason}")
            output_lines.append("")
            output_lines.append("**Before**:")
            output_lines.append("```")
            output_lines.append(change.before)
            output_lines.append("```")
            output_lines.append("")
            output_lines.append("**After**:")
            output_lines.append("```")
            output_lines.append(change.after)
            output_lines.append("```")
            output_lines.append("")
    
    return "\n".join(output_lines)
