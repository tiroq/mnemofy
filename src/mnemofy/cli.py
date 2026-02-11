"""Command-line interface for mnemofy."""

import json
import logging
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import readchar
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mnemofy.artifacts import (
    ProcessingMetadata,
    ASREngineInfo,
    LLMEngineInfo,
    ProcessingConfig,
    ArtifactManifest,
    create_processing_metadata,
    create_artifact_manifest,
)
from mnemofy.audio import AudioExtractor
from mnemofy.classifier import HeuristicClassifier, MeetingType, extract_high_signal_segments
from mnemofy.formatters import TranscriptFormatter
from mnemofy.llm import get_llm_engine, get_llm_config
from mnemofy.llm.base import LLMError
from mnemofy.model_selector import (
    ModelSelectionError,
    get_model_table,
    list_models,
    recommend_model,
    MODEL_SPECS,
)
from mnemofy.notes import (
    StructuredNotesGenerator,
    BasicNotesExtractor,
    render_meeting_notes,
)
from mnemofy.output_manager import OutputManager
from mnemofy.resources import detect_system_resources
from mnemofy.transcriber import Transcriber
from mnemofy.tui.model_menu import ModelMenu, is_interactive_environment
from mnemofy.tui.meeting_type_menu import select_meeting_type

app = typer.Typer(
    name="mnemofy",
    help="Extract audio from media files, transcribe speech, and produce documented meeting notes",
    add_completion=False,
)
console = Console()
logger = logging.getLogger(__name__)


@app.command()
def transcribe(
    input_file: Optional[Path] = typer.Argument(
        None,
        help="Path to audio or video file (aac, mp3, wav, mkv, mp4). Not required when using --list-models.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output Markdown file path (default: input_name_notes.md)",
    ),
    outdir: Optional[Path] = typer.Option(
        None,
        "--outdir",
        help="Output directory for transcript and notes files (default: same as input)",
        file_okay=False,
        dir_okay=True,
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Whisper model to use (tiny, base, small, medium, large-v3). "
        "If not provided, auto-detects based on system resources. "
        "Use --list-models to see all available models.",
    ),
    auto: bool = typer.Option(
        False,
        "--auto",
        help="Auto-select model without interactive menu (headless mode). "
        "Uses system resource detection to recommend best model.",
    ),
    no_gpu: bool = typer.Option(
        False,
        "--no-gpu",
        help="Force CPU-only mode, disable GPU acceleration if available",
    ),
    list_models_flag: bool = typer.Option(
        False,
        "--list-models",
        help="Display available models and exit (does not transcribe)",
    ),
    title: str = typer.Option(
        "Meeting Notes",
        "--title",
        "-t",
        help="Title for the generated notes",
    ),
    keep_audio: bool = typer.Option(
        False,
        "--keep-audio",
        "-k",
        help="Keep extracted audio file",
    ),
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        help="Language of audio (e.g., en, es, fr). Auto-detect if not specified",
    ),
    notes: str = typer.Option(
        "basic",
        "--notes",
        help="Notes generation mode: 'basic' (deterministic) or 'llm' (LLM-enhanced)",
    ),
    meeting_type: Optional[str] = typer.Option(
        "auto",
        "--meeting-type",
        help="Meeting type: auto (detect), status, planning, design, demo, talk, incident, discovery, oneonone, brainstorm",
    ),
    classify: str = typer.Option(
        "heuristic",
        "--classify",
        help="Classification mode: heuristic (default), llm, or off (disable detection)",
    ),
    template: Optional[Path] = typer.Option(
        None,
        "--template",
        help="Custom template file path (overrides default meeting type templates)",
    ),
    llm_engine: str = typer.Option(
        "openai",
        "--llm-engine",
        help="LLM engine: openai (default), ollama, or openai_compat",
    ),
    llm_model: Optional[str] = typer.Option(
        None,
        "--llm-model",
        help="LLM model name (default: gpt-4o-mini for openai, llama3.2:3b for ollama)",
    ),
    llm_base_url: Optional[str] = typer.Option(
        None,
        "--llm-base-url",
        help="Custom LLM API base URL (for openai_compat or custom endpoints)",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Skip interactive prompts (auto-accept detected meeting type)",
    ),
    normalize: bool = typer.Option(
        False,
        "--normalize",
        help="Apply deterministic transcript normalization (stutter reduction, sentence stitching)",
    ),
    repair: bool = typer.Option(
        False,
        "--repair",
        help="Use LLM to repair ASR errors (requires LLM engine, outputs change log)",
    ),
    remove_fillers: bool = typer.Option(
        False,
        "--remove-fillers",
        help="Remove filler words (um, uh, like) during normalization (use with --normalize)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging (shows LLM request details, timing, detection info)",
    ),
    model_suffix: bool = typer.Option(
        False,
        "--model-suffix",
        help="Include model name in output filenames (e.g., meeting.base.transcript.json). "
        "Useful for comparing outputs from different models without overwriting.",
    ),
) -> None:
    """
    Transcribe audio/video file and generate structured meeting notes.

    The tool will:
    1. Detect system resources and recommend appropriate Whisper model
    2. Extract audio from the media file (if needed)
    3. Transcribe speech using recommended or specified model
    4. Generate structured Markdown notes with topics, decisions, actions, and mentions

    Model Selection Behavior:
    - With --model: Uses specified model (explicit override)
    - With --auto: Auto-selects without interactive menu
    - With TTY (interactive terminal): Shows interactive model menu
    - Non-TTY (piped input, CI/CD): Auto-selects silently
    - Fallback: Uses 'base' model if detection fails
    """
    import logging
    import time
    
    # Configure logging based on verbose flag
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='[%(levelname)s] %(message)s',
        force=True
    )
    logger = logging.getLogger(__name__)
    
    # Start timing for processing metadata
    process_start_time = datetime.now()
    
    # Handle --list-models flag (exit early)
    if list_models_flag:
        try:
            resources = detect_system_resources(no_gpu=no_gpu)
            table = get_model_table(resources, use_gpu=not no_gpu)
            console.print(table)
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not detect system resources: {e}")
            # Fallback: show models without resource info
            console.print("\n[bold]Available Whisper Models:[/bold]")
            for model_name in list_models():
                console.print(f"  • {model_name}")
        raise typer.Exit(0)
    
    # Validate input_file is provided when not using --list-models
    if input_file is None:
        console.print("[red]Error:[/red] INPUT_FILE is required when not using --list-models")
        raise typer.Exit(1)
    
    # Model selection flow
    selected_model = None
    
    # Step 1: Check for explicit model override
    if model is not None:
        selected_model = model
        console.print(f"[dim]Using explicit model: {selected_model}[/dim]")
        logger.debug(f"Model selection: explicit override '{selected_model}'")
    else:
        # Step 2: Detect system resources for auto-selection
        try:
            resources = detect_system_resources()
            use_gpu = not no_gpu
            
            logger.debug(f"System resources detected: RAM={resources.available_ram_gb:.1f}GB, "
                        f"GPU={'available' if resources.has_gpu else 'not available'}")
            
            # Step 3: Determine if interactive menu should be shown
            interactive_available = is_interactive_environment()
            should_show_menu = interactive_available and not auto
            
            logger.debug(f"Interactive mode: available={interactive_available}, "
                        f"auto_mode={auto}, will_show_menu={should_show_menu}")
            
            if should_show_menu:
                # Interactive mode: show menu for user selection
                from mnemofy.model_selector import filter_compatible_models
                
                compatible = filter_compatible_models(resources, use_gpu=use_gpu)
                recommended, reasoning = recommend_model(resources, use_gpu=use_gpu)
                
                logger.debug(f"Compatible models: {[m.name for m in compatible]}, "
                           f"recommended: {recommended.name}")
                
                console.print(f"\n[bold]System Resources:[/bold] {reasoning}")
                console.print("[bold]Select a model:[/bold]")
                
                menu = ModelMenu(compatible, recommended=recommended, resources=resources)
                
                menu_start = time.time()
                selected_spec = menu.show()
                menu_duration = time.time() - menu_start
                
                logger.debug(f"Model menu interaction took {menu_duration*1000:.0f}ms")
                
                if selected_spec is None:
                    console.print("[yellow]Model selection cancelled[/yellow]")
                    raise typer.Exit(1)
                
                selected_model = selected_spec.name
                console.print(f"[dim]Selected model: {selected_model}[/dim]")
            else:
                # Auto-selection mode (--auto or non-TTY)
                recommended, reasoning = recommend_model(resources, use_gpu=use_gpu)
                selected_model = recommended.name
                mode = "auto-selected"
                console.print(f"[dim]{mode.capitalize()}: {recommended.name} ({reasoning})[/dim]")
                logger.debug(f"Auto-selected model: {selected_model} ({reasoning})")
                
        except ModelSelectionError as e:
            # No compatible models found - this is a critical error
            console.print(f"[red]Error:[/red] {e}")
            console.print("[red]No compatible models found for your system.[/red]")
            console.print("\nPossible solutions:")
            console.print("  • Free up more RAM and try again")
            console.print("  • Manually specify a smaller model with --model tiny")
            console.print("  • Use --no-gpu to force CPU-only mode")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Resource detection failed: {e}")
            console.print("[yellow]Falling back to 'base' model[/yellow]")
            selected_model = "base"
    
    try:
        # Initialize OutputManager for path management
        try:
            manager = OutputManager(input_file, outdir=outdir)
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to initialize output directory: {e}")
            raise typer.Exit(1)

        console.print(f"\n[bold blue]mnemofy[/bold blue] - Processing {input_file.name}")
        
        # Check if audio has already been extracted
        audio_output_path = manager.get_audio_path()
        if audio_output_path.exists():
            console.print(f"[yellow]Note:[/yellow] Audio file already exists: {audio_output_path}")
            console.print("[dim]Press 's' to skip extraction, or any other key to re-extract: [/dim]", end="")
            try:
                choice = readchar.readchar()
                if choice.lower() == 's':
                    audio_file = audio_output_path
                    console.print("Skipping extraction")
                    logger.debug(f"User chose to skip audio extraction, using existing file: {audio_file}")
                else:
                    console.print("Re-extracting audio")
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Extracting audio...", total=None)
                        extractor = AudioExtractor()
                        audio_file = extractor.extract_audio(input_file, output_file=audio_output_path)
                        progress.update(task, description="[green]✓ Audio extracted")
                    console.print(f"[dim]Audio file: {audio_file}[/dim]")
            except Exception as e:
                console.print(f"Continuing with re-extraction...")
                logger.debug(f"Interactive prompt failed: {e}, defaulting to re-extraction")
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Extracting audio...", total=None)
                    extractor = AudioExtractor()
                    audio_file = extractor.extract_audio(input_file, output_file=audio_output_path)
                    progress.update(task, description="[green]✓ Audio extracted")
                console.print(f"[dim]Audio file: {audio_file}[/dim]")
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Extracting audio...", total=None)

                # Use OutputManager to determine audio output path
                extractor = AudioExtractor()
                audio_file = extractor.extract_audio(input_file, output_file=audio_output_path)

                progress.update(task, description="[green]✓ Audio extracted")

            console.print(f"[dim]Audio file: {audio_file}[/dim]")

        # Initialize LLM engine once if any LLM-backed feature is requested
        llm_engine_instance = None
        llm_needed = repair or classify == "llm" or notes == "llm"
        if llm_needed:
            logger.debug(f"LLM mode requested: classify={classify}, notes={notes}, repair={repair}")
            try:
                # Load configuration from file + env + CLI overrides
                cli_overrides = {}
                if llm_engine != "openai":  # Only override if not default
                    cli_overrides["engine"] = llm_engine
                if llm_model:
                    cli_overrides["model"] = llm_model
                if llm_base_url:
                    cli_overrides["base_url"] = llm_base_url

                logger.debug(f"Loading LLM config with CLI overrides: {cli_overrides}")

                llm_config = get_llm_config(cli_overrides=cli_overrides)

                logger.debug(f"Final LLM config: engine={llm_config.engine}, "
                           f"model={llm_config.model}, timeout={llm_config.timeout}s")

                # Create LLM engine using merged config
                llm_start = time.time()
                llm_engine_instance = get_llm_engine(
                    engine_type=llm_config.engine,
                    model=llm_config.model,
                    base_url=llm_config.base_url,
                    api_key=llm_config.api_key,
                    timeout=llm_config.timeout
                )
                llm_init_duration = time.time() - llm_start

                if llm_engine_instance:
                    console.print(f"[dim]LLM engine: {llm_engine_instance.get_model_name()}[/dim]")
                    logger.debug(f"LLM engine initialized in {llm_init_duration*1000:.0f}ms: "
                               f"{llm_engine_instance.get_model_name()}")
                else:
                    console.print("[yellow]Warning:[/yellow] LLM engine unavailable, falling back to heuristic mode")
                    logger.debug("LLM engine returned None, falling back to heuristic mode")
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] LLM initialization failed: {e}")
                console.print("[dim]Falling back to heuristic mode[/dim]")
                logger.debug(f"LLM initialization error: {e}")

        # Step 3: Generate formatted transcripts
        # First, check if transcripts already exist
        transcript_paths = manager.get_model_aware_transcript_paths(selected_model) if model_suffix else manager.get_transcript_paths()
        transcript_json_path = transcript_paths["json"]
        transcription: Optional[dict] = None
        segments: List[dict] = []
        skip_transcription = False
        
        if transcript_json_path.exists():
            console.print(f"[yellow]Note:[/yellow] Transcripts already exist")
            console.print("[dim]Press 's' to skip transcription, or any other key to re-transcribe: [/dim]", end="")
            try:
                choice = readchar.readchar()
                if choice.lower() == 's':
                    console.print("Skipping transcription")
                    logger.debug("User chose to skip transcription, loading existing transcripts")
                    skip_transcription = True
                    
                    # Load existing transcription from JSON
                    import json
                    with open(transcript_json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    # Reconstruct transcription and segments from JSON
                    if isinstance(json_data, dict) and 'segments' in json_data:
                        segments = json_data['segments'] if isinstance(json_data['segments'], list) else []
                        transcription = {"segments": segments}
                        if 'language' in json_data:
                            transcription['language'] = json_data['language']
                    elif isinstance(json_data, list):
                        segments = json_data
                        transcription = {"segments": segments}
                    
                    logger.debug(f"Loaded {len(segments)} segments from existing transcript")
                else:
                    console.print("Re-transcribing audio")
                    logger.debug("User chose to re-transcribe")
            except Exception as e:
                console.print(f"Continuing with re-transcription...")
                logger.debug(f"Interactive prompt failed: {e}, defaulting to re-transcription")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating formatted transcripts...", total=None)

            transcript_start = time.time()
            transcriber = None
            
            if not skip_transcription:
                transcriber = Transcriber(model_name=selected_model)
                transcription = transcriber.transcribe(audio_file, language=lang)
                segments = transcriber.get_segments(transcription)
            else:
                # Mark task as already done since we loaded existing transcript
                task = progress.add_task("[green]✓ Transcripts loaded[/green]", total=None)
            
            # Step 3.5: Normalize or repair transcript (if enabled and not skipped)
            transcript_changes = []
            
            if not skip_transcription and (normalize or repair) and transcription is not None:
                logger.debug(f"Transcript preprocessing enabled: normalize={normalize}, repair={repair}")
                
                # Ensure transcriber is initialized (it should be from the transcription step above)
                if transcriber is None:
                    transcriber = Transcriber(model_name=selected_model)
                
                # Validate repair requirements
                if repair and not llm_engine_instance:
                    console.print("[yellow]Warning:[/yellow] --repair requires LLM engine, skipping repair")
                    repair = False
                
                # Apply normalization
                if normalize:
                    progress.update(task, description="Normalizing transcript...")
                    from mnemofy.transcriber import NormalizationResult
                    
                    norm_start = time.time()
                    norm_result = transcriber.normalize_transcript(
                        transcription,
                        remove_fillers=remove_fillers,
                        normalize_numbers=True,
                    )
                    norm_duration = time.time() - norm_start
                    
                    transcription = norm_result.transcription
                    transcript_changes.extend(norm_result.changes)
                    segments = transcriber.get_segments(transcription)
                    
                    console.print(f"[dim]Applied {len(norm_result.changes)} normalization changes[/dim]")
                    logger.debug(f"Normalization: {len(norm_result.changes)} changes in {norm_duration*1000:.0f}ms")
                
                # Apply LLM-based repair
                if repair and llm_engine_instance:
                    progress.update(task, description="Repairing transcript with LLM...")
                    try:
                        import asyncio
                        
                        repair_start = time.time()
                        repair_result = asyncio.run(
                            transcriber.repair_transcript(transcription, llm_engine_instance)
                        )
                        repair_duration = time.time() - repair_start
                        
                        transcription = repair_result.transcription
                        transcript_changes.extend(repair_result.changes)
                        segments = transcriber.get_segments(transcription)
                        
                        console.print(f"[dim]Applied {len(repair_result.changes)} LLM repairs[/dim]")
                        logger.debug(f"LLM repair: {len(repair_result.changes)} changes in {repair_duration*1000:.0f}ms")
                    except Exception as e:
                        console.print(f"[yellow]Warning:[/yellow] Transcript repair failed: {e}")
                        console.print("[dim]Continuing with normalized transcript[/dim]")
                        logger.debug(f"Repair failed: {e}")
            elif skip_transcription and (normalize or repair):
                console.print("[dim]Skipping transcript preprocessing (using existing transcript)[/dim]")
                logger.debug("Skipping transcript preprocessing because existing transcript was used")
            
            # Determine effective language: prefer explicit --lang, then detected, then fallback
            detected_language = transcription.get("language") if transcription else None
            effective_language = lang or detected_language or "en"
            
            # Prepare metadata (enriched with model details)
            model_spec = MODEL_SPECS.get(selected_model)
            metadata = {
                "engine": "faster-whisper",
                "model": selected_model,
                "language": effective_language,
                "duration": sum(s["end"] - s["start"] for s in segments),
            }
            
            # Add optional model specification details if available
            if model_spec:
                metadata["model_size_gb"] = model_spec.min_ram_gb
                metadata["quality_rating"] = model_spec.quality_rating
                metadata["speed_rating"] = model_spec.speed_rating
            
            # Add processing flags
            if normalize or repair:
                metadata["preprocessing"] = {
                    "normalized": normalize,
                    "repaired": repair,
                    "remove_fillers": remove_fillers if normalize else False,
                }
            
            # Generate all formats
            txt_output = TranscriptFormatter.to_txt(segments)
            srt_output = TranscriptFormatter.to_srt(segments)
            json_output = TranscriptFormatter.to_json(segments, metadata)
            
            # Get paths for writing (already determined at the beginning)
            txt_path = transcript_paths["txt"]
            srt_path = transcript_paths["srt"]
            json_path = transcript_paths["json"]
            
            txt_path.write_text(txt_output, encoding="utf-8")
            srt_path.write_text(srt_output, encoding="utf-8")
            json_path.write_text(json_output, encoding="utf-8")
            
            # Write changes log if normalization or repair was performed
            if transcript_changes:
                changes_log_path = manager.get_changes_log_path()
                changes_output = _format_changes_log(transcript_changes)
                changes_log_path.write_text(changes_output, encoding="utf-8")
                console.print(f"[dim]Changes log: {changes_log_path}[/dim]")

            transcript_duration = time.time() - transcript_start
            
            # Format duration nicely
            if transcript_duration < 60:
                duration_str = f"{transcript_duration:.1f}s"
            else:
                minutes = int(transcript_duration // 60)
                seconds = transcript_duration % 60
                duration_str = f"{minutes}m {seconds:.0f}s"
            
            progress.update(task, description=f"[green]✓ Transcripts generated ({duration_str})")

        # Step 4: Detect meeting type (if enabled)
        classification_result = None
        detected_type = None
        
        if classify != "off" and meeting_type == "auto":
            logger.debug(f"Meeting type detection: mode={classify}, auto-detect=True")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Detecting meeting type...", total=None)
                
                if classify == "llm" and llm_engine_instance:
                    # Use LLM classifier
                    try:
                        transcript_text = " ".join(s["text"] for s in segments)
                        
                        logger.debug(f"Transcript length for detection: {len(transcript_text)} chars")
                        
                        # Extract high-signal segments (use config values if available)
                        llm_config_for_extract = get_llm_config()
                        high_signal = extract_high_signal_segments(
                            transcript_text,
                            context_words=llm_config_for_extract.context_words,
                            max_segments=llm_config_for_extract.max_segments
                        )
                        
                        logger.debug(f"Extracted {len(high_signal)} high-signal segments, "
                                   f"total {sum(len(s) for s in high_signal)} chars")
                        
                        detect_start = time.time()
                        classification_result = llm_engine_instance.classify_meeting_type(
                            transcript_text,
                            high_signal_segments=high_signal
                        )
                        detect_duration = time.time() - detect_start
                        detected_type = classification_result.detected_type
                        
                        # Display detection result
                        confidence_pct = classification_result.confidence * 100
                        console.print(f"\n[bold]Detected Meeting Type:[/bold] {detected_type.value}")
                        console.print(f"[dim]Confidence: {confidence_pct:.1f}% (LLM)[/dim]")
                        if classification_result.evidence:
                            console.print(f"[dim]Evidence: {', '.join(classification_result.evidence[:3])}[/dim]")
                        
                        logger.debug(f"LLM detection: type={detected_type.value}, "
                                   f"confidence={confidence_pct:.1f}%, duration={detect_duration*1000:.0f}ms")
                        
                        progress.update(task, description="[green]✓ Meeting type detected (LLM)")
                    except LLMError as e:
                        console.print(f"[yellow]Warning:[/yellow] LLM classification failed: {e}")
                        console.print("[dim]Falling back to heuristic mode[/dim]")
                        logger.debug(f"LLM classification error: {e}, falling back to heuristic")
                        # Fallback to heuristic
                        transcript_text = " ".join(s["text"] for s in segments)
                        classifier = HeuristicClassifier()
                        
                        detect_start = time.time()
                        classification_result = classifier.detect_meeting_type(transcript_text, segments)
                        detect_duration = time.time() - detect_start
                        detected_type = classification_result.detected_type
                        
                        logger.debug(f"Heuristic fallback: type={detected_type.value}, "
                                   f"duration={detect_duration*1000:.0f}ms")
                        
                        progress.update(task, description="[green]✓ Meeting type detected (heuristic fallback)")
                else:
                    # Use heuristic classifier
                    transcript_text = " ".join(s["text"] for s in segments)
                    classifier = HeuristicClassifier()
                    
                    logger.debug(f"Using heuristic classifier on {len(transcript_text)} chars")
                    
                    detect_start = time.time()
                    classification_result = classifier.detect_meeting_type(transcript_text, segments)
                    detect_duration = time.time() - detect_start
                    detected_type = classification_result.detected_type
                    
                    # Display detection result
                    confidence_pct = classification_result.confidence * 100
                    console.print(f"\n[bold]Detected Meeting Type:[/bold] {detected_type.value}")
                    console.print(f"[dim]Confidence: {confidence_pct:.1f}% (Heuristic)[/dim]")
                    if classification_result.evidence:
                        console.print(f"[dim]Evidence: {', '.join(classification_result.evidence[:3])}[/dim]")
                    
                    logger.debug(f"Heuristic detection: type={detected_type.value}, "
                               f"confidence={confidence_pct:.1f}%, duration={detect_duration*1000:.0f}ms")
                    
                    progress.update(task, description="[green]✓ Meeting type detected")
        elif meeting_type and meeting_type != "auto":
            # Use explicit meeting type
            try:
                detected_type = MeetingType(meeting_type.lower())
                console.print(f"\n[dim]Using explicit meeting type: {detected_type.value}[/dim]")
            except ValueError:
                console.print(f"[red]Error:[/red] Invalid meeting type '{meeting_type}'")
                console.print(f"Valid types: {', '.join(mt.value for mt in MeetingType)}")
                raise typer.Exit(1)
        
        # Step 4.5: Interactive meeting type selection (if enabled and available)
        if detected_type and classification_result and not no_interactive:
            # Show interactive menu for user to confirm or override
            interactive_available = is_interactive_environment()
            
            logger.debug(f"Interactive meeting type selection: available={interactive_available}, "
                       f"detected={detected_type.value}, no_interactive={no_interactive}")
            
            if interactive_available:
                try:
                    # Let user confirm or override via menu
                    menu_start = time.time()
                    selected_type = select_meeting_type(
                        classification_result,
                        auto_accept_threshold=0.6,
                        interactive=True
                    )
                    menu_duration = time.time() - menu_start
                    
                    logger.debug(f"Meeting type menu interaction took {menu_duration*1000:.0f}ms")
                    
                    if selected_type != detected_type:
                        console.print(f"\n[cyan]User selected:[/cyan] {selected_type.value}")
                        logger.debug(f"User overrode detected type: {detected_type.value} -> {selected_type.value}")
                        detected_type = selected_type
                    else:
                        logger.debug(f"User accepted detected type: {detected_type.value}")
                except Exception as e:
                    console.print(f"[yellow]Warning:[/yellow] Interactive menu failed: {e}")
                    console.print(f"[dim]Continuing with detected type: {detected_type.value}[/dim]")
                    logger.debug(f"Interactive menu error: {e}")
        
        # Step 5: Generate notes
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating notes...", total=None)

            # Use meeting-type-aware notes generation if type detected
            if detected_type and not template:
                logger.debug(f"Generating meeting-type-aware notes: type={detected_type.value}, "
                           f"mode={notes}, template={template}")
                
                # Extract structured information (basic or LLM)
                if notes == "llm" and llm_engine_instance:
                    try:
                        # Use LLM notes extraction
                        notes_start = time.time()
                        extracted_items = llm_engine_instance.generate_notes(
                            transcript_segments=segments,
                            meeting_type=detected_type.value,
                            focus_areas=None
                        )
                        notes_duration = time.time() - notes_start
                        
                        console.print("[dim]Notes extracted using LLM[/dim]")
                        logger.debug(f"LLM notes extraction: {len(extracted_items)} items in {notes_duration*1000:.0f}ms")
                    except LLMError as e:
                        console.print(f"[yellow]Warning:[/yellow] LLM notes extraction failed: {e}")
                        console.print("[dim]Falling back to basic extraction[/dim]")
                        logger.debug(f"LLM notes extraction failed: {e}, falling back to basic")
                        # Fallback to basic extraction
                        extractor = BasicNotesExtractor()
                        
                        notes_start = time.time()
                        extracted_items = extractor.extract_all(segments, detected_type)
                        notes_duration = time.time() - notes_start
                        
                        logger.debug(f"Basic extraction: {len(extracted_items)} items in {notes_duration*1000:.0f}ms")
                else:
                    # Use basic heuristic extraction
                    extractor = BasicNotesExtractor()
                    
                    notes_start = time.time()
                    extracted_items = extractor.extract_all(segments, detected_type)
                    notes_duration = time.time() - notes_start
                    
                    logger.debug(f"Basic extraction: {len(extracted_items)} items in {notes_duration*1000:.0f}ms")
                
                # Prepare metadata for template
                template_metadata = {
                    "title": title,
                    "date": metadata.get("date", ""),
                    "duration": f"{int(metadata['duration'] // 60)}m {int(metadata['duration'] % 60)}s",
                    "confidence": f"{classification_result.confidence:.2f}" if classification_result else "N/A",
                    "engine": classification_result.engine if classification_result else "manual",
                }
                
                # Render using appropriate template
                try:
                    notes_markdown = render_meeting_notes(
                        detected_type,
                        extracted_items,
                        template_metadata,
                        custom_template_dir=template.parent if template else None
                    )
                except Exception as e:
                    from jinja2 import TemplateNotFound
                    if isinstance(e, TemplateNotFound) or "Template" in str(e):
                        console.print(f"[red]Error: {e}[/red]")
                        console.print("[yellow]Tip:[/yellow] Check if templates are installed correctly")
                        console.print("[dim]Try reinstalling mnemofy with: pip install -e .[/dim]")
                        logger.debug(f"Template rendering failed: {e}")
                        raise typer.Exit(1)
                    else:
                        raise
            else:
                # Fall back to legacy notes generator
                try:
                    notes_generator = StructuredNotesGenerator(mode="basic")  # Only basic mode supported in legacy
                    notes_markdown = notes_generator.generate(segments, metadata, include_audio=keep_audio)
                except NotImplementedError as e:
                    console.print(f"[red]Error: {e}[/red]")
                    console.print("[yellow]Please specify a meeting type to use LLM notes generation.[/yellow]")
                    raise typer.Exit(1)
            
            # Determine output path for notes
            if output is None:
                output = manager.get_notes_path()
            
            # Write notes output
            output.write_text(notes_markdown, encoding="utf-8")
            
            # Write meeting-type.json if type was detected
            if classification_result:
                import json
                meeting_type_path = manager.outdir / f"{manager.basename}.meeting-type.json"
                meeting_type_data = {
                    "detected_type": classification_result.detected_type.value,
                    "confidence": classification_result.confidence,
                    "evidence": classification_result.evidence,
                    "secondary_types": [
                        {"type": mt.value, "score": score}
                        for mt, score in classification_result.secondary_types
                    ],
                    "engine": classification_result.engine,
                    "timestamp": classification_result.timestamp.isoformat(),
                }
                meeting_type_path.write_text(json.dumps(meeting_type_data, indent=2), encoding="utf-8")

            progress.update(task, description="[green]✓ Notes generated")

        # Step 6: Generate metadata and artifacts manifest
        process_end_time = datetime.now()
        
        # Build ASR engine info
        model_spec = MODEL_SPECS.get(selected_model)
        asr_info = ASREngineInfo(
            engine="faster-whisper",
            model=selected_model,
            model_size_gb=model_spec.min_ram_gb if model_spec else None,
            quality_rating=model_spec.quality_rating if model_spec else None,
            speed_rating=model_spec.speed_rating if model_spec else None,
        )
        
        # Build LLM engine info (if used)
        llm_info = None
        if llm_engine_instance:
            llm_purposes = []
            if classify == "llm":
                llm_purposes.append("meeting_type_detection")
            if notes == "llm":
                llm_purposes.append("notes_generation")
            if repair:
                llm_purposes.append("transcript_repair")
            
            llm_info = LLMEngineInfo(
                engine=llm_engine,
                model=llm_engine_instance.get_model_name(),
                purpose=", ".join(llm_purposes) if llm_purposes else "general",
            )
        
        # Build processing config
        proc_config = ProcessingConfig(
            language=effective_language,
            normalize=normalize,
            repair=repair,
            meeting_type=detected_type.value if detected_type else None,
            classify_mode=classify,
            notes_mode=notes,
        )
        
        # Count words in transcript
        transcript_text = " ".join(s["text"] for s in segments)
        word_count = len(transcript_text.split())
        
        # Create processing metadata
        proc_metadata = create_processing_metadata(
            input_file=input_file.name,
            asr_engine=asr_info,
            config=proc_config,
            start_time=process_start_time,
            end_time=process_end_time,
            llm_engine=llm_info,
            language_detected=detected_language,
            transcript_duration_seconds=metadata["duration"],
            word_count=word_count,
            segment_count=len(segments),
        )
        
        # Save processing metadata
        metadata_path = manager.get_metadata_path()
        if model_suffix:
            # Use model-suffixed metadata filename for comparison
            metadata_path = manager.outdir / f"{manager.basename}.{selected_model}.metadata.json"
            logger.debug(f"Using model-suffixed metadata path: {metadata_path}")
        
        metadata_path.write_text(proc_metadata.to_json(), encoding="utf-8")
        
        # Track run history (append to history file)
        history_path = manager.outdir / f"{manager.basename}.run-history.jsonl"
        run_record = {
            "timestamp": process_end_time.isoformat(),
            "model": selected_model,
            "duration_seconds": proc_metadata.duration_seconds,
            "transcript_duration": metadata["duration"],
            "word_count": word_count,
            "segment_count": len(segments),
            "config": asdict(proc_config),
        }
        
        # Append to history file (JSONL format - one JSON object per line)
        with open(history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(run_record, ensure_ascii=False) + "\n")
        
        logger.debug(f"Appended run record to history: {history_path}")
        
        # Create artifacts manifest
        manifest = create_artifact_manifest(
            input_file=input_file.name,
            model_name=selected_model,
        )
        
        # Add artifacts to manifest
        def get_file_size(path: Path) -> int:
            try:
                return path.stat().st_size if path.exists() else 0
            except Exception:
                return 0
        
        # Transcript artifacts
        manifest.add_artifact(
            "transcript", str(txt_path.relative_to(manager.outdir)),
            "txt", "Plain text transcript with timestamps",
            get_file_size(txt_path), selected_model
        )
        manifest.add_artifact(
            "transcript", str(srt_path.relative_to(manager.outdir)),
            "srt", "SubRip subtitle format transcript",
            get_file_size(srt_path), selected_model
        )
        manifest.add_artifact(
            "transcript", str(json_path.relative_to(manager.outdir)),
            "json", "Structured JSON transcript with metadata",
            get_file_size(json_path), selected_model, "1.0"
        )
        
        # Notes artifact
        manifest.add_artifact(
            "notes", str(output.relative_to(manager.outdir)),
            "md", "Structured meeting notes",
            get_file_size(output), 
            llm_engine_instance.get_model_name() if (notes == "llm" and llm_engine_instance) else "basic_extractor"
        )
        
        # Classification result (if generated)
        if classification_result:
            meeting_type_path = manager.outdir / f"{manager.basename}.meeting-type.json"
            manifest.add_artifact(
                "classification", str(meeting_type_path.relative_to(manager.outdir)),
                "json", "Meeting type classification result",
                get_file_size(meeting_type_path),
                llm_engine_instance.get_model_name() if (classify == "llm" and llm_engine_instance) else "heuristic_classifier"
            )
        
        # Changes log (if generated)
        if transcript_changes:
            changes_log_path = manager.get_changes_log_path()
            changes_model = (
                llm_engine_instance.get_model_name() if (repair and llm_engine_instance) else "normalizer"
            )
            manifest.add_artifact(
                "log", str(changes_log_path.relative_to(manager.outdir)),
                "md", "Transcript normalization/repair changes log",
                get_file_size(changes_log_path),
                changes_model
            )
        
        # Metadata artifact
        manifest.add_artifact(
            "metadata", str(metadata_path.relative_to(manager.outdir)),
            "json", "Processing metadata and configuration",
            get_file_size(metadata_path), None, "1.0"
        )
        
        # Audio artifact (if kept)
        if keep_audio:
            audio_path = manager.get_audio_path()
            manifest.add_artifact(
                "audio", str(audio_path.relative_to(manager.outdir)),
                "wav", "Extracted audio (16kHz mono WAV)",
                get_file_size(audio_path)
            )
        
        # Save artifacts manifest
        manifest_path = manager.get_artifacts_manifest_path()
        if model_suffix:
            # Use model-suffixed manifest filename
            manifest_path = manager.outdir / f"{manager.basename}.{selected_model}.artifacts.json"
            logger.debug(f"Using model-suffixed manifest path: {manifest_path}")
        
        manifest_path.write_text(manifest.to_json(), encoding="utf-8")
        
        # Clean up temporary audio file if needed
        if not keep_audio and audio_file != input_file:
            try:
                audio_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors

        console.print("\n[bold green]✓ Success![/bold green]")
        
        if model_suffix:
            console.print(f"[cyan]ℹ Model-suffixed filenames enabled ({selected_model})[/cyan]")
        
        console.print(f"[dim]Output files generated:[/dim]")
        console.print(f"  Transcript (TXT): {txt_path}")
        console.print(f"  Subtitle (SRT): {srt_path}")
        console.print(f"  Structured (JSON): {json_path}")
        if classification_result:
            meeting_type_path = manager.outdir / f"{manager.basename}.meeting-type.json"
            console.print(f"  Meeting Type: {meeting_type_path}")
        console.print(f"  Notes: {output}")
        console.print(f"[dim]Metadata:[/dim]")
        console.print(f"  Processing Info: {metadata_path}")
        console.print(f"  Artifacts Index: {manifest_path}")
        console.print(f"  Run History: {history_path}")

        # Show stats
        console.print("\n[bold]Statistics:[/bold]")
        console.print(f"  Segments: {len(segments)}")
        total_duration = sum(s["end"] - s["start"] for s in segments)
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        console.print(f"  Duration: {minutes}m {seconds}s")

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    from mnemofy import __version__

    console.print(f"mnemofy version {__version__}")


@app.command()
def analyze_metadata(
    metadata_file: Optional[Path] = typer.Argument(
        None,
        help="Path to metadata JSON file (*.metadata.json). If not provided, will also analyze artifacts manifest if found.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    artifacts_file: Optional[Path] = typer.Option(
        None,
        "--artifacts",
        "-a",
        help="Path to artifacts manifest JSON file (*.artifacts.json)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    transcripts: Optional[list[Path]] = typer.Option(
        None,
        "--transcripts",
        "-t",
        help="Path to transcript JSON files to compare (can specify multiple times)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    cost: bool = typer.Option(
        False,
        "--cost",
        "-c",
        help="Include LLM cost estimation",
    ),
) -> None:
    """Analyze processing metadata and artifacts.

    This command analyzes the metadata and artifacts generated during transcription,
    providing insights into model usage, processing time, and output statistics.

    Examples:
        # Analyze metadata file
        mnemofy analyze-metadata meeting.metadata.json

        # Analyze with artifacts manifest
        mnemofy analyze-metadata meeting.metadata.json -a meeting.artifacts.json

        # Compare multiple transcript JSONs
        mnemofy analyze-metadata -t meeting.tiny.transcript.json -t meeting.base.transcript.json

        # Include LLM cost estimation
        mnemofy analyze-metadata meeting.metadata.json --cost
    """
    from mnemofy.analysis import (
        analyze_processing_metadata,
        analyze_artifacts_manifest,
        compare_transcript_metadata,
        calculate_processing_cost,
    )

    if not metadata_file and not artifacts_file and not transcripts:
        console.print("[red]Error: Must provide at least one of: metadata file, artifacts file, or transcript files[/red]")
        raise typer.Exit(1)

    # Analyze metadata
    if metadata_file:
        if not metadata_file.exists():
            console.print(f"[red]Error: Metadata file not found: {metadata_file}[/red]")
            raise typer.Exit(1)
        analyze_processing_metadata(metadata_file)

        # Calculate cost if requested
        if cost:
            calculate_processing_cost(metadata_file)

        # Auto-discover artifacts file if not specified
        if not artifacts_file:
            auto_artifacts = metadata_file.with_suffix(".artifacts.json")
            if auto_artifacts.exists():
                artifacts_file = auto_artifacts

    # Analyze artifacts
    if artifacts_file:
        if not artifacts_file.exists():
            console.print(f"[red]Error: Artifacts file not found: {artifacts_file}[/red]")
            raise typer.Exit(1)
        analyze_artifacts_manifest(artifacts_file)

    # Compare transcripts
    if transcripts:
        valid_transcripts = [t for t in transcripts if t.exists()]
        if len(valid_transcripts) < 2:
            console.print("[yellow]Warning: Need at least 2 transcript files for comparison[/yellow]")
        else:
            compare_transcript_metadata(valid_transcripts)


@app.command()
def compare_runs(
    history_file: Path = typer.Argument(
        ...,
        help="Path to run history file (*.run-history.jsonl)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    show_analysis: bool = typer.Option(
        True,
        "--analysis/--no-analysis",
        help="Show detailed performance analysis",
    ),
    show_recommendations: bool = typer.Option(
        True,
        "--recommendations/--no-recommendations",
        help="Show model recommendations",
    ),
) -> None:
    """Compare transcription runs with different models.

    This command analyzes the run history file to compare performance and quality
    across different model runs, helping you choose the best model for your needs.

    The run history file (*.run-history.jsonl) is automatically created by the
    transcribe command each time you process a file.

    Examples:
        # Compare all runs
        mnemofy compare-runs meeting.run-history.jsonl

        # Show only comparison table, skip analysis
        mnemofy compare-runs meeting.run-history.jsonl --no-analysis

        # Skip recommendations
        mnemofy compare-runs meeting.run-history.jsonl --no-recommendations
    """
    from mnemofy.analysis import (
        load_run_history,
        display_run_comparison,
        analyze_model_performance,
        show_recommendations,
    )

    if not history_file.exists():
        console.print(f"[red]Error: Run history file not found: {history_file}[/red]")
        raise typer.Exit(1)

    # Load run history
    runs = load_run_history(history_file)

    if not runs:
        console.print("[yellow]No valid run records found.[/yellow]")
        raise typer.Exit(0)

    # Display comparison table
    display_run_comparison(runs)

    # Show analysis
    if show_analysis:
        analyze_model_performance(runs)

    # Show recommendations
    if show_recommendations:
        show_recommendations(runs)

    console.print(f"\n[dim]Total runs analyzed: {len(runs)}[/dim]")
    console.print(f"[dim]History file: {history_file}[/dim]\n")


def _format_changes_log(changes: list) -> str:
    """Format transcript changes into markdown log.
    
    Args:
        changes: List of TranscriptChange objects
    
    Returns:
        Markdown-formatted changes log
    """
    from mnemofy.transcriber import TranscriptChange
    
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
            output_lines.append(f"```")
            output_lines.append(change.before)
            output_lines.append(f"```")
            output_lines.append("")
            output_lines.append("**After**:")
            output_lines.append(f"```")
            output_lines.append(change.after)
            output_lines.append(f"```")
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
            output_lines.append(f"```")
            output_lines.append(change.before)
            output_lines.append(f"```")
            output_lines.append("")
            output_lines.append("**After**:")
            output_lines.append(f"```")
            output_lines.append(change.after)
            output_lines.append(f"```")
            output_lines.append("")
    
    return "\n".join(output_lines)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
